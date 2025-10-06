import streamlit as st
import pandas as pd
import json
from typing import List
from math import radians, sin, cos, sqrt, atan2
from streamlit_geolocation import streamlit_geolocation
import folium
from streamlit_folium import st_folium


# (El resto de tus clases y funciones se mantiene exactamente igual)
@st.cache_resource
def load_and_create_centros(path: str) -> List['CentroReciclaje']:
    with open(path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return [CentroReciclaje(**centro) for centro in data]


class CentroReciclaje:
    def __init__(self, nombre, lat, lon, horario, materiales):
        self.nombre = nombre
        self.lat = lat
        self.lon = lon
        self.horario = horario
        self.materiales = materiales
        self.distance = None


def haversine(lat1, lon1, lat2, lon2):
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
    def __init__(self, data_path: str):
        self._centros: List[CentroReciclaje] = load_and_create_centros(data_path)

    def get_all_materials(self) -> List[str]:
        all_mats = set()
        for centro in self._centros:
            for material in centro.materiales:
                all_mats.add(material)
        return sorted(list(all_mats))

    def filter_by_materials(self, selected_materials: List[str]) -> List[CentroReciclaje]:
        if not selected_materials:
            return self._centros
        filtered_iterator = filter(
            lambda centro: all(item in centro.materiales for item in selected_materials),
            self._centros
        )
        return list(filtered_iterator)

    def sort_by_distance(self, user_lat, user_lon, centros: List[CentroReciclaje]) -> List[CentroReciclaje]:
        for centro in centros:
            centro.distance = haversine(user_lat, user_lon, centro.lat, centro.lon)
        return sorted(centros, key=lambda centro: centro.distance)


# --- Interfaz de Streamlit ---
st.set_page_config(layout="wide")
st.title("♻️ Buscador Inteligente de Centros de Reciclaje")

try:
    recomendador = Recomendador('centros_reciclaje.json')

    # (La sección de la barra lateral se mantiene igual)
    st.sidebar.header("👇 Filtra tu Búsqueda")
    all_materials = recomendador.get_all_materials()
    selected_materials = st.sidebar.multiselect(
        "1. Selecciona los materiales:",
        options=all_materials,
        placeholder="Elige uno o más materiales"
    )
    filtered_centros = recomendador.filter_by_materials(selected_materials)
    st.sidebar.markdown("---")
    st.sidebar.subheader("📍 Encuentra el más cercano")
    location = streamlit_geolocation()

    user_lat, user_lon = None, None
    nearest_center = None

    if location and location['latitude']:
        user_lat, user_lon = location['latitude'], location['longitude']
        st.sidebar.success(f"Ubicación obtenida: Lat: {user_lat:.4f}, Lon: {user_lon:.4f}")
        filtered_centros = recomendador.sort_by_distance(user_lat, user_lon, filtered_centros)
        if filtered_centros:
            nearest_center = filtered_centros[0]

    # (La sección de métricas se mantiene igual)
    col1, col2 = st.columns(2)
    col1.metric(label="Centros Encontrados", value=len(filtered_centros))
    if nearest_center:
        col2.metric(label="Centro más cercano", value=nearest_center.nombre,
                    delta=f"- {nearest_center.distance:.2f} km", delta_color="off")
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

            ### INICIA EL NUEVO CÓDIGO PARA DIBUJAR LA LÍNEA ###
            # Si hemos encontrado un centro cercano y tenemos la ubicación del usuario...
            if nearest_center:
                # 1. Definimos los puntos de inicio y fin de la línea
                points = [(user_lat, user_lon), (nearest_center.lat, nearest_center.lon)]

                # 2. Creamos la línea punteada y la añadimos al mapa
                folium.PolyLine(
                    locations=points,
                    color='red',
                    weight=2,
                    dash_array='5, 10'  # '5px de línea, 10px de espacio' crea el efecto punteado
                ).add_to(m)
            ### TERMINA EL NUEVO CÓDIGO ###

            st_folium(m, width='stretch')

        with col_data:
            st.subheader("Detalles de los Centros (ordenados por distancia)")
            df_display_data = []
            for centro in filtered_centros:
                data = vars(centro).copy()
                if data['distance'] is not None:
                    data['distance'] = f"{data['distance']:.2f} km"
                df_display_data.append(data)
            df_display = pd.DataFrame(df_display_data)
            st.dataframe(df_display, width='stretch')
    else:
        st.warning("No se encontraron centros de reciclaje. Intenta con menos filtros.")

except Exception as e:
    st.error(f"Ocurrió un error inesperado: {e}")