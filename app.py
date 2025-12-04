import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Configuración de la página
st.set_page_config(
    page_title="Análisis Conflicto Armado - Medellín",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Función para cargar datos
@st.cache_data
def load_data(file_path):
    df = pd.read_csv(file_path)
    df["fecha_declaracion"] = pd.to_datetime(df["fecha_declaracion"])
    df["ano_declara"] = df["fecha_declaracion"].dt.year
    df["mes_declara"] = df["fecha_declaracion"].dt.month
    return df


# Cargar datos
csv_path = "datos.csv"

if not os.path.exists(csv_path):
    st.error(
        f"No se encontró el archivo '{csv_path}'. Por favor coloca el archivo CSV en la misma carpeta que app.py"
    )
    st.info(
        "El archivo debe llamarse 'datos.csv' o cambia el nombre en la línea 22 del código"
    )
    st.stop()

df = load_data(csv_path)

# Filtrar datos por origen
df_intermunicipal = df[df["origen_hecho"] == "INTERMUNICIPAL"].copy()
df_intraurbano = df[df["origen_hecho"] == "INTRAURBANO"].copy()

# Título principal
st.title("Análisis de Conflicto Armado - Medellín")
st.markdown("Datos de Desplazamiento y Hechos Victimizantes")
st.markdown("---")

# Sidebar con información general
with st.sidebar:
    st.header("Información del Dataset")

    st.subheader("Totales por Origen")
    st.metric("Intermunicipal (Fuera de Medellín)", f"{len(df_intermunicipal):,}")
    st.metric("Intraurbano (Dentro de Medellín)", f"{len(df_intraurbano):,}")
    st.metric("Total General", f"{len(df):,}")

    st.markdown("---")

    st.subheader("Intermunicipal por Año")
    inter_2024 = len(df_intermunicipal[df_intermunicipal["ano_declara"] == 2024])
    inter_2025 = len(df_intermunicipal[df_intermunicipal["ano_declara"] == 2025])
    st.write(f"**2024:** {inter_2024:,}")
    st.write(f"**2025:** {inter_2025:,}")

    st.markdown("---")

    st.subheader("Intraurbano por Año")
    intra_2024 = len(df_intraurbano[df_intraurbano["ano_declara"] == 2024])
    intra_2025 = len(df_intraurbano[df_intraurbano["ano_declara"] == 2025])
    st.write(f"**2024:** {intra_2024:,}")
    st.write(f"**2025:** {intra_2025:,}")

    st.markdown("---")

    st.subheader("Rango de Fechas")
    st.write(f"**Desde:** {df['fecha_declaracion'].min().strftime('%Y-%m-%d')}")
    st.write(f"**Hasta:** {df['fecha_declaracion'].max().strftime('%Y-%m-%d')}")

# Selector principal de análisis
st.header("Selecciona el tipo de análisis")

tipo_analisis = st.radio(
    "Tipo de Origen:",
    ["INTERMUNICIPAL (Fuera de Medellín)", "INTRAURBANO (Dentro de Medellín)"],
    horizontal=True,
)

# Determinar qué dataset usar
if "INTERMUNICIPAL" in tipo_analisis:
    df_seleccionado = df_intermunicipal.copy()
    tipo_texto = "INTERMUNICIPAL"
    ubicacion_texto = "Municipios fuera de Medellín"
else:
    df_seleccionado = df_intraurbano.copy()
    tipo_texto = "INTRAURBANO"
    ubicacion_texto = "Dentro de Medellín"

st.info(
    f"**Filtro activo:** {tipo_texto} - {ubicacion_texto} | Total registros: {len(df_seleccionado):,}"
)

st.markdown("---")

# Importar páginas
try:
    from pages import datos_generales
    from pages import analisis_municipios
    from pages import hechos_victimizantes
    from pages import analisis_demografico
    from pages import grupos_responsables_todos
    from pages import grupos_responsables_desplazamiento
except ImportError as e:
    st.error(f"Error importando módulos: {e}")
    st.info(
        "Asegúrate de que la carpeta 'pages' existe y contiene todos los archivos .py necesarios"
    )
    st.stop()

# Crear tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    [
        "Datos Generales",
        "Por Municipios/Barrios",
        "Hechos Victimizantes",
        "Análisis Demográfico",
        "Grupos Responsables (Todos)",
        "Grupos (Solo Desplazamiento)",
    ]
)

with tab1:
    datos_generales.render(df_seleccionado, tipo_texto, ubicacion_texto)

with tab2:
    analisis_municipios.render(df_seleccionado, tipo_texto, ubicacion_texto)

with tab3:
    hechos_victimizantes.render(df_seleccionado, tipo_texto, ubicacion_texto)

with tab4:
    analisis_demografico.render(df_seleccionado, tipo_texto, ubicacion_texto)

with tab5:
    grupos_responsables_todos.render(df_seleccionado, tipo_texto, ubicacion_texto)

with tab6:
    grupos_responsables_desplazamiento.render(
        df_seleccionado, tipo_texto, ubicacion_texto
    )

# Footer
st.markdown("---")
st.markdown("### Estadísticas Generales")

col1, col2, col3, col4 = st.columns(4)
with col1:
    if tipo_texto == "INTERMUNICIPAL":
        st.metric("Total Municipios", df_seleccionado["municipio_procede"].nunique())
    else:
        st.metric("Total Barrios", df_seleccionado["barrio_procede"].nunique())
with col2:
    st.metric("Grupos Identificados", df_seleccionado["presunto_responsable"].nunique())
with col3:
    st.metric("Hechos Victimizantes", df_seleccionado["hecho_victimizante"].nunique())
with col4:
    edad_promedio = df_seleccionado[df_seleccionado["edad"].notna()]["edad"].mean()
    st.metric("Edad Promedio", f"{edad_promedio:.1f} años")
