import streamlit as st

st.set_page_config(
    page_title="Proyecto Final",
    page_icon="♻️",
)

st.title("Sistema de Recomendación de Centros de Reciclaje")
st.sidebar.success("Selecciona una página para navegar.")

st.header("1.1 Contexto")
st.write("""
En un mundo que enfrenta desafíos ambientales crecientes, el reciclaje se ha convertido en una práctica esencial.
Aunque la conciencia ha aumentado, muchas personas luchan por encontrar centros de reciclaje adecuados para sus necesidades específicas.
Este sistema busca resolver esa brecha.
""")

st.header("1.2 Problema Identificado")
st.write("""
La principal dificultad para los usuarios es identificar centros de reciclaje que se ajusten a su ubicación, horario y, crucialmente, a los **tipos de materiales que aceptan**.
La falta de información clara provoca que materiales reciclables terminen en la basura común.
""")

st.header("1.3 ODS y Metas del Objetivo")
st.write("""
Este sistema se alinea con el **Objetivo de Desarrollo Sostenible (ODS) 12: Producción y Consumo Responsables**.
Específicamente, contribuye a las metas:
- **12.5:** Reducir considerablemente la generación de desechos mediante reciclado y reutilización.
- **12.8:** Asegurar que las personas tengan la información pertinente para estilos de vida en armonía con la naturaleza.
""")

st.info("Navega a la página **'Buscador de Centros'** en el menú de la izquierda para comenzar.", icon="👈")