import streamlit as st
import pandas as pd
import os

def load_data():
    """Carga los datos desde el CSV"""
    csv_path = 'datos.csv'
    if not os.path.exists(csv_path):
        st.error(f"No se encontró el archivo '{csv_path}'")
        return None
    
    df = pd.read_csv(csv_path)
    df['fecha_declaracion'] = pd.to_datetime(df['fecha_declaracion'])
    df['ano_declara'] = df['fecha_declaracion'].dt.year
    df['mes_declara'] = df['fecha_declaracion'].dt.month
    return df

def run():
    """Ejecuta el dashboard de hechos victimizantes"""
    st.title("⚠️ Análisis de Hechos Victimizantes")
    st.markdown("Dashboard de todos los hechos victimizantes del conflicto armado")
    
    # Cargar datos
    df = load_data()
    if df is None:
        return
    
    # Filtrar datos
    df_inter = df[df['origen_hecho'] == 'INTERMUNICIPAL'].copy()
    df_intra = df[df['origen_hecho'] == 'INTRAURBANO'].copy()
    
    # Selector de origen
    st.markdown("---")
    tipo_analisis = st.radio(
        "Selecciona el tipo de origen:",
        ["INTERMUNICIPAL (Fuera de Medellín)", "INTRAURBANO (Dentro de Medellín)"],
        horizontal=True
    )
    
    if "INTERMUNICIPAL" in tipo_analisis:
        df_seleccionado = df_inter.copy()
        tipo_texto = "INTERMUNICIPAL"
        ubicacion_texto = "Municipios fuera de Medellín"
    else:
        df_seleccionado = df_intra.copy()
        tipo_texto = "INTRAURBANO"
        ubicacion_texto = "Dentro de Medellín"
    
    st.info(f"**Filtro activo:** {tipo_texto} - {ubicacion_texto} | Total registros: {len(df_seleccionado):,}")
    
    # Importar módulo
    from modules import hechos_victimizantes, grupos_responsables_todos
    
    # Tabs
    tab1, tab2 = st.tabs([
        "Hechos Victimizantes",
        "Grupos Responsables"
    ])
    
    with tab1:
        hechos_victimizantes.render(df_seleccionado, tipo_texto, ubicacion_texto)
    
    with tab2:
        grupos_responsables_todos.render(df_seleccionado, tipo_texto, ubicacion_texto)