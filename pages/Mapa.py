import streamlit as st
import pandas as pd
from typing import List, Optional, Dict, Any
from math import radians, sin, cos, sqrt, atan2
import folium
from streamlit_folium import st_folium

# Import guard para streamlit_js_eval: si no está, no abortamos; usamos fallback.
try:
    from streamlit_js_eval import streamlit_js_eval
    HAS_JS_EVAL = True
except Exception:
    streamlit_js_eval = None
    HAS_JS_EVAL = False

# Firebase
import firebase_admin
from firebase_admin import credentials, firestore

# -------------------------
# Configuración de la página
# -------------------------
st.set_page_config(page_title="♻️ Buscador de Centros de Reciclaje", layout="wide")
st.title("♻️ Buscador Inteligente de Centros de Reciclaje")
st.caption("Ubica centros, filtra por materiales y obtén recomendaciones basadas en reglas (Firestore).")

# -------------------------
# Utilidades: Haversine
# -------------------------
def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Devuelve distancia en kilómetros entre dos pares lat/lon."""
    R = 6371.0
    lat1_rad, lon1_rad = radians(lat1), radians(lon1)
    lat2_rad, lon2_rad = radians(lat2), radians(lon2)
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    a = sin(dlat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

# -------------------------
# Modelos de datos
# -------------------------
class CentroReciclaje:
    def __init__(self, nombre: Optional[str]=None, lat: Optional[float]=None, lon: Optional[float]=None,
                 horario: Optional[str]=None, materiales: Optional[Any]=None, ubicacion: Optional[str]=None, **kwargs):
        self.nombre = nombre if nombre else "Nombre no disponible"
        self.lat = float(lat) if lat is not None else 0.0
        self.lon = float(lon) if lon is not None else 0.0
        self.horario = horario if horario else "No disponible"
        self.ubicacion = ubicacion if ubicacion else self.nombre
        self.distance: Optional[float] = None

        # Normalizar materiales a lista de lowercase
        if isinstance(materiales, str):
            temp_list = materiales.split(',')
            self.materiales = [m.strip().lower() for m in temp_list if m.strip()]
        elif isinstance(materiales, list):
            self.materiales = [str(m).lower().strip() for m in materiales]
        else:
            self.materiales = []

# -------------------------
# Motor de reglas
# -------------------------
class Regla:
    def __init__(self, condicions_str: str, conclusiones: str):
        self.conclusiones = conclusiones
        self.condiciones_list = []
        for cond in condicions_str.split(';'):
            if ':' in cond:
                k, v = cond.split(':', 1)
                self.condiciones_list.append((k.strip().lower(), v.strip().lower()))

    def checar_condiciones(self, centro: CentroReciclaje) -> bool:
        for key, val in self.condiciones_list:
            if key == 'material':
                if val not in centro.materiales:
                    return False
            elif key == 'horario':
                if val not in centro.horario.lower():
                    return False
            elif key == 'ubicacion':
                if val != centro.ubicacion.lower():
                    return False
            else:
                # Si hay una condición desconocida, la ignoramos (o podrías añadir más reglas)
                pass
        return True

# -------------------------
# Inicializar Firebase (st.secrets)
# -------------------------
@st.cache_resource
def init_firebase_from_secrets() -> Optional[firestore.Client]:
    try:
        # Debes tener en Settings->Secrets un bloque [firebase] similar al ejemplo que te di.
        if not firebase_admin._apps:
            firebase_secret = st.secrets["firebase"]
            # Construimos dict con saltos de línea correctos en private_key
            creds = dict(firebase_secret)
            if "private_key" in creds:
                creds["private_key"] = creds["private_key"].replace("\\n", "\n")
            cred = credentials.Certificate(creds)
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except KeyError:
        st.error("Error: No se encontró la configuración 'firebase' en st.secrets. Revisa Settings → Secrets.")
        return None
    except Exception as e:
        st.error(f"Error al inicializar Firebase: {e}")
        st.exception(e)
        return None

# -------------------------
# Cargar centros y reglas
# -------------------------
@st.cache_resource
def load_and_create_centros(_db: firestore.Client) -> List[CentroReciclaje]:
    if _db is None:
        return []
    try:
        docs = _db.collection("centros_reciclaje").stream()
        centros = []
        for d in docs:
            data = d.to_dict()
            centros.append(CentroReciclaje(**data))
        return centros
    except Exception as e:
        st.error(f"Error leyendo 'centros_reciclaje' desde Firestore: {e}")
        st.exception(e)
        return []

@st.cache_resource
def load_rules(_db: firestore.Client) -> List[Regla]:
    if _db is None:
        return []
    reglas = []
    try:
        docs = _db.collection("reglas").stream()
        for d in docs:
            data = d.to_dict()
            # Suponemos que 'conclusion' existe y las condiciones son campos que empiezan con 'condicion'
            if "conclusion" in data:
                condiciones = [str(v) for k, v in data.items() if k.startswith("condicion")]
                if condiciones:
                    reglas.append(Regla(";".join(condiciones), data["conclusion"]))
        return reglas
    except Exception as e:
        st.error(f"Error leyendo 'reglas' desde Firestore: {e}")
        st.exception(e)
        return []

# -------------------------
# Clase recomendador (lógica)
# -------------------------
class Recomendador:
    def __init__(self, db_client: firestore.Client):
        self._centros = load_and_create_centros(db_client)
        self._reglas = load_rules(db_client)

    def get_all_centros(self) -> List[CentroReciclaje]:
        return self._centros

    def get_all_materials(self) -> List[str]:
        s = set()
        for c in self._centros:
            for m in c.materiales:
                s.add(m.capitalize())
        return sorted(list(s))

    def filter_by_materials(self, selected_materials: List[str]) -> List[CentroReciclaje]:
        if not selected_materials:
            return self._centros
        selected_lower = [m.lower() for m in selected_materials]
        return [c for c in self._centros if all(x in c.materiales for x in selected_lower)]

    def sort_by_distance(self, user_lat: float, user_lon: float, centros: List[CentroReciclaje]) -> List[CentroReciclaje]:
        for c in centros:
            c.distance = haversine(user_lat, user_lon, c.lat, c.lon)
        return sorted(centros, key=lambda x: x.distance if x.distance is not None else float('inf'))

    def aplicar_motor_logico(self, centros_filtrados: List[CentroReciclaje]) -> Dict[str, List[str]]:
        resultados = {}
        for c in centros_filtrados:
            conclusiones = []
            for r in self._reglas:
                if r.checar_condiciones(c):
                    conclusiones.append(r.conclusiones)
            if conclusiones:
                resultados[c.nombre] = conclusiones
        return resultados

# -------------------------
# Interfaz principal
# -------------------------
def main():
    db_client = init_firebase_from_secrets()
    if db_client is None:
        st.stop()

    recomendador = Recomendador(db_client)

    # Sidebar: filtros
    st.sidebar.header("👇 Filtra tu Búsqueda")
    all_materials = recomendador.get_all_materials()
    selected_materials = st.sidebar.multiselect("1. Selecciona los materiales:", options=all_materials, placeholder="Elige uno o más materiales")
    filtered_centros = recomendador.filter_by_materials(selected_materials)

    st.sidebar.markdown("---")
    st.sidebar.subheader("📍 Obtener ubicación del usuario")

    # Intentamos obtener la ubicación vía streamlit_js_eval si está disponible
    user_lat = None
    user_lon = None
    nearest_center = None

    if HAS_JS_EVAL:
        try:
            st.sidebar.write("Intentando obtener ubicación desde el navegador (permite el permiso cuando aparezca).")
            coords = streamlit_js_eval(js_expressions="navigator.geolocation.getCurrentPosition(p=>window.parent.postMessage(p.coords))")
            # coords puede ser None si el navegador no permite o el mensaje no llega
            if isinstance(coords, dict) and "latitude" in coords and "longitude" in coords:
                user_lat = coords["latitude"]
                user_lon = coords["longitude"]
            else:
                # coords a veces vuelve vacío: no confiar 100%
                user_lat = None
                user_lon = None
        except Exception:
            # No queremos que un fallo de JS rompa la app
            st.sidebar.warning("No se pudo obtener la ubicación automáticamente (fallo en streamlit_js_eval).")
            user_lat = None
            user_lon = None
    else:
        st.sidebar.info("streamlit_js_eval no está instalado. Usa coordenadas manuales o agrégalo al requirements.txt.")

    # Fallbacks: entrada manual o ubicación por defecto
    if user_lat is None or user_lon is None:
        st.sidebar.markdown("**Fallback:** introduce coordenadas manualmente (si lo deseas).")
        manual_lat = st.sidebar.text_input("Latitud (manual)", value="")
        manual_lon = st.sidebar.text_input("Longitud (manual)", value="")
        if manual_lat.strip() and manual_lon.strip():
            try:
                user_lat = float(manual_lat)
                user_lon = float(manual_lon)
            except ValueError:
                st.sidebar.error("Coordenadas manuales no válidas. Deben ser números (ej: 19.4326, -99.1332).")
                user_lat = None
                user_lon = None

    # Si aún no hay coords, podemos usar una ubicación por defecto (ejemplo: Ciudad de México)
    if user_lat is None or user_lon is None:
        if st.sidebar.checkbox("Usar ubicación por defecto (Ciudad de México)"):
            user_lat, user_lon = 19.4326, -99.1332
            st.sidebar.info("Usando ubicación por defecto: Ciudad de México.")

    # Procesamiento principal: ordenar por distancia si hay ubicación
    if user_lat is not None and user_lon is not None:
        filtered_centros = recomendador.sort_by_distance(user_lat, user_lon, filtered_centros)
        if filtered_centros:
            nearest_center = filtered_centros[0]

    # Métricas principales
    col1, col2 = st.columns(2)
    col1.metric(label="Centros encontrados", value=len(filtered_centros))
    if nearest_center:
        col2.metric(label="Centro más cercano", value=nearest_center.nombre, delta=f"- {nearest_center.distance:.2f} km", delta_color="off")
    else:
        col2.metric(label="Centro más cercano", value="N/A")

    st.markdown("---")

    # Visualización: mapa + tabla
    if filtered_centros:
        col_map, col_data = st.columns([0.6, 0.4])

        with col_map:
            st.subheader("Ubicación en el Mapa")
            map_center = [user_lat, user_lon] if user_lat else [19.4326, -99.1332]
            zoom_level = 13 if user_lat else 10
            m = folium.Map(location=map_center, zoom_start=zoom_level)
            # Marcadores de centros
            for c in filtered_centros:
                folium.Marker(
                    location=[c.lat, c.lon],
                    popup=f"<b>{c.nombre}</b><br>Horario: {c.horario}",
                    tooltip=c.ubicacion
                ).add_to(m)
            # Marcador del usuario
            if user_lat:
                folium.Marker(
                    location=[user_lat, user_lon],
                    popup="<b>Tu Ubicación</b>",
                    icon=folium.Icon(color='red', icon='user', prefix='fa')
                ).add_to(m)
            # Línea al centro más cercano
            if nearest_center and user_lat:
                folium.PolyLine(locations=[(user_lat, user_lon), (nearest_center.lat, nearest_center.lon)],
                                weight=3, dash_array='5, 10').add_to(m)

            st_folium(m, width='100%', height=600)

        with col_data:
            st.subheader("Detalles (ordenados)")
            df_display = []
            for c in filtered_centros:
                entry = {
                    "nombre": c.nombre,
                    "distance": f"{c.distance:.2f} km" if c.distance is not None else "N/A",
                    "ubicacion": c.ubicacion,
                    "horario": c.horario,
                    "materiales": ", ".join([m.capitalize() for m in c.materiales])
                }
                df_display.append(entry)
            df = pd.DataFrame(df_display)
            st.dataframe(df, use_container_width=True)

    else:
        st.warning("No se encontraron centros con esos filtros.")

    st.markdown("---")
    # Motor lógico: mostrar resultados si hay centros
    with st.expander("Ver Recomendaciones del Motor Lógico (de Firebase)"):
        if filtered_centros:
            resultados = recomendador.aplicar_motor_logico(filtered_centros)
            if resultados:
                st.subheader("💡 Recomendaciones especiales:")
                for nombre, conclusiones in resultados.items():
                    st.markdown(f"#### {nombre}")
                    for c in conclusiones:
                        st.success(f"**Regla disparada:** {c}")
                    st.markdown("---")
            else:
                st.success("✅ Ninguno de los centros filtrados disparó una regla lógica.")
        else:
            st.info("No hay centros en los que aplicar reglas.")

    # Botón opcional para guardar la ubicación del usuario en Firestore
    if user_lat and user_lon:
        if st.button("Guardar mi ubicación en Firestore"):
            try:
                db_client.collection("ubicaciones").add({
                    "latitud": float(user_lat),
                    "longitud": float(user_lon)
                })
                st.success("Ubicación guardada en Firestore.")
            except Exception as e:
                st.error(f"No se pudo guardar la ubicación: {e}")
                st.exception(e)

if __name__ == "__main__":
    main()
