# ====================================================================
# --- BLOQUE 1: IMPORTACIONES ---
# ====================================================================
import streamlit as st
import pandas as pd
from typing import List
from math import radians, sin, cos, sqrt, atan2

# Componentes de UI
from streamlit_geolocation import streamlit_geolocation
import folium
from streamlit_folium import st_folium

# Firebase (para la base de datos)
import firebase_admin
from firebase_admin import credentials, firestore

# ====================================================================
# --- BLOQUE 2: CONEXIÓN A FIREBASE (con st.secrets) ---
# ====================================================================

# Usamos @st.cache_resource para que esto se ejecute UNA SOLA VEZ.
@st.cache_resource
def init_firebase():
    """
    Inicializa la conexión con Firebase usando las credenciales
    guardadas en el archivo secrets.toml (st.secrets).
    """
    try:
        if not firebase_admin._apps:  # Evita reinicializar la app
            # 1. Leemos las credenciales (son de solo lectura)
            secret_creds = st.secrets["firebase_credentials"]
            # 2. Hacemos una COPIA a un diccionario normal
            creds_dict = dict(secret_creds)
            # 3. Ahora SÍ podemos modificar nuestra copia
            if 'private_key' in creds_dict:
                creds_dict['private_key'] = creds_dict['private_key'].replace('\\n', '\n')
            if not creds_dict:
                st.error("Error: No se encontraron las 'firebase_credentials' en st.secrets.")
                return None
            print("Cargando credenciales desde st.secrets...")
            # 4. Usamos la COPIA modificada para inicializar
            cred = credentials.Certificate(creds_dict)
            firebase_admin.initialize_app(cred)
            print("--- Conexión a Firebase exitosa (desde st.secrets) ---")
        return firestore.client()
    except KeyError:
        st.error("Error: Faltan las 'firebase_credentials' en tu archivo .streamlit/secrets.toml")
        return None
    except Exception as e:
        st.error(f"Error al inicializar Firebase desde st.secrets: {e}")
        return None


@st.cache_resource
def load_and_create_centros(_db) -> List['CentroReciclaje']:
    """Lee la colección 'centros_reciclaje' de Firebase y la convierte en objetos CentroReciclaje."""
    if _db is None:
        st.error("No se pudo conectar a Firebase. La aplicación no puede cargar datos.")
        return []

    print("--- LEYENDO DATOS DESDE FIREBASE ---")
    centros_ref = _db.collection('centros_reciclaje') # <-- Apuntando a tu colección
    docs = centros_ref.stream()

    lista_centros = []
    try:
        for doc in docs:
            data = doc.to_dict()
            lista_centros.append(CentroReciclaje(**data))

        if not lista_centros:
            # Corregido el typo en el nombre de la colección
            print("--- ADVERTENCIA: Se conectó a Firebase pero no se encontraron documentos en 'centros_reciclaje' ---")
            st.warning("Se conectó a Firebase, pero la colección 'centros_reciclaje' está vacía o no se pudo leer.")
            return []

        print(f"--- Se cargaron {len(lista_centros)} centros desde Firebase ---")
        return lista_centros

    except Exception as e:
        st.error(f"Error al leer datos de Firebase. Revisa la estructura de tus documentos: {e}")
        st.exception(e)
        return []


# ====================================================================
# --- BLOQUE 3: PARADIGMA POO (Modelos de Datos) ---
# ====================================================================

class CentroReciclaje:
    """Clase que representa un único centro de reciclaje. Modela la estructura de nuestros datos."""
    def __init__(self, nombre=None, lat=None, lon=None, horario=None, materiales=None, ubicacion=None, **kwargs):
        """
        Constructor robusto que acepta campos de Firebase.
        **kwargs ignora campos extra que no usamos.
        """
        # Usamos valores por defecto para evitar que la app falle
        self.nombre = nombre if nombre else "Nombre no disponible"
        self.lat = float(lat) if lat is not None else 0.0  # Default a 0.0 si falta
        self.lon = float(lon) if lon is not None else 0.0  # Default a 0.0 si falta

        self.horario = horario if horario else "No disponible"

        # 'ubicacion' es útil para la lógica
        self.ubicacion = ubicacion if ubicacion else self.nombre
        self.distance = None  # Se calculará después.

        # Convierte el STRING 'materiales' en una LISTA
        if isinstance(materiales, str):
            temp_list = materiales.lower().split(',')
            self.materiales = [m.strip() for m in temp_list if m.strip()]
        elif isinstance(materiales, list):
            self.materiales = [str(m).lower().strip() for m in materiales]
        else:
            # Si 'materiales' es None o no existe, crea una lista vacía
            self.materiales = []

