# --- IMPORTACIONES NECESARIAS ---
import streamlit as st
import pandas as pd
import json
from typing import List
from math import radians, sin, cos, sqrt, atan2
# Componente de terceros para obtener la geolocalización del usuario en el navegador.
from streamlit_geolocation import streamlit_geolocation
# Folium es una librería para crear mapas interactivos.
import folium
# st_folium es el componente que permite renderizar mapas de Folium dentro de Streamlit.
from streamlit_folium import st_folium


# --- FUNCIÓN DE CARGA DE DATOS CON CACHÉ ---
# El decorador @st.cache_resource le dice a Streamlit que ejecute esta función solo una vez.
# El resultado (la lista de objetos CentroReciclaje) se guarda en memoria (caché).
# En las siguientes ejecuciones, Streamlit reutilizará el resultado cacheado en lugar de releer el archivo.
# Esto mejora drásticamente el rendimiento de la aplicación.
@st.cache_resource
def load_and_create_centros(path: str) -> List['CentroReciclaje']:
    """Lee un archivo JSON y lo convierte en una lista de objetos CentroReciclaje."""
    with open(path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    # Se utiliza una comprensión de listas para crear los objetos de forma concisa.
    return [CentroReciclaje(**centro) for centro in data]


# --- MODELO DE DATOS: CLASE PARA CENTROS DE RECICLAJE ---
class CentroReciclaje:
    """Clase que representa un único centro de reciclaje. Modela la estructura de nuestros datos."""

    def __init__(self, nombre, lat, lon, horario, materiales):
        self.nombre = nombre
        self.lat = lat
        self.lon = lon
        self.horario = horario
        self.materiales = materiales
        self.distance = None  # Se inicializa como None y se calculará después.


# --- FUNCIÓN PURA: CÁLCULO DE DISTANCIA ---
def haversine(lat1, lon1, lat2, lon2):
    """
    Calcula la distancia en kilómetros entre dos puntos geográficos (lat, lon).
    Esta es una función pura: para las mismas entradas, siempre produce la misma salida
    y no tiene efectos secundarios.
    """
    R = 6371.0  # Radio de la Tierra en km.
    lat1_rad, lon1_rad = radians(lat1), radians(lon1)
    lat2_rad, lon2_rad = radians(lat2), radians(lon2)
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    a = sin(dlat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c
    return distance


# --- LÓGICA DE NEGOCIO: CLASE RECOMENDADOR ---
class Recomendador:
    """Encapsula toda la lógica de negocio: cargar, filtrar y ordenar los centros."""

    def __init__(self, data_path: str):
        # Al crear una instancia, se cargan los datos usando nuestra función con caché.
        self._centros: List[CentroReciclaje] = load_and_create_centros(data_path)

    def get_all_materials(self) -> List[str]:
        """Obtiene una lista única y ordenada de todos los materiales disponibles."""
        all_mats = set()  # Usamos un 'set' para evitar duplicados automáticamente.
        for centro in self._centros:
            for material in centro.materiales:
                all_mats.add(material)
        return sorted(list(all_mats))  # Convertimos a lista y ordenamos.

    def filter_by_materials(self, selected_materials: List[str]) -> List[CentroReciclaje]:
        """
        Filtra los centros basándose en los materiales seleccionados.
        Este es un excelente ejemplo de paradigma funcional.
        """
        if not selected_materials:
            return self._centros  # Si no hay selección, devuelve todos los centros.

        # 'filter' es una función de orden superior que toma una función (lambda) y un iterable.
        # La lambda verifica si TODOS ('all') los materiales seleccionados están en los materiales de un centro.
        # Esto es más declarativo que un bucle 'for' con un 'if'.
        filtered_iterator = filter(
            lambda centro: all(item in centro.materiales for item in selected_materials),
            self._centros
        )
        return list(filtered_iterator)

    def sort_by_distance(self, user_lat, user_lon, centros: List[CentroReciclaje]) -> List[CentroReciclaje]:
        """Calcula la distancia de cada centro al usuario y los ordena de menor a mayor."""
        # Primero, calcula y asigna la distancia a cada objeto 'CentroReciclaje'.
        for centro in centros:
            centro.distance = haversine(user_lat, user_lon, centro.lat, centro.lon)

        # 'sorted' es otra función de estilo funcional.
        # La 'key' lambda le dice a 'sorted' que use el atributo 'distance' de cada objeto como criterio de ordenación.
        return sorted(centros, key=lambda centro: centro.distance)


# --- INTERFAZ DE STREAMLIT ---
st.set_page_config(layout="wide")
st.title("♻️ Buscador Inteligente de Centros de Reciclaje")

# Bloque try-except para manejar cualquier error inesperado y mostrar un mensaje amigable.
try:
    # 1. INICIALIZACIÓN
    # Creamos una instancia de nuestro recomendador. Los datos se cargarán aquí (probablemente desde caché).
    recomendador = Recomendador('centros_reciclaje.json')

    # 2. BARRA LATERAL (INPUTS DEL USUARIO)
    st.sidebar.header("👇 Filtra tu Búsqueda")
    all_materials = recomendador.get_all_materials()
    # st.multiselect permite al usuario elegir cero o más opciones de una lista.
    selected_materials = st.sidebar.multiselect(
        "1. Selecciona los materiales:",
        options=all_materials,
        placeholder="Elige uno o más materiales"
    )
    # Aplicamos el primer filtro basado en la selección del usuario.
    filtered_centros = recomendador.filter_by_materials(selected_materials)

    st.sidebar.markdown("---")
    st.sidebar.subheader("📍 Encuentra el más cercano")
    # Este componente solicita al navegador la ubicación del usuario (requiere permiso).
    location = streamlit_geolocation()

    # 3. PROCESAMIENTO PRINCIPAL
    user_lat, user_lon = None, None
    nearest_center = None

    # Si obtuvimos una ubicación válida del usuario...
    if location and location.get('latitude'):
        user_lat, user_lon = location['latitude'], location['longitude']
        st.sidebar.success(f"Ubicación obtenida: Lat: {user_lat:.4f}, Lon: {user_lon:.4f}")
        # Aplicamos el segundo filtro: ordenar por distancia.
        filtered_centros = recomendador.sort_by_distance(user_lat, user_lon, filtered_centros)
        if filtered_centros:
            # El centro más cercano será el primero de la lista ordenada.
            nearest_center = filtered_centros[0]

    # 4. VISUALIZACIÓN DE RESULTADOS
    # st.metric es ideal para mostrar KPIs o datos clave de un vistazo.
    col1, col2 = st.columns(2)
    col1.metric(label="Centros Encontrados", value=len(filtered_centros))
    if nearest_center:
        col2.metric(label="Centro más cercano", value=nearest_center.nombre,
                    delta=f"- {nearest_center.distance:.2f} km",
                    delta_color="off")  # 'delta' muestra un cambio o diferencia.
    st.markdown("---")

    # Si la lista de centros filtrados no está vacía, mostramos el mapa y la tabla.
    if filtered_centros:
        col_map, col_data = st.columns([0.6, 0.4])  # Dividimos el espacio: 60% para el mapa, 40% para la tabla.

        with col_map:
            st.subheader("Ubicación en el Mapa")
            # Definimos el centro del mapa: la ubicación del usuario si la tenemos, o un punto por defecto (CDMX).
            map_center = [user_lat, user_lon] if user_lat else [19.4326, -99.1332]
            zoom_level = 13 if user_lat else 10

            # Creamos el objeto mapa de Folium.
            m = folium.Map(location=map_center, zoom_start=zoom_level)

            # Iteramos sobre los centros filtrados para añadir un marcador para cada uno.
            for centro in filtered_centros:
                folium.Marker(
                    location=[centro.lat, centro.lon],
                    popup=f"<b>{centro.nombre}</b><br>Horario: {centro.horario}",  # Contenido HTML del popup.
                    tooltip="Clic para ver detalles"
                ).add_to(m)

            # Si tenemos la ubicación del usuario, añadimos un marcador especial para él.
            if user_lat:
                folium.Marker(
                    location=[user_lat, user_lon],
                    popup="<b>Tu Ubicación</b>",
                    icon=folium.Icon(color='red', icon='user', prefix='fa')  # Ícono rojo de usuario.
                ).add_to(m)

            # Si hay un centro cercano, dibujamos una línea punteada desde el usuario hasta él.
            if nearest_center:
                points = [(user_lat, user_lon), (nearest_center.lat, nearest_center.lon)]
                folium.PolyLine(
                    locations=points,
                    color='red',
                    weight=2,
                    dash_array='5, 10'  # '5px de línea, 10px de espacio' crea el efecto punteado.
                ).add_to(m)

            # Renderizamos el mapa en la interfaz de Streamlit.
            st_folium(m, width='stretch')

        with col_data:
            st.subheader("Detalles de los Centros (ordenados por distancia)")
            # Usamos pandas DataFrame para mostrar los datos en una tabla limpia y ordenada.
            # Pre-procesamos la lista de objetos para formatear la distancia.
            df_display_data = []
            for centro in filtered_centros:
                data = vars(centro).copy()  # Convertimos el objeto a diccionario.
                if data['distance'] is not None:
                    data['distance'] = f"{data['distance']:.2f} km"
                df_display_data.append(data)

            df_display = pd.DataFrame(df_display_data)
            # st.dataframe muestra el DataFrame en una tabla interactiva.
            st.dataframe(df_display, width='stretch')
    else:
        # Si no se encontraron centros, mostramos un mensaje informativo.
        st.warning("No se encontraron centros de reciclaje. Intenta con menos filtros.")

except Exception as e:
    # Si ocurre cualquier error en el bloque 'try', se captura y se muestra aquí.
    st.error(f"Ocurrió un error inesperado: {e}")