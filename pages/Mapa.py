# ====================================================================
# --- BLOQUE 1: IMPORTACIONES ---
# ====================================================================
import streamlit as st
import pandas as pd
from typing import List
from math import radians, sin, cos, sqrt, atan2

# ✅ CAMBIO: reemplazamos streamlit_geolocation por streamlit_js_eval
from streamlit_js_eval import streamlit_js_eval

import folium
from streamlit_folium import st_folium

# Firebase (para la base de datos)
import firebase_admin
from firebase_admin import credentials, firestore

# ====================================================================
# --- BLOQUE 2: CONEXIÓN A FIREBASE (con st.secrets) ---
# ====================================================================

@st.cache_resource
def init_firebase():
    """Inicializa la conexión con Firebase usando las credenciales guardadas en st.secrets."""
    try:
        if not firebase_admin._apps:
            secret_creds = st.secrets["firebase_credentials"]
            creds_dict = dict(secret_creds)
            if 'private_key' in creds_dict:
                creds_dict['private_key'] = creds_dict['private_key'].replace('\\n', '\n')
            if not creds_dict:
                st.error("Error: No se encontraron las 'firebase_credentials' en st.secrets.")
                return None
            print("Cargando credenciales desde st.secrets...")
            cred = credentials.Certificate(creds_dict)
            firebase_admin.initialize_app(cred)
            print("--- Conexión a Firebase exitosa ---")
        return firestore.client()
    except KeyError:
        st.error("Error: faltan las 'firebase_credentials' en tu archivo .streamlit/secrets.toml")
        return None
    except Exception as e:
        st.error(f"Error al inicializar Firebase: {e}")
        return None


@st.cache_resource
def load_and_create_centros(_db) -> List['CentroReciclaje']:
    """Lee la colección 'centros_reciclaje' de Firebase y la convierte en objetos CentroReciclaje."""
    if _db is None:
        st.error("No se pudo conectar a Firebase.")
        return []

    print("--- LEYENDO DATOS DESDE FIREBASE ---")
    centros_ref = _db.collection('centros_reciclaje')
    docs = centros_ref.stream()
    lista_centros = []
    try:
        for doc in docs:
            data = doc.to_dict()
            lista_centros.append(CentroReciclaje(**data))
        if not lista_centros:
            st.warning("Se conectó a Firebase, pero la colección 'centros_reciclaje' está vacía.")
            return []
        print(f"--- Se cargaron {len(lista_centros)} centros ---")
        return lista_centros
    except Exception as e:
        st.error(f"Error al leer datos de Firebase: {e}")
        st.exception(e)
        return []


# ====================================================================
# --- BLOQUE 3: PARADIGMA POO (Modelos de Datos) ---
# ====================================================================

class CentroReciclaje:
    """Clase que representa un único centro de reciclaje."""
    def __init__(self, nombre=None, lat=None, lon=None, horario=None, materiales=None, ubicacion=None, **kwargs):
        self.nombre = nombre if nombre else "Nombre no disponible"
        self.lat = float(lat) if lat is not None else 0.0
        self.lon = float(lon) if lon is not None else 0.0
        self.horario = horario if horario else "No disponible"
        self.ubicacion = ubicacion if ubicacion else self.nombre
        self.distance = None

        if isinstance(materiales, str):
            temp_list = materiales.lower().split(',')
            self.materiales = [m.strip() for m in temp_list if m.strip()]
        elif isinstance(materiales, list):
            self.materiales = [str(m).lower().strip() for m in materiales]
        else:
            self.materiales = []


# ====================================================================
# --- BLOQUE 4: PARADIGMA LÓGICO (Motor de Reglas) ---
# ====================================================================

class Regla:
    """Clase que modela una regla 'SI-ENTONCES'."""
    def __init__(self, condicions_str: str, conclusiones: str):
        self.conclusiones = conclusiones
        self.condiciones_list = []
        for cond in condicions_str.split(';'):
            if ':' in cond:
                key, val = cond.split(':', 1)
                self.condiciones_list.append((key.strip().lower(), val.strip().lower()))

    def checar_condiciones(self, centro: CentroReciclaje) -> bool:
        for key, value in self.condiciones_list:
            if key == 'material' and value not in centro.materiales:
                return False
            elif key == 'horario' and value not in centro.horario.lower():
                return False
            elif key == 'ubicacion' and value != centro.ubicacion.lower():
                return False
        return True


@st.cache_resource
def load_rules(_db) -> List[Regla]:
    """Lee la colección 'reglas' de Firebase y la convierte en objetos Regla."""
    if _db is None:
        return []
    print("--- LEYENDO REGLAS DESDE FIREBASE ---")
    reglas_ref = _db.collection('reglas')
    docs = reglas_ref.stream()
    lista_reglas = []
    try:
        for doc in docs:
            data = doc.to_dict()
            if 'conclusion' in data:
                condiciones = [str(v) for k, v in data.items() if k.startswith('condicion')]
                if condiciones:
                    lista_reglas.append(Regla(";".join(condiciones), data['conclusion']))
        print(f"--- Se cargaron {len(lista_reglas)} reglas ---")
        return lista_reglas
    except Exception as e:
        st.error(f"Error al leer reglas: {e}")
        return []


# ====================================================================
# --- BLOQUE 5: PARADIGMA POO (Lógica de Negocio) ---
# ====================================================================

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1_rad, lon1_rad = radians(lat1), radians(lon1)
    lat2_rad, lon2_rad = radians(lat2), radians(lon2)
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


class Recomendador:
    def __init__(self, db_client):
        self._centros = load_and_create_centros(db_client)
        self._reglas = load_rules(db_client)

    def get_all_centros(self):
        return self._centros

    def get_all_materials(self):
        all_mats = set()
        for c in self._centros:
            for m in c.materiales:
                all_mats.add(m.capitalize())
        return sorted(all_mats)

    def filter_by_materials(self, selected_materials):
        if not selected_materials:
            return self._centros
        selected_mats_lower = [m.lower() for m in selected_materials]
        return list(filter(lambda c: all(m in c.materiales for m in selected_mats_lower), self._centros))

    def sort_by_distance(self, user_lat, user_lon, centros):
        for c in centros:
            c.distance = haversine(user_lat, user_lon, c.lat, c.lon)
        return sorted(centros, key=lambda c: c.distance)

    def aplicar_motor_logico(self, centros_filtrados):
        resultados_logicos = {}
        for c in centros_filtrados:
            conclusiones_encontradas = []
            for regla in self._reglas:
                if regla.checar_condiciones(c):
                    conclusiones_encontradas.append(regla.conclusiones)
            if conclusiones_encontradas:
                resultados_logicos[c.nombre] = conclusiones_encontradas
        return resultados_logicos


# ====================================================================
# --- BLOQUE 6: INTERFAZ DE STREAMLIT ---
# ====================================================================

st.set_page_config(layout="wide")
st.title("♻️ Buscador Inteligente de Centros de Reciclaje")
st.info("Motor Lógico con Reglas desde Firebase | Conexión segura con st.secrets")

try:
    db_client = init_firebase()
    if db_client:
        recomendador = Recomendador(db_client)
    else:
        st.error("No se pudo inicializar Firebase.")
        st.stop()

    st.sidebar.header("👇 Filtra tu Búsqueda")
    all_materials = recomendador.get_all_materials()

    if not all_materials:
        st.error("No se pudieron cargar los materiales desde Firebase.")
    else:
        selected_materials = st.sidebar.multiselect(
            "1. Selecciona los materiales:",
            options=all_materials,
            placeholder="Elige uno o más materiales"
        )

        filtered_centros = recomendador.filter_by_materials(selected_materials)

        st.sidebar.markdown("---")
        st.sidebar.subheader("📍 Encuentra el más cercano")

        # ✅ CAMBIO: usamos streamlit_js_eval para obtener coordenadas
        coords = streamlit_js_eval(js_expressions="navigator.geolocation.getCurrentPosition(p=>window.parent.postMessage(p.coords))")
        user_lat, user_lon = None, None

        if coords and "latitude" in coords and "longitude" in coords:
            user_lat = coords["latitude"]
            user_lon = coords["longitude"]
            st.sidebar.success(f"Ubicación obtenida: Lat: {user_lat:.4f}, Lon: {user_lon:.4f}")
            filtered_centros = recomendador.sort_by_distance(user_lat, user_lon, filtered_centros)
            nearest_center = filtered_centros[0] if filtered_centros else None
        else:
            nearest_center = None
            st.sidebar.warning("No se pudo obtener la ubicación del usuario.")

        col1, col2 = st.columns(2)
        col1.metric("Centros Encontrados", len(filtered_centros))
        if nearest_center:
            col2.metric("Centro más cercano", nearest_center.nombre, delta=f"- {nearest_center.distance:.2f} km", delta_color="off")

        st.markdown("---")
        if filtered_centros:
            col_map, col_data = st.columns([0.6, 0.4])
            with col_map:
                st.subheader("Ubicación en el Mapa")
                map_center = [user_lat, user_lon] if user_lat else [19.4326, -99.1332]
                zoom_level = 13 if user_lat else 10
                m = folium.Map(location=map_center, zoom_start=zoom_level)
                for centro in filtered_centros:
                    folium.Marker(
                        location=[centro.lat, centro.lon],
                        popup=f"<b>{centro.nombre}</b><br>Horario: {centro.horario}",
                        tooltip="Clic para ver detalles"
                    ).add_to(m)
                if user_lat:
                    folium.Marker(
                        location=[user_lat, user_lon],
                        popup="<b>Tu Ubicación</b>",
                        icon=folium.Icon(color='red', icon='user', prefix='fa')
                    ).add_to(m)
                if nearest_center:
                    points = [(user_lat, user_lon), (nearest_center.lat, nearest_center.lon)]
                    folium.PolyLine(points, color='red', weight=2, dash_array='5,10').add_to(m)
                st_folium(m, width='stretch')

            with col_data:
                st.subheader("Detalles de los Centros (ordenados por distancia)")
                df_data = []
                for c in filtered_centros:
                    d = vars(c).copy()
                    if d['distance'] is not None:
                        d['distance'] = f"{d['distance']:.2f} km"
                    d['materiales'] = ", ".join(m.capitalize() for m in c.materiales)
                    df_data.append(d)
                df_display = pd.DataFrame(df_data)
                st.dataframe(df_display, width='stretch',
                             column_order=("nombre", "distance", "ubicacion", "horario", "materiales"))
        else:
            st.warning("No se encontraron centros con esos filtros.")

        st.markdown("---")
        with st.expander("Ver Recomendaciones del Motor Lógico (de Firebase)"):
            if filtered_centros:
                resultados_logicos = recomendador.aplicar_motor_logico(filtered_centros)
                if resultados_logicos:
                    st.subheader("💡 Recomendaciones Especiales Encontradas:")
                    for nombre, conclusiones in resultados_logicos.items():
                        st.markdown(f"#### {nombre}")
                        for conclusion in conclusiones:
                            st.success(f"**Regla disparada:** {conclusion}")
                        st.markdown("---")
                else:
                    st.success("✅ Ninguno de los centros filtrados disparó una regla lógica.")
            else:
                st.warning("No hay centros para aplicar el motor lógico.")

except Exception as e:
    st.error(f"Ocurrió un error inesperado: {e}")
    st.exception(e)
