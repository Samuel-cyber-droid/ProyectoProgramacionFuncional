import streamlit as st

st.set_page_config(
    page_title="Inicio - Buscador de Reciclaje",
    page_icon="♻️",
    layout="centered"
)

# --- Encabezado ---
st.image("https://images.unsplash.com/photo-1532996122724-e3c354a0b15b", width='stretch')
st.title("Sistema Inteligente de Reciclaje")
st.markdown("¡Bienvenido! Te ayudamos a encontrar el centro de reciclaje ideal para ti de la forma más fácil.")
st.markdown("---")

# ### NUEVO: Sección "¿Cómo Funciona?"
st.header("¿Cómo Funciona? 🤔")
col1, col2, col3 = st.columns(3, gap="large")

with col1:
    st.image("https://cdn-icons-png.flaticon.com/512/3477/3477113.png", width=100)
    st.subheader("1. Ubícate")
    st.write("Permite el acceso a tu ubicación para encontrar las opciones más cercanas a ti.")

with col2:
    st.image("https://cdn-icons-png.flaticon.com/512/3500/3500826.png", width=100)
    st.subheader("2. Filtra")
    st.write("Selecciona los materiales específicos que deseas reciclar (plástico, vidrio, etc.).")

with col3:
    st.image("https://cdn-icons-png.flaticon.com/512/9906/9906471.png", width=100)
    st.subheader("3. Encuentra")
    st.write("Visualiza los centros en el mapa, ordenados por distancia, y elige el mejor para ti.")

st.markdown("---")

# --- Mantenemos los expanders para información detallada ---
st.subheader("Más Información Sobre el Proyecto")
with st.expander("🌍 Contexto y Problema"):
    st.write("""
    **Contexto:** En un mundo que enfrenta desafíos ambientales crecientes, el reciclaje se ha convertido en una práctica esencial. Aunque la conciencia ha aumentado, muchas personas luchan por encontrar centros de reciclaje adecuados. 

    **Problema:** La principal dificultad para los usuarios es identificar centros de reciclaje que se ajusten a su ubicación, horario y, crucialmente, a los **tipos de materiales que aceptan**
    """)

with st.expander("🌱 Alineación con los Objetivos de Desarrollo Sostenible (ODS)"):
    st.write("""
    Este sistema se alinea con el **ODS 12: Producción y Consumo Responsables** Específicamente, contribuye a las metas:
    - **12.5:** Reducir considerablemente la generación de desechos mediante reciclado y reutilización
    - **12.8:** Asegurar que las personas tengan la información pertinente para estilos de vida en armonía con la naturaleza
    """)

# --- Modificamos la barra lateral para incluir los créditos ---
st.sidebar.success("Selecciona una página para navegar.")

# ### NUEVO: Sección de créditos en la barra lateral ###
st.sidebar.markdown("---")
st.sidebar.header("Desarrollado por:")
# CÓDIGO CON ERROR
st.sidebar.info(
    """
    - Cerón Gonzalez Samantha Yarazet
    - Guerrero Chavez Samuel Antonio
    - Marquez Mejía Araceli
    - Santillán López Mireya
    """
)