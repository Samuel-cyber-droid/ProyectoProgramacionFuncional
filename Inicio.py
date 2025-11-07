# Importamos la librería Streamlit, fundamental para crear la interfaz web.
import streamlit as st
# Importamos el módulo 'os' para interactuar con el sistema operativo,
# específicamente para manejar rutas de archivos de forma robusta.
import os

# --- CONFIGURACIÓN INICIAL DE LA PÁGINA ---
# Es una buena práctica que st.set_page_config() sea el primer comando de Streamlit.
# Define metadatos importantes como el título en la pestaña del navegador, el ícono y el layout.
st.set_page_config(
    page_title="Inicio - Buscador de Reciclaje",
    page_icon="♻️",
    layout="centered"  # 'centered' mantiene el contenido en un ancho fijo y legible.
)

# ---   ANALYTICS    ---
GOOGLE_ANALYTICS_SCRIPT= """
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-GHWRR564SW"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
    
      gtag('config', 'G-GHWRR564SW');
    </script>
"""
st.markdown(GOOGLE_ANALYTICS_SCRIPT, unsafe_allow_html=True)

# --- GESTIÓN DE RUTAS A RECURSOS (ASSETS) ---
# Definimos una carpeta base para los recursos gráficos.
assets_dir = "assets"
# Usamos os.path.join para construir rutas. Esto asegura que el código sea compatible
# con diferentes sistemas operativos (Windows usa '\', Linux/macOS usan '/').
header_image = os.path.join(assets_dir, "photo-1532996122724-e3c354a0b15b.jpeg")
icon_ubicate = os.path.join(assets_dir, "3477113.png")
icon_filtra = os.path.join(assets_dir, "3500826.png")
icon_encuentra = os.path.join(assets_dir, "search_24dp_000000_FILL0_wght400_GRAD0_opsz24.png")

# --- SECCIÓN DE ENCABEZADO ---
# Verificamos si la imagen de cabecera existe antes de intentar mostrarla.
# Esto previene que la aplicación falle si el archivo no se encuentra.
if os.path.exists(header_image):
    # Mostramos la imagen. El argumento 'use_column_width=True' es preferible a un ancho fijo
    # para que la imagen se ajuste de forma responsiva al ancho de la columna o página.
    st.image(header_image, width='stretch')
else:
    # Si la imagen no existe, mostramos una advertencia útil para el desarrollador.
    st.warning("No se encontró la imagen de cabecera en la carpeta 'assets'.")

# Títulos y texto de introducción a la aplicación.
st.title("Sistema Inteligente de Reciclaje")
st.markdown("¡Bienvenido! Te ayudamos a encontrar el centro de reciclaje ideal para ti de la forma más fácil.")
st.markdown("---") # Crea una línea horizontal para separar secciones.

# --- SECCIÓN "¿CÓMO FUNCIONA?" ---
st.header("¿Cómo Funciona? 🤔")
# Creamos tres columnas para organizar el contenido visualmente. 'gap="large"' añade más espacio entre ellas.
col1, col2, col3 = st.columns(3, gap="large")

# Usamos un bloque 'with' para asignar contenido a cada columna.
with col1:
    # Verificamos la existencia de cada ícono antes de mostrarlo.
    if os.path.exists(icon_ubicate):
        st.image(icon_ubicate, width=100) # Usamos un ancho fijo para íconos pequeños.
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

# --- SECCIÓN DE INFORMACIÓN ADICIONAL (EXPANDERS) ---
st.subheader("Más Información Sobre el Proyecto")
# st.expander crea una sección colapsable, ideal para mostrar información detallada sin saturar la página.
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

# --- BARRA LATERAL (SIDEBAR) ---
# El contenido dentro de st.sidebar aparecerá en el menú lateral izquierdo.
st.sidebar.success("Selecciona una página para navegar.")
st.sidebar.markdown("---")
st.sidebar.header("Desarrollado por:")
# st.sidebar.info es un buen componente para mostrar información secundaria o de autoría.
st.sidebar.info(
    """
    - Cerón Gonzalez Samantha Yarazet
    - Guerrero Chavez Samuel Antonio
    - Marquez Mejía Araceli
    - Santillán López Mireya
    """
)