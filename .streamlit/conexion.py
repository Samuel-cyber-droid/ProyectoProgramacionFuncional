import streamlit as st
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore


# Usamos stcache_resource para inicializar la conexión una sola vez
@st.cache_resource
def init_firebase_connection():
    """
    Inicializa la conexión con Firebase usando las credenciales
    almacenadas en stsecrets.
    """
    try:
        # Intenta obtener la app de Firebase por defecto
        # (para evitar reinicializar si ya existe)
        firebase_admin.get_app()
    except ValueError:
        # Si no existe, inicialízala

        # Carga las credenciales desde st.secrets
        # "firebase_credentials" debe coincidir con el [titulo] en secrets.toml
        creds_dict = st.secrets["firebase_credentials"]

        # Inicializa el SDK de Firebase Admin
        cred = credentials.Certificate(creds_dict)
        firebase_admin.initialize_app(cred)
        print("Firebase inicializado por primera vez.")

    # Retorna el cliente de Firestore
    return firestore.client()


# --- INICIO DE TU APP DE STREAMLIT ---

# 1. Llama a la función para obtener el cliente de Firestore
try:
    db = init_firebase_connection()

    st.title("Mi App de Streamlit con Firebase 🔥")

    # 2. Ejemplo: Leer datos de Firestore
    st.subheader("Datos de mi colección 'usuarios':")

    # Reemplaza 'usuarios' con el nombre de tu colección
    docs_ref = db.collection('usuarios')
    docs = docs_ref.stream()

    # Itera sobre los documentos y muéstralos
    for doc in docs:
        st.write(f"Documento ID: {doc.id}")
        st.json(doc.to_dict())
        st.divider()

    # 3. Ejemplo: Escribir datos en Firestore
    st.subheader("Escribir nuevos datos:")

    nuevo_nombre = st.text_input("Nombre de usuario:")
    if st.button("Guardar en Firebase"):
        if nuevo_nombre:
            # Crea un nuevo documento en la colección 'usuarios'
            doc_ref = db.collection('usuarios').document()
            doc_ref.set({
                'nombre': nuevo_nombre,
                'creado_por': 'Streamlit'
            })
            st.success(f"¡Usuario '{nuevo_nombre}' guardado con éxito!")
            st.balloons()
            # st.rerun() # Opcional: para refrescar la lista de arriba
        else:
            st.warning("Por favor, ingresa un nombre.")

except Exception as e:
    st.error("Error al conectar o interactuar con Firebase:")
    st.error(f"Detalle: {e}")
    st.warning("Asegúrate de haber configurado 'secrets.toml' correctamente.")