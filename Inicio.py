import streamlit as st
import os

# CORRECCIÓN 1: st.set_page_config() debe ser el primer comando de Streamlit.
st.set_page_config(
    page_title="Inicio - Buscador de Reciclaje",
    page_icon="♻️",
    layout="centered"
)

# CORRECCIÓN 2: Creamos una ruta individual para CADA imagen que queremos cargar localmente.
assets_dir = "assets"
header_image = os.path.join(assets_dir, "photo-1532996122724-e3c354a0b15b.jpeg")
icon_ubicate = os.path.join(assets_dir, "3477113.png")
icon_filtra = os.path.join(assets_dir, "3500826.png")
# Nota: La imagen 'search...' no se usaba, la reemplacé por la correcta del ejemplo anterior.
icon_encuentra = os.path.join(assets_dir, "search_24dp_000000_FILL0_wght400_GRAD0_opsz24.png")

# --- Encabezado ---
# CORRECCIÓN 3: Reemplazamos la URL por nuestra ruta local y comprobamos si existe.
if os.path.exists(header_image):
    # CORRECCIÓN 4: Se usa 'use_column_width=True' para ajustar la imagen al ancho, no 'width'.
    st.image(header_image, width='stretch')
else:
    st.warning("No se encontró la imagen de cabecera en la carpeta 'assets'.")

st.title("Sistema Inteligente de Reciclaje")
st.markdown("¡Bienvenido! Te ayudamos a encontrar el centro de reciclaje ideal para ti de la forma más fácil.")
st.markdown("---")

# --- Sección "¿Cómo Funciona?" ---
st.header("¿Cómo Funciona? 🤔")
col1, col2, col3 = st.columns(3, gap="large")

with col1:
    if os.path.exists(icon_ubicate):
        st.image(icon_ubicate, width=100)
    st.subheader("1. Ubícate")
    st.write("Permite el acceso a tu ubicación para encontrar las opciones más cercanas a ti.")

with col2:
    if os.path.exists(icon_filtra):
        st.image(icon_filtra, width=100)
    st.subheader("2. Filtra")
    st.write("Selecciona los materiales específicos que deseas reciclar (plástico, vidrio, etc.).")

with col3:
    if os.path.exists(icon_encuentra):
        st.image(icon_encuentra, width=100)
    st.subheader("3. Encuentra")
    st.write("Visualiza los centros en el mapa, ordenados por distancia, y elige el mejor para ti.")

st.markdown("---")

# --- Expanders de Información ---
st.subheader("Más Información Sobre el Proyecto")
with st.expander("🌍 Contexto y Problema"):
    st.write("""
    **Contexto:** En un mundo que enfrenta desafíos ambientales crecientes, el reciclaje se ha convertido en una práctica esencial. Aunque la conciencia ha aumentado, muchas personas luchan por encontrar centros de reciclaje adecuados. 

    **Problema:** La principal dificultad para los usuarios es identificar centros de reciclaje que se ajusten a su ubicación, horario y, crucialmente, a los **tipos de materiales que aceptan**.
    """)

with st.expander("🌱 Alineación con los Objetivos de Desarrollo Sostenible (ODS)"):
    st.write("""
    Este sistema se alinea con el **ODS 12: Producción y Consumo Responsables**. Específicamente, contribuye a las metas:
    - **12.5:** Reducir considerablemente la generación de desechos mediante reciclado y reutilización.
    - **12.8:** Asegurar que las personas tengan la información pertinente para estilos de vida en armonía con la naturaleza.
    """)

# --- Barra Lateral ---
st.sidebar.success("Selecciona una página para navegar.")
st.sidebar.markdown("---")
st.sidebar.header("Desarrollado por:")
st.sidebar.info(
    """
    - Cerón Gonzalez Samantha Yarazet
    - Guerrero Chavez Samuel Antonio
    - Marquez Mejía Araceli
    - Santillán López Mireya
    """
)