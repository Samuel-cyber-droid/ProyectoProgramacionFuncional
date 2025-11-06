# ====================================================================
# --- BLOQUE 1: IMPORTACIONES ---
# ====================================================================
import streamlit as st
import pandas as pd
from typing import List
# Se eliminaron las importaciones de math, folium y geolocation

# Componentes de UI
# (Ya no se necesita streamlit_geolocation)

# Firebase (para la base de datos)
import firebase_admin
from firebase_admin import credentials, firestore


# ====================================================================
# --- BLOQUE 2: CONEXIÓN A FIREBASE (con st.secrets) ---
# ====================================================================

@st.cache_resource
def init_firebase():
    """
    Inicializa la conexión con Firebase usando las credenciales
    guardadas en el archivo secrets.toml (st.secrets).
    """
    try:
        if not firebase_admin._apps:
            secret_creds = st.secrets["firebase_credentials"]
            creds_dict = dict(secret_creds)
            if 'private_key' in creds_dict:
                creds_dict['private_key'] = creds_dict['private_key'].replace('\\n', '\n')
            if not creds_dict:
                st.error("Error: No se encontraron las 'firebase_credentials' en st.secrets.")
                return None
            print("Cargando credenciales desde st.secrets...")
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
    centros_ref = _db.collection('centros_reciclaje')
    docs = centros_ref.stream()

    lista_centros = []
    try:
        for doc in docs:
            data = doc.to_dict()
            lista_centros.append(CentroReciclaje(**data))

        if not lista_centros:
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
        """Constructor robusto que acepta campos opcionales de Firebase."""
        self.nombre = nombre if nombre else "Nombre no disponible"
        self.lat = float(lat) if lat is not None else 0.0
        self.lon = float(lon) if lon is not None else 0.0
        self.horario = horario if horario else "No disponible"
        self.ubicacion = ubicacion if ubicacion else self.nombre
        self.distance = None  # Este campo ya no se usará, pero no daña tenerlo

        # Convierte el STRING 'materiales' en una LISTA
        if isinstance(materiales, str):
            temp_list = materiales.lower().split(',')
            self.materiales = [m.strip() for m in temp_list if m.strip()]
        elif isinstance(materiales, list):
            self.materiales = [str(m).lower().strip() for m in materiales]
        else:
            self.materiales = []


# ====================================================================
# --- BLOQUE 4: PARADIGMA LÓGICO (Motor de Reglas) ---
# ====================================================================

class Regla:
    """Clase que modela una regla 'SI-ENTONCES' leída de Firebase."""

    def __init__(self, condicions_str: str, conclusiones: str):
        self.conclusiones = conclusiones
        self.condiciones_list = []

        # Parsea el string combinado de condiciones
        # Ej: "material:pet;ubicacion:polanco"
        for cond in condicions_str.split(';'):
            if ':' in cond:
                key, val = cond.split(':', 1)
                self.condiciones_list.append((key.strip().lower(), val.strip().lower()))

    def checar_condiciones(self, centro: CentroReciclaje) -> bool:
        """Compara este centro (hecho) con las condiciones de esta regla."""
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
    reglas_ref = _db.collection('reglas')
    docs = reglas_ref.stream()

    lista_reglas = []
    try:
        doc_count = 0
        for doc in docs:
            doc_count += 1
            data = doc.to_dict()
            print(f"Documento {doc_count} encontrado. Campos: {data.keys()}")

            # Lógica mejorada para leer campos 'condicion1', 'condicion2', etc.
            if 'conclusion' in data:
                lista_condiciones_str = []
                for key, value in data.items():
                    if key.startswith('condicion'):
                        lista_condiciones_str.append(str(value))

                if lista_condiciones_str:
                    string_condiciones_combinadas = ";".join(lista_condiciones_str)
                    print(
                        f"¡Éxito! Documento {doc_count} COINCIDE. Añadiendo regla con {len(lista_condiciones_str)} condiciones.")
                    lista_reglas.append(Regla(string_condiciones_combinadas, data['conclusion']))
                else:
                    print(
                        f"AVISO: Documento {doc_count} tiene 'conclusion' pero CERO campos 'condicion...'. Omitiendo.")
            else:
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

# --- La función haversine() fue eliminada ---

class Recomendador:
    """Encapsula toda la lógica de negocio: cargar, filtrar y ordenar los centros."""

    def __init__(self, db_client):
        self._centros: List[CentroReciclaje] = load_and_create_centros(db_client)
        self._reglas: List[Regla] = load_rules(db_client)

    def get_all_centros(self) -> List[CentroReciclaje]:
        return self._centros

    def get_all_materials(self) -> List[str]:
        all_mats = set()
        for centro in self._centros:
            for material in centro.materiales:
                all_mats.add(material.capitalize())
        return sorted(list(all_mats))

    # --- DEMOSTRACIÓN DE PARADIGMA FUNCIONAL ---
    def filter_by_materials(self, selected_materials: List[str]) -> List[CentroReciclaje]:
        if not selected_materials:
            return self._centros
        selected_mats_lower = [m.lower() for m in selected_materials]
        filtered_iterator = filter(
            lambda centro: all(item in centro.materiales for item in selected_mats_lower),
            self._centros
        )
        return list(filtered_iterator)

    # --- El método sort_by_distance() fue eliminado ---

    # --- METODO DEL MOTOR DE INFERENCIA LÓGICA ---
    def aplicar_motor_logico(self, centros_filtrados: List[CentroReciclaje]):
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

        # --- Se eliminó la barra lateral de geolocalización ---

        # 6. VISUALIZACIÓN DE RESULTADOS (Métricas)
        st.metric(label="Centros Encontrados", value=len(filtered_centros))
        st.markdown("---")

        # 7. VISUALIZACIÓN DE RESULTADOS (Mapa y Tabla)
        if filtered_centros:
            col_map, col_data = st.columns([0.6, 0.4])

            with col_map:
                st.subheader("Ubicación en el Mapa")

                # --- REEMPLAZO CON st.map ---
                # 1. Preparamos los datos para st.map
                map_data = pd.DataFrame(
                    [{'lat': centro.lat, 'lon': centro.lon} for centro in filtered_centros
                     if centro.lat is not None and centro.lon is not None]  # Filtro de seguridad
                )

                # 2. Mostramos el mapa (solo si hay datos válidos)
                if not map_data.empty:
                    st.map(map_data, zoom=10)
                else:
                    st.warning("Centros filtrados no tienen coordenadas para mostrar en el mapa.")

            with col_data:
                st.subheader("Detalles de los Centros")
                df_display_data = []
                for centro in filtered_centros:
                    data = vars(centro).copy()
                    # Se elimina el 'distance' de los datos
                    data.pop('distance', None)
                    data['materiales'] = ", ".join(m.capitalize() for m in data['materiales'])
                    df_display_data.append(data)

                df_display = pd.DataFrame(df_display_data)

                # Se quita 'distance' del orden de columnas
                st.dataframe(df_display, width='stretch',
                             column_order=("nombre", "ubicacion", "horario", "materiales"))
        else:
            st.warning("No se encontraron centros de reciclaje con esos filtros.")

        # 8. VISUALIZACIÓN DE PROGRAMACIÓN LÓGICA (Motor de Reglas)
        st.markdown("---")
        with st.expander("Ver Recomendaciones del Motor Lógico (de Firebase)"):
            if filtered_centros:
                resultados_logicos = recomendador.aplicar_motor_logico(filtered_centros)
                st.info("El motor comparó los centros filtrados contra las reglas de Firebase.")

                if resultados_logicos:
                    st.subheader("💡 Recomendaciones Especiales Encontradas:")
                    for nombre_centro, conclusiones in resultados_logicos.items():
                        st.markdown(f"#### {nombre_centro}")
                        for conclusion in conclusiones:
                            st.success(f"**Regla disparada:** {conclusion}")
                        st.markdown("---")
                else:
                    st.success("✅ Ninguno de los centros filtrados disparó una regla lógica.")
            else:
                st.warning("No hay centros para aplicar el motor lógico.")

except Exception as e:
    st.error(f"Ocurrió un error inesperado en la aplicación: {e}")
    st.exception(e)