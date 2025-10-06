import streamlit as st
import pandas as pd
import json

# --- 1. Carga de Datos desde JSON ---
# Esta función carga los datos desde el archivo .json
# @st.cache_data asegura que los datos se carguen solo una vez.
@st.cache_data
def load_data(path):
    with open(path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return pd.DataFrame(data)

# --- 2. Interfaz de la Página ---
st.set_page_config(layout="wide")
st.title("🌎 Buscador de Centros de Reciclaje")
st.write("Usa esta herramienta para encontrar centros de reciclaje cercanos.")

try:
    # Cargamos los datos
    df_centros = load_data('centros_reciclaje.json')

    st.subheader("Centros Disponibles en el Mapa")
    st.map(df_centros, latitude='lat', longitude='lon', size=10)

    st.subheader("Detalles de los Centros")
    st.dataframe(df_centros)

except FileNotFoundError:
    st.error(
        "No se encontró el archivo 'centros_reciclaje.json'. "
        "Asegúrate de que el archivo esté en la misma carpeta que 'app.py'."
    )
except Exception as e:
    st.error(f"Ocurrió un error al cargar los datos: {e}")