# ====================================================================
# --- BLOQUE 4: PARADIGMA LÓGICO (Motor de Reglas) ---
# ====================================================================

class Regla:
    """Clase que modela una regla 'SI-ENTONCES' leída de Firebase."""

    def __init__(self, condicions_str: str, conclusiones: str):
        self.conclusiones = conclusiones
        self.condiciones_list = []  # Lista de tuplas (clave, valor)

        # Parseamos el string de condiciones: "clave1:valor1; clave2:valor2"
        for cond in condicions_str.split(';'):
            if ':' in cond:
                key, val = cond.split(':', 1)  # '1' para que solo separe en el primer ':'
                self.condiciones_list.append((key.strip().lower(), val.strip().lower()))

    def checar_condiciones(self, centro: CentroReciclaje) -> bool:
        """
        Compara este centro (hecho) con las condiciones de esta regla.
        Devuelve True si TODAS las condiciones se cumplen.
        """
        for key, value in self.condiciones_list:
            if key == 'material':
                if value not in centro.materiales:
                    return False
            elif key == 'horario':
                if value not in centro.horario.lower():
                    return False
            elif key == 'ubicacion':
                if value != centro.ubicacion.lower():
                    return False
            else:
                pass
        return True


@st.cache_resource
def load_rules(_db) -> List[Regla]:
    """Lee la colección 'reglas' de Firebase y la convierte en objetos Regla."""
    if _db is None:
        return []

    print("--- LEYENDO REGLAS DESDE FIREBASE ---")
    reglas_ref = _db.collection('reglas')  # Asegúrate que este nombre sea correcto
    docs = reglas_ref.stream()

    lista_reglas = []
    try:
        doc_count = 0
        for doc in docs:
            doc_count += 1
            data = doc.to_dict()

            print(f"Documento {doc_count} encontrado. Campos: {data.keys()}")

            # 1. Primero, revisamos si existe el campo 'conclusion'
            if 'conclusion' in data:
                lista_condiciones_str = []

                # 2. Iteramos sobre todas las claves (campos) del documento
                for key, value in data.items():
                    # 3. Si la clave EMPIEZA CON "condicion"...
                    if key.startswith('condicion'):
                        # ...añadimos su valor (ej. "material:pet") a nuestra lista
                        lista_condiciones_str.append(str(value))

                # 4. Si encontramos al menos una condición...
                if lista_condiciones_str:
                    # 5. Las unimos en un solo string con ';'
                    string_condiciones_combinadas = ";".join(lista_condiciones_str)

                    print(
                        f"¡Éxito! Documento {doc_count} COINCIDE. Añadiendo regla con {len(lista_condiciones_str)} condiciones.")

                    # 6. Creamos la regla con el string combinado
                    lista_reglas.append(Regla(string_condiciones_combinadas, data['conclusion']))
                else:
                    print(
                        f"AVISO: Documento {doc_count} tiene 'conclusion' pero CERO campos 'condicion...'. Omitiendo.")

            else:
                # Si no tiene 'conclusion', se omite
                print(f"AVISO: El Documento {doc_count} fue OMITIDO. No tiene el campo 'conclusion'.")

        if doc_count == 0:
            print("ADVERTENCIA: La colección 'reglas' existe pero está COMPLETAMENTE VACÍA.")

        print(f"--- Se cargaron {len(lista_reglas)} reglas lógicas desde Firebase ---")
        return lista_reglas

    except Exception as e:
        st.error(f"Error al leer la colección 'reglas' de Firebase: {e}")
        return []

# ====================================================================
# --- BLOQUE 5: PARADIGMA POO (Lógica de Negocio) Y FUNCIONAL ---
# ====================================================================

# --- Función Pura (Estilo Funcional) ---
def haversine(lat1, lon1, lat2, lon2):
    """Calcula la distancia en kilómetros entre dos puntos geográficos (lat, lon)."""
    R = 6371.0
    lat1_rad, lon1_rad = radians(lat1), radians(lon1)
    lat2_rad, lon2_rad = radians(lat2), radians(lon2)
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    a = sin(dlat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c
    return distance


class Recomendador:
    """Encapsula toda la lógica de negocio: cargar, filtrar y ordenar los centros."""

    def __init__(self, db_client):
        # Al crear una instancia, se cargan los HECHOS (centros)
        self._centros: List[CentroReciclaje] = load_and_create_centros(db_client)
        # Y también se cargan las REGLAS (lógica)
        self._reglas: List[Regla] = load_rules(db_client)

    def get_all_centros(self) -> List[CentroReciclaje]:
        """Devuelve la lista completa de centros (cargada desde Firebase)."""
        return self._centros

    def get_all_materials(self) -> List[str]:
        """Obtiene una lista única y ordenada de todos los materiales disponibles."""
        all_mats = set()
        for centro in self._centros:
            for material in centro.materiales:
                all_mats.add(material.capitalize())  # Pone mayúscula inicial
        return sorted(list(all_mats))

    # --- DEMOSTRACIÓN DE PARADIGMA FUNCIONAL (Sin Cambios) ---
    def filter_by_materials(self, selected_materials: List[str]) -> List[CentroReciclaje]:
        """Filtra los centros usando la función de orden superior 'filter'."""
        if not selected_materials:
            return self._centros
        selected_mats_lower = [m.lower() for m in selected_materials]
        filtered_iterator = filter(
            lambda centro: all(item in centro.materiales for item in selected_mats_lower),
            self._centros
        )
        return list(filtered_iterator)

    # --- DEMOSTRACIÓN DE PARADIGMA FUNCIONAL (Sin Cambios) ---
    def sort_by_distance(self, user_lat, user_lon, centros: List[CentroReciclaje]) -> List[CentroReciclaje]:
        """Ordena los centros usando la función 'sorted' con una 'key' lambda."""
        for centro in centros:
            centro.distance = haversine(user_lat, user_lon, centro.lat, centro.lon)
        return sorted(centros, key=lambda centro: centro.distance)

    # --- METODO DEL MOTOR DE INFERENCIA LÓGICA ---
    def aplicar_motor_logico(self, centros_filtrados: List[CentroReciclaje]):
        """
        Ejecuta el motor de inferencia.
        Compara los Hechos (centros) contra las Reglas (de Firebase).
        """
        print(f"--- Ejecutando motor lógico con {len(self._reglas)} reglas sobre {len(centros_filtrados)} centros ---")
        resultados_logicos = {}
        for centro in centros_filtrados:
            conclusiones_encontradas = []
            for regla in self._reglas:
                if regla.checar_condiciones(centro):
                    conclusiones_encontradas.append(regla.conclusiones)
            if conclusiones_encontradas:
                resultados_logicos[centro.nombre] = conclusiones_encontradas
        return resultados_logicos


# ====================================================================
# --- BLOQUE 6: INTERFAZ DE STREAMLIT (App Principal) ---
# ====================================================================
st.set_page_config(layout="wide")
st.title("♻️ Buscador Inteligente de Centros de Reciclaje")
st.info("Motor Lógico con Reglas desde Firebase | Conexión segura con st.secrets")

try:
    # 1. INICIALIZACIÓN (POO)
    db_client = init_firebase()
    if db_client:
        recomendador = Recomendador(db_client)
    else:
        st.error("No se pudo inicializar la base de datos. La aplicación se detendrá.")
        st.stop()

    # 2. BARRA LATERAL (INPUTS DEL USUARIO)
    st.sidebar.header("👇 Filtra tu Búsqueda")
    all_materials = recomendador.get_all_materials()

    if not all_materials:
        st.error("No se pudieron cargar datos desde Firebase. Revisa la conexión y la configuración.")
    else:
        selected_materials = st.sidebar.multiselect(
            "1. Selecciona los materiales:",
            options=all_materials,
            placeholder="Elige uno o más materiales"
        )

        # 3. LÓGICA FUNCIONAL (filter)
        filtered_centros = recomendador.filter_by_materials(selected_materials)

        st.sidebar.markdown("---")
        st.sidebar.subheader("📍 Encuentra el más cercano")
        location = streamlit_geolocation()

        # 4. PROCESAMIENTO PRINCIPAL
        user_lat, user_lon = None, None
        nearest_center = None

        if location and location.get('latitude'):
            user_lat, user_lon = location['latitude'], location['longitude']
            st.sidebar.success(f"Ubicación obtenida: Lat: {user_lat:.4f}, Lon: {user_lon:.4f}")
            # 5. LÓGICA FUNCIONAL (sort)
            filtered_centros = recomendador.sort_by_distance(user_lat, user_lon, filtered_centros)
            if filtered_centros:
                nearest_center = filtered_centros[0]

        # 6. VISUALIZACIÓN DE RESULTADOS (Métricas)
        col1, col2 = st.columns(2)
        col1.metric(label="Centros Encontrados", value=len(filtered_centros))
        if nearest_center:
            col2.metric(label="Centro más cercano", value=nearest_center.nombre,
                        delta=f"- {nearest_center.distance:.2f} km",
                        delta_color="off")
        st.markdown("---")

        # 7. VISUALIZACIÓN DE RESULTADOS (Mapa y Tabla)
        if filtered_centros:
            col_map, col_data = st.columns([0.6, 0.4])

            with col_map:
                st.subheader("Ubicación en el Mapa")
                # Corregida la longitud para el centro por defecto
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
                    folium.PolyLine(locations=points, color='red', weight=2, dash_array='5, 10').add_to(m)
                st_folium(m, width='stretch')

            with col_data:
                st.subheader("Detalles de los Centros (ordenados por distancia)")
                df_display_data = []
                for centro in filtered_centros:
                    data = vars(centro).copy()
                    if data['distance'] is not None:
                        data['distance'] = f"{data['distance']:.2f} km"
                    # Corregida la capitalización para cada material
                    data['materiales'] = ", ".join(m.capitalize() for m in data['materiales'])
                    df_display_data.append(data)

                df_display = pd.DataFrame(df_display_data)
                st.dataframe(df_display, width='stretch',
                             column_order=("nombre", "distance", "ubicacion", "horario", "materiales"))
        else:
            st.warning("No se encontraron centros de reciclaje con esos filtros.")

        # 8. VISUALIZACIÓN DE PROGRAMACIÓN LÓGICA (Motor de Reglas)
        st.markdown("---")
        with st.expander("Ver Recomendaciones del Motor Lógico (de Firebase)"):

            if filtered_centros:
                # Ejecutamos el motor lógico SOBRE LOS CENTROS FILTRADOS
                resultados_logicos = recomendador.aplicar_motor_logico(filtered_centros)

                st.info("El motor comparó los centros filtrados contra las reglas de Firebase.")

                if resultados_logicos:

                    st.subheader("💡 Recomendaciones Especiales Encontradas:")

                    for nombre_centro, conclusiones in resultados_logicos.items():

                        # Mostramos el nombre del centro como un encabezado
                        st.markdown(f"#### {nombre_centro}")

                        # Iteramos sobre cada conclusión (regla disparada) para ese centro
                        for conclusion in conclusiones:
                            # st.success muestra un mensaje bonito en una caja verde
                            st.success(f"**Regla disparada:** {conclusion}")

                        st.markdown("---")  # Un separador

                else:
                    st.success("✅ Ninguno de los centros filtrados disparó una regla lógica.")
            else:
                st.warning("No hay centros para aplicar el motor lógico.")

except Exception as e:
    st.error(f"Ocurrió un error inesperado en la aplicación: {e}")
    st.exception(e)