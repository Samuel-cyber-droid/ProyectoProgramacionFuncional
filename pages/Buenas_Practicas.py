import streamlit as st

# Configuración de la página, usando 'layout="wide"' para que el contenido ocupe todo el ancho de la pantalla.
st.set_page_config(
    page_title="Buenas Prácticas de Reciclaje",
    page_icon="♻️",
    layout="wide"
)

# --- TÍTULO Y DESCRIPCIÓN ---
st.title("♻️ Guía de Buenas Prácticas de Reciclaje")
st.markdown(
    "Adoptar hábitos sencillos puede marcar una gran diferencia. Aquí tienes algunos consejos clave para reciclar de manera más efectiva.")
st.markdown("---")

# --- CONTENIDO PRINCIPAL EN DOS COLUMNAS ---
# Usamos columnas para presentar la información de una manera más atractiva y fácil de leer,
# evitando una lista vertical muy larga.
col1, col2 = st.columns(2, gap="large")

# Contenido de la primera columna.
with col1:
    st.subheader("🧼 1. Limpia los Envases")
    # st.info crea una caja azul, ideal para resaltar información o consejos clave.
    st.info(
        """
        **¿Por qué?** Los restos de comida pueden contaminar lotes enteros de material reciclable, haciéndolos inutilizables.
        - **Acción:** Enjuaga botellas, latas y recipientes de plástico o vidrio antes de depositarlos. No necesitan estar perfectos, solo sin residuos orgánicos.
        """
    )

    st.subheader("📦 3. Papel y Cartón, Limpios y Secos")
    st.info(
        """
        **¿Por qué?** El papel o cartón manchado con grasa, aceite o humedad no se puede reciclar, ya que las fibras están dañadas.
        - **Acción:** Cajas de pizza con grasa, servilletas usadas o papel mojado deben ir a la basura orgánica o general. Asegúrate de que el material esté seco y doblado.
        """
    )

    st.subheader("🔋 5. Pilas y Electrónicos: ¡Cuidado Especial!")
    st.info(
        """
        **¿Por qué?** Contienen materiales tóxicos como mercurio o litio que son muy dañinos para el medio ambiente si terminan en la basura común.
        - **Acción:** NUNCA los tires a la basura. Llévalos a puntos de recolección especiales. Muchos supermercados y centros comerciales tienen contenedores específicos para pilas.
        """
    )

# Contenido de la segunda columna.
with col2:
    st.subheader("💧 2. Aplasta las Botellas y Latas")
    st.info(
        """
        **¿Por qué?** Ahorra una cantidad enorme de espacio, tanto en tu casa como en los camiones de recolección, haciendo el proceso más eficiente.
        - **Acción:** Después de limpiarlas, aplasta las botellas de plástico (PET) y las latas de aluminio. Si puedes, vuelve a ponerles la tapa.
        """
    )

    st.subheader("🚫 4. Conoce lo que NO se Recicla (Comúnmente)")
    st.info(
        """
        **¿Por qué?** Depositar basura en el contenedor de reciclaje se llama "contaminación" y puede arruinar el esfuerzo de todos.
        - **No reciclables comunes:** Bolsas de plástico delgadas, popotes/pajitas, vasos de café de cartón encerado, pañales, servilletas usadas. En caso de duda, es mejor no depositarlo.
        """
    )

    st.subheader("🔍 6. Separa por Tipo de Material")
    st.info(
        """
        **¿Por qué?** Facilita enormemente el trabajo en las plantas de reciclaje.
        - **Acción:** Si en tu localidad hay contenedores separados, úsalos correctamente:
            - **Orgánico:** Restos de comida.
            - **Papel y Cartón:** Cajas, periódicos, hojas.
            - **Vidrio:** Botellas y frascos.
            - **Plásticos y Metales:** Envases, latas, etc.
        """
    )

st.markdown("---")
# st.success crea una caja verde, perfecta para un mensaje final de conclusión o éxito.
st.success("¡Cada pequeña acción cuenta para construir un futuro más sostenible! Gracias por tu esfuerzo.")