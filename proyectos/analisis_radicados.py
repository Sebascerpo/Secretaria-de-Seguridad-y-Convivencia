import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from io import BytesIO
from datetime import datetime
import numpy as np


def remove_timezone(series):
    """Remueve timezone de una serie de datetime de forma segura"""
    if series.empty or series.isna().all():
        return series
    try:
        tz_info = series.dt.tz
        if tz_info is not None:
            return series.apply(lambda x: x.replace(tzinfo=None) if pd.notna(x) and hasattr(x, 'tz') and x.tz is not None else x)
        else:
            return series
    except (AttributeError, TypeError, ValueError):
        try:
            return pd.to_datetime(series.astype(str), errors='coerce')
        except:
            return series


@st.cache_data
def load_data(gestion_path, radicados_path):
    """Carga gestion-documental.csv y lo enriquece con radicados.csv usando id_atencion"""
    try:
        # Cargar gestión documental como dataset principal
        df_gestion = pd.read_csv(gestion_path)
        
        # Cargar radicados para enriquecimiento
        df_radicados = pd.read_csv(radicados_path)
        
        # Convertir fechas en gestión documental
        df_gestion['fecha_radicado'] = pd.to_datetime(df_gestion['fecha_radicado'], errors='coerce')
        df_gestion['fecha_radicado'] = remove_timezone(df_gestion['fecha_radicado'])
        
        if 'fecha_atencion' in df_gestion.columns:
            df_gestion['fecha_atencion'] = pd.to_datetime(df_gestion['fecha_atencion'], errors='coerce')
            df_gestion['fecha_atencion'] = remove_timezone(df_gestion['fecha_atencion'])
        
        if 'fecha_cambio_destino' in df_gestion.columns:
            df_gestion['fecha_cambio_destino'] = pd.to_datetime(df_gestion['fecha_cambio_destino'], errors='coerce')
            df_gestion['fecha_cambio_destino'] = remove_timezone(df_gestion['fecha_cambio_destino'])
        
        # Convertir fechas en radicados
        df_radicados['fecha_radicado'] = pd.to_datetime(df_radicados['fecha_radicado'], errors='coerce')
        df_radicados['fecha_radicado'] = remove_timezone(df_radicados['fecha_radicado'])
        
        if 'fecha_atencion' in df_radicados.columns:
            df_radicados['fecha_atencion'] = pd.to_datetime(df_radicados['fecha_atencion'], errors='coerce')
            df_radicados['fecha_atencion'] = remove_timezone(df_radicados['fecha_atencion'])
        
        # Convertir id_atencion a string para hacer el merge
        df_gestion['id_atencion'] = df_gestion['id_atencion'].astype(str)
        df_radicados['id_atencion'] = df_radicados['id_atencion'].astype(str)
        
        # Filtrar valores válidos de id_atencion para el merge
        df_radicados_valid = df_radicados[
            (df_radicados['id_atencion'].notna()) & 
            (df_radicados['id_atencion'] != '') & 
            (df_radicados['id_atencion'] != 'nan') &
            (df_radicados['id_atencion'] != 'None')
        ]
        
        # Hacer left join para enriquecer gestion-documental con datos de radicados
        # Usar sufijos para evitar conflictos de columnas
        df = df_gestion.merge(
            df_radicados_valid[['id_atencion', 'numero_radicado', 'asunto', 'servicio', 'fecha_atencion', 
                               'funcionario_atendio', 'radicador', 'destino']].rename(
                columns={
                    'numero_radicado': 'numero_radicado_rad',
                    'asunto': 'asunto_rad',
                    'servicio': 'servicio_rad',
                    'fecha_atencion': 'fecha_atencion_rad',
                    'funcionario_atendio': 'funcionario_atendio_rad',
                    'radicador': 'radicador_rad',
                    'destino': 'destino_rad'
                }
            ),
            on='id_atencion',
            how='left'
        )
        
        # Extraer componentes temporales
        df['ano'] = df['fecha_radicado'].dt.year
        df['mes'] = df['fecha_radicado'].dt.month
        df['mes_nombre'] = df['fecha_radicado'].dt.strftime('%Y-%m')
        df['mes_ano'] = df['fecha_radicado'].dt.to_period('M').astype(str)
        df['trimestre'] = df['fecha_radicado'].dt.quarter
        df['trimestre_ano'] = df['fecha_radicado'].dt.to_period('Q').astype(str)
        df['dia_semana'] = df['fecha_radicado'].dt.day_name()
        
        # Crear flag de atención
        df['tiene_atencion'] = df['id_atencion'].notna() & (df['id_atencion'] != '') & (df['id_atencion'] != 'nan')
        
        # Calcular tiempo hasta atención (en días)
        df['dias_hasta_atencion'] = None
        mask_atencion = df['tiene_atencion'] & df['fecha_atencion'].notna() & df['fecha_radicado'].notna()
        if mask_atencion.any():
            fecha_atencion = remove_timezone(df.loc[mask_atencion, 'fecha_atencion'])
            fecha_radicado = remove_timezone(df.loc[mask_atencion, 'fecha_radicado'])
            df.loc[mask_atencion, 'dias_hasta_atencion'] = (fecha_atencion - fecha_radicado).dt.days
        
        # Calcular tiempo hasta cambio de destino (en días)
        df['dias_hasta_cambio_destino'] = None
        mask_cambio = df['fecha_cambio_destino'].notna() & df['fecha_radicado'].notna()
        if mask_cambio.any():
            fecha_cambio = remove_timezone(df.loc[mask_cambio, 'fecha_cambio_destino'])
            fecha_radicado_cambio = remove_timezone(df.loc[mask_cambio, 'fecha_radicado'])
            df.loc[mask_cambio, 'dias_hasta_cambio_destino'] = (fecha_cambio - fecha_radicado_cambio).dt.days
        
        # Identificar si hubo cambio de destino
        df['tiene_cambio_destino'] = df['fecha_cambio_destino'].notna()
        
        # Limpiar y normalizar campos de texto
        text_cols = ['funcionario_atendio', 'destino', 'servicio', 'radicador', 'asunto']
        for col in text_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
                df[col] = df[col].replace('nan', '')
                df[col] = df[col].replace('None', '')
                df[col] = df[col].replace('', np.nan)
        
        return df
    except Exception as e:
        st.error(f"Error técnico al procesar los archivos: {e}")
        import traceback
        st.code(traceback.format_exc())
        return pd.DataFrame()


def export_to_excel(df_dict, filename="reporte_gestion_documental.xlsx"):
    """Exporta múltiples DataFrames a un archivo Excel con múltiples hojas"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for sheet_name, df in df_dict.items():
            clean_name = sheet_name[:31] if len(sheet_name) > 31 else sheet_name
            df.to_excel(writer, sheet_name=clean_name, index=False)
    output.seek(0)
    return output.getvalue()


def run(project_info):
    """Función principal para ejecutar el análisis de gestión documental"""
    
    # Configuración de rutas
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Usar archivo_datos del project_info (gestion-documental.csv)
    gestion_path = os.path.join(current_dir, "..", project_info.get("archivo_datos", "data/gestion-documental.csv"))
    radicados_path = os.path.join(current_dir, "..", "data", "radicados.csv")
    
    # Encabezado
    st.title("Análisis de Gestión Documental")
    st.markdown("### Sistema de análisis de flujo y gestión de documentos")
    st.markdown("---")
    
    # Cargar datos
    if not os.path.exists(gestion_path):
        st.error(f"No se encontró el archivo de gestión documental en: {gestion_path}")
        return
    
    if not os.path.exists(radicados_path):
        st.warning(f"No se encontró el archivo de radicados en: {radicados_path}. Continuando sin enriquecimiento.")
        df = pd.read_csv(gestion_path)
    else:
        df = load_data(gestion_path, radicados_path)
    
    if df.empty:
        st.warning("El archivo de datos está vacío o tiene un formato no válido.")
        return
    
    # FILTROS GLOBALES (Sidebar)
    with st.sidebar:
        st.header("Filtros de Análisis")
        
        # Filtro de rango de fechas
        if df['fecha_radicado'].notna().any():
            min_date = df['fecha_radicado'].min().date()
            max_date = df['fecha_radicado'].max().date()
            date_range = st.date_input(
                "Rango de Fechas",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
            if len(date_range) == 2:
                fecha_inicio, fecha_fin = date_range
            else:
                fecha_inicio, fecha_fin = min_date, max_date
        else:
            fecha_inicio, fecha_fin = None, None
        
        # Filtro Destino
        lista_destinos = ["TODOS"] + sorted([
            d for d in df["destino"].unique().tolist() 
            if pd.notna(d) and d != "" and d != "nan"
        ])
        filtro_destino = st.selectbox("Destino", lista_destinos)
        
        # Filtro Radicador
        lista_radicadores = ["TODOS"] + sorted([
            r for r in df["radicador"].unique().tolist() 
            if pd.notna(r) and r != "" and r != "nan"
        ])
        filtro_radicador = st.selectbox("Radicador", lista_radicadores)
        
        # Filtro Funcionario
        lista_funcionarios = ["TODOS"] + sorted([
            f for f in df["funcionario_atendio"].unique().tolist() 
            if pd.notna(f) and f != "" and f != "nan"
        ])
        filtro_funcionario = st.selectbox("Funcionario", lista_funcionarios)
        
        # Filtro Servicio
        lista_servicios = ["TODOS"] + sorted([
            s for s in df["servicio"].unique().tolist() 
            if pd.notna(s) and s != "" and s != "nan"
        ])
        filtro_servicio = st.selectbox("Servicio", lista_servicios)
        
        # Filtro Funcionario (Origen)
        lista_funcionarios_origen = ["TODOS"] + sorted([
            f for f in df["funcionario_atendio"].unique().tolist() 
            if pd.notna(f) and f != "" and f != "nan"
        ])
        filtro_funcionario_origen = st.selectbox("Funcionario (Origen)", lista_funcionarios_origen)
        
        # Filtro Cambio de Destino
        filtro_cambio = st.selectbox(
            "Cambio de Destino",
            ["TODOS", "Con Cambio", "Sin Cambio"]
        )
    
    # Aplicar filtros
    df_filtrado = df.copy()
    
    if fecha_inicio and fecha_fin:
        df_filtrado = df_filtrado[
            (df_filtrado['fecha_radicado'].dt.date >= fecha_inicio) &
            (df_filtrado['fecha_radicado'].dt.date <= fecha_fin)
        ]
    
    if filtro_destino != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["destino"] == filtro_destino]
    if filtro_radicador != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["radicador"] == filtro_radicador]
    if filtro_funcionario != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["funcionario_atendio"] == filtro_funcionario]
    if filtro_servicio != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["servicio"] == filtro_servicio]
    if filtro_funcionario_origen != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["funcionario_atendio"] == filtro_funcionario_origen]
    if filtro_cambio == "Con Cambio":
        df_filtrado = df_filtrado[df_filtrado["tiene_cambio_destino"] == True]
    elif filtro_cambio == "Sin Cambio":
        df_filtrado = df_filtrado[df_filtrado["tiene_cambio_destino"] == False]
    
    # INDICADORES CLAVE (KPIs)
    total_documentos = len(df_filtrado)
    documentos_con_atencion = df_filtrado['tiene_atencion'].sum()
    documentos_con_cambio = df_filtrado['tiene_cambio_destino'].sum()
    destinos_unicos = df_filtrado['destino'].nunique()
    radicadores_unicos = df_filtrado['radicador'].nunique()
    funcionarios_unicos = df_filtrado['funcionario_atendio'].nunique()
    
    # Tiempo promedio hasta atención
    tiempo_promedio_atencion = df_filtrado['dias_hasta_atencion'].mean() if df_filtrado['dias_hasta_atencion'].notna().any() else 0
    tiempo_promedio_cambio = df_filtrado['dias_hasta_cambio_destino'].mean() if df_filtrado['dias_hasta_cambio_destino'].notna().any() else 0
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    col1.metric("Total Documentos", f"{total_documentos:,.0f}")
    col2.metric("Con Atención", f"{documentos_con_atencion:,.0f}")
    col3.metric("Con Cambio Destino", f"{documentos_con_cambio:,.0f}")
    col4.metric("Destinos Únicos", destinos_unicos)
    col5.metric("Tiempo Prom. Atención", f"{tiempo_promedio_atencion:.1f} días")
    col6.metric("Tiempo Prom. Cambio", f"{tiempo_promedio_cambio:.1f} días")
    
    st.markdown("---")
    
    # ANÁLISIS CON PESTAÑAS
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "Resumen Ejecutivo",
        "Flujo de Documentos",
        "Análisis por Destino",
        "Análisis por Radicador",
        "Análisis por Funcionario",
        "Análisis de Servicios",
        "Métricas de Tiempo"
    ])
    
    # TAB 1: RESUMEN EJECUTIVO
    with tab1:
        st.subheader("Resumen Ejecutivo")
        st.markdown("Indicadores clave y métricas principales de gestión documental")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Top 10 Destinos")
            df_destino_summary = df_filtrado.groupby('destino').size().reset_index(name='Total')
            df_destino_summary = df_destino_summary.sort_values('Total', ascending=False).head(10)
            df_destino_summary.columns = ['Destino', 'Total Documentos']
            st.dataframe(df_destino_summary, use_container_width=True, hide_index=True)
        
        with col2:
            st.markdown("#### Top 10 Radicadores")
            df_radicador_summary = df_filtrado.groupby('radicador').size().reset_index(name='Total')
            df_radicador_summary = df_radicador_summary.sort_values('Total', ascending=False).head(10)
            df_radicador_summary.columns = ['Radicador', 'Total Documentos']
            st.dataframe(df_radicador_summary, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        col3, col4 = st.columns(2)
        
        with col3:
            st.markdown("#### Top 10 Funcionarios")
            df_funcionario_summary = df_filtrado.groupby('funcionario_atendio').size().reset_index(name='Total')
            df_funcionario_summary = df_funcionario_summary.sort_values('Total', ascending=False).head(10)
            df_funcionario_summary.columns = ['Funcionario', 'Total Documentos']
            st.dataframe(df_funcionario_summary, use_container_width=True, hide_index=True)
        
        with col4:
            st.markdown("#### Top 10 Servicios")
            df_servicio_summary = df_filtrado.groupby('servicio').size().reset_index(name='Total')
            df_servicio_summary = df_servicio_summary.sort_values('Total', ascending=False).head(10)
            df_servicio_summary.columns = ['Servicio', 'Total Documentos']
            st.dataframe(df_servicio_summary, use_container_width=True, hide_index=True)
        
        # Insights
        st.markdown("---")
        st.markdown("#### Insights Clave")
        
        mes_max = df_filtrado.groupby('mes_ano').size().idxmax() if not df_filtrado.empty else "N/A"
        mes_max_count = df_filtrado.groupby('mes_ano').size().max() if not df_filtrado.empty else 0
        destino_max = df_filtrado.groupby('destino').size().idxmax() if not df_filtrado.empty else "N/A"
        destino_max_count = df_filtrado.groupby('destino').size().max() if not df_filtrado.empty else 0
        
        tasa_atencion = (documentos_con_atencion / total_documentos * 100) if total_documentos > 0 else 0
        tasa_cambio = (documentos_con_cambio / total_documentos * 100) if total_documentos > 0 else 0
        
        st.info(f"""
        **Resumen del Período Analizado:**
        
        - **Mes con más documentos:** {mes_max} ({mes_max_count:,} documentos)
        - **Destino principal:** {destino_max} ({destino_max_count:,} documentos)
        - **Tasa de atención:** {tasa_atencion:.1f}%
        - **Tasa de cambio de destino:** {tasa_cambio:.1f}%
        - **Tiempo promedio hasta atención:** {tiempo_promedio_atencion:.1f} días
        - **Tiempo promedio hasta cambio:** {tiempo_promedio_cambio:.1f} días
        """)
    
    # TAB 2: FLUJO DE DOCUMENTOS
    with tab2:
        st.subheader("Flujo de Documentos")
        st.markdown("Análisis de patrones de enrutamiento y flujo de documentos")
        
        # Flujo Funcionario -> Destino
        st.markdown("#### Flujo: Funcionario → Destino (Top 20 combinaciones)")
        df_flujo = df_filtrado.groupby(['funcionario_atendio', 'destino']).size().reset_index(name='Cantidad')
        df_flujo = df_flujo.sort_values('Cantidad', ascending=False).head(20)
        df_flujo.columns = ['Funcionario', 'Destino', 'Cantidad de Documentos']
        st.dataframe(df_flujo, use_container_width=True)
        
        # Distribución por funcionario
        st.markdown("#### Distribución por Funcionario")
        df_funcionario_dist = df_filtrado.groupby('funcionario_atendio').size().reset_index(name='Total')
        df_funcionario_dist = df_funcionario_dist.sort_values('Total', ascending=False).head(15)
        
        fig_funcionario = px.bar(
            df_funcionario_dist,
            x='Total',
            y='funcionario_atendio',
            orientation='h',
            title="Top 15 Funcionarios por Volumen",
            labels={'Total': 'Total de Documentos', 'funcionario_atendio': 'Funcionario'}
        )
        fig_funcionario.update_layout(height=500)
        st.plotly_chart(fig_funcionario, use_container_width=True)
    
    # TAB 3: ANÁLISIS POR DESTINO
    with tab3:
        st.subheader("Análisis por Destino")
        st.markdown("Análisis detallado de documentos por destino")
        
        # Resumen por destino
        df_destino = df_filtrado.groupby('destino').agg({
            'numero_radicado': 'count',
            'tiene_atencion': 'sum',
            'tiene_cambio_destino': 'sum',
            'dias_hasta_atencion': 'mean',
            'radicador': 'nunique',
            'funcionario_atendio': 'nunique'
        }).reset_index()
        df_destino.columns = ['Destino', 'Total Documentos', 'Con Atención', 'Con Cambio', 
                             'Días Prom. Atención', 'Radicadores Únicos', 'Funcionarios Únicos']
        df_destino['Días Prom. Atención'] = df_destino['Días Prom. Atención'].round(1)
        df_destino = df_destino.sort_values('Total Documentos', ascending=False)
        
        st.markdown("#### Resumen por Destino")
        st.dataframe(df_destino, use_container_width=True, height=400)
        
        # Visualizaciones
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### Top 15 Destinos por Volumen")
            fig_destino = px.bar(
                df_destino.head(15),
                x='Total Documentos',
                y='Destino',
                orientation='h',
                color='Total Documentos',
                color_continuous_scale='Blues',
                title="Top 15 Destinos por Volumen"
            )
            fig_destino.update_layout(height=600)
            st.plotly_chart(fig_destino, use_container_width=True)
        
        with col2:
            st.markdown("##### Distribución Porcentual (Top 10)")
            fig_pie_destino = px.pie(
                df_destino.head(10),
                values='Total Documentos',
                names='Destino',
                title="Distribución de Documentos - Top 10 Destinos"
            )
            fig_pie_destino.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig_pie_destino, use_container_width=True)
    
    # TAB 4: ANÁLISIS POR RADICADOR
    with tab4:
        st.subheader("Análisis por Radicador")
        st.markdown("Análisis de quién crea los documentos y sus patrones")
        
        # Resumen por radicador
        df_radicador = df_filtrado.groupby('radicador').agg({
            'numero_radicado': 'count',
            'destino': 'nunique',
            'servicio': 'nunique',
            'tiene_atencion': 'sum'
        }).reset_index()
        df_radicador.columns = ['Radicador', 'Total Documentos', 'Destinos Únicos', 
                               'Servicios Únicos', 'Con Atención']
        df_radicador['Tasa Atención (%)'] = (df_radicador['Con Atención'] / df_radicador['Total Documentos'] * 100).round(2)
        df_radicador = df_radicador.sort_values('Total Documentos', ascending=False)
        
        st.markdown("#### Resumen por Radicador")
        st.dataframe(df_radicador, use_container_width=True, height=400)
        
        # Visualización
        st.markdown("##### Top 20 Radicadores por Productividad")
        fig_radicador = px.bar(
            df_radicador.head(20),
            x='Total Documentos',
            y='Radicador',
            orientation='h',
            color='Tasa Atención (%)',
            color_continuous_scale='Greens',
            title="Top 20 Radicadores por Volumen"
        )
        fig_radicador.update_layout(height=600)
        st.plotly_chart(fig_radicador, use_container_width=True)
    
    # TAB 5: ANÁLISIS POR FUNCIONARIO
    with tab5:
        st.subheader("Análisis por Funcionario")
        st.markdown("Análisis de quién procesa los documentos y su eficiencia")
        
        # Resumen por funcionario
        df_funcionario = df_filtrado.groupby('funcionario_atendio').agg({
            'numero_radicado': 'count',
            'destino': 'nunique',
            'servicio': 'nunique',
            'dias_hasta_atencion': 'mean'
        }).reset_index()
        df_funcionario.columns = ['Funcionario', 'Total Documentos', 'Destinos Únicos', 
                                  'Servicios Únicos', 'Días Prom. Atención']
        df_funcionario['Días Prom. Atención'] = df_funcionario['Días Prom. Atención'].round(1)
        df_funcionario = df_funcionario.sort_values('Total Documentos', ascending=False)
        
        st.markdown("#### Resumen por Funcionario")
        st.dataframe(df_funcionario, use_container_width=True, height=400)
        
        # Visualización
        st.markdown("##### Top 20 Funcionarios por Volumen")
        fig_funcionario = px.bar(
            df_funcionario.head(20),
            x='Total Documentos',
            y='Funcionario',
            orientation='h',
            color='Días Prom. Atención',
            color_continuous_scale='Reds',
            title="Top 20 Funcionarios por Volumen"
        )
        fig_funcionario.update_layout(height=600)
        st.plotly_chart(fig_funcionario, use_container_width=True)
        
        # Análisis de eficiencia
        st.markdown("##### Análisis de Eficiencia: Volumen vs Tiempo")
        df_funcionario_eff = df_funcionario[df_funcionario['Días Prom. Atención'].notna()]
        if not df_funcionario_eff.empty:
            fig_scatter = px.scatter(
                df_funcionario_eff,
                x='Total Documentos',
                y='Días Prom. Atención',
                size='Destinos Únicos',
                hover_name='Funcionario',
                title="Eficiencia: Volumen vs Tiempo de Atención",
                labels={
                    'Total Documentos': 'Total de Documentos',
                    'Días Prom. Atención': 'Días Promedio hasta Atención',
                    'Destinos Únicos': 'Destinos Únicos'
                }
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
    
    # TAB 6: ANÁLISIS DE SERVICIOS
    with tab6:
        st.subheader("Análisis de Servicios")
        st.markdown("Análisis de tipos de servicio y sus patrones de enrutamiento")
        
        # Resumen por servicio
        df_servicio = df_filtrado.groupby('servicio').agg({
            'numero_radicado': 'count',
            'destino': 'nunique',
            'tiene_atencion': 'sum',
            'dias_hasta_atencion': 'mean'
        }).reset_index()
        df_servicio.columns = ['Servicio', 'Total Documentos', 'Destinos Únicos', 
                              'Con Atención', 'Días Prom. Atención']
        df_servicio['Días Prom. Atención'] = df_servicio['Días Prom. Atención'].round(1)
        df_servicio = df_servicio.sort_values('Total Documentos', ascending=False)
        
        st.markdown("#### Resumen por Servicio")
        st.dataframe(df_servicio, use_container_width=True, height=400)
        
        # Visualizaciones
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### Top 15 Servicios por Volumen")
            fig_servicio = px.bar(
                df_servicio.head(15),
                x='Total Documentos',
                y='Servicio',
                orientation='h',
                color='Total Documentos',
                color_continuous_scale='Purples',
                title="Top 15 Servicios por Volumen"
            )
            fig_servicio.update_layout(height=600)
            st.plotly_chart(fig_servicio, use_container_width=True)
        
        with col2:
            st.markdown("##### Distribución Porcentual (Top 10)")
            fig_pie_servicio = px.pie(
                df_servicio.head(10),
                values='Total Documentos',
                names='Servicio',
                title="Distribución de Documentos - Top 10 Servicios"
            )
            fig_pie_servicio.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig_pie_servicio, use_container_width=True)
        
        # Servicios por destino
        st.markdown("##### Servicios por Destino (Top 20 combinaciones)")
        df_serv_dest = df_filtrado.groupby(['servicio', 'destino']).size().reset_index(name='Cantidad')
        df_serv_dest = df_serv_dest.sort_values('Cantidad', ascending=False).head(20)
        df_serv_dest.columns = ['Servicio', 'Destino', 'Cantidad de Documentos']
        st.dataframe(df_serv_dest, use_container_width=True)
    
    # TAB 7: MÉTRICAS DE TIEMPO
    with tab7:
        st.subheader("Métricas de Tiempo")
        st.markdown("Análisis de tiempos de procesamiento y tendencias")
        
        # Tendencias mensuales
        st.markdown("#### Tendencias Mensuales")
        df_mes = df_filtrado.groupby('mes_ano').agg({
            'numero_radicado': 'count',
            'dias_hasta_atencion': 'mean',
            'dias_hasta_cambio_destino': 'mean'
        }).reset_index()
        df_mes.columns = ['Mes', 'Total Documentos', 'Días Prom. Atención', 'Días Prom. Cambio']
        df_mes['Días Prom. Atención'] = df_mes['Días Prom. Atención'].round(1)
        df_mes['Días Prom. Cambio'] = df_mes['Días Prom. Cambio'].round(1)
        df_mes = df_mes.sort_values('Mes')
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_mes_vol = px.line(
                df_mes,
                x='Mes',
                y='Total Documentos',
                markers=True,
                title="Tendencia Mensual de Documentos",
                labels={'Total Documentos': 'Total de Documentos', 'Mes': 'Mes'}
            )
            st.plotly_chart(fig_mes_vol, use_container_width=True)
        
        with col2:
            fig_mes_tiempo = px.line(
                df_mes[df_mes['Días Prom. Atención'].notna()],
                x='Mes',
                y='Días Prom. Atención',
                markers=True,
                title="Tiempo Promedio hasta Atención por Mes",
                labels={'Días Prom. Atención': 'Días', 'Mes': 'Mes'}
            )
            st.plotly_chart(fig_mes_tiempo, use_container_width=True)
        
        # Tiempos por destino
        st.markdown("#### Tiempo Promedio por Destino (Top 15)")
        df_tiempo_dest = df_filtrado.groupby('destino').agg({
            'dias_hasta_atencion': 'mean'
        }).reset_index()
        df_tiempo_dest.columns = ['Destino', 'Días Promedio']
        df_tiempo_dest = df_tiempo_dest[df_tiempo_dest['Días Promedio'].notna()]
        df_tiempo_dest = df_tiempo_dest.sort_values('Días Promedio', ascending=False).head(15)
        
        fig_tiempo_dest = px.bar(
            df_tiempo_dest,
            x='Días Promedio',
            y='Destino',
            orientation='h',
            title="Tiempo Promedio hasta Atención por Destino",
            labels={'Días Promedio': 'Días', 'Destino': 'Destino'}
        )
        st.plotly_chart(fig_tiempo_dest, use_container_width=True)
    
    # EXPORTACIÓN
    st.markdown("---")
    st.subheader("Exportar Reportes")
    
    # Preparar datos para exportación
    export_data = {}
    
    # Datos completos
    cols_to_export = [c for c in df_filtrado.columns if not c.endswith('_rad')]
    export_data["Datos Completos"] = df_filtrado[cols_to_export].copy()
    
    # Agregar hojas de resumen
    if not df_destino.empty:
        export_data["Resumen por Destino"] = df_destino.copy()
    if not df_radicador.empty:
        export_data["Resumen por Radicador"] = df_radicador.copy()
    if not df_funcionario.empty:
        export_data["Resumen por Funcionario"] = df_funcionario.copy()
    if not df_servicio.empty:
        export_data["Resumen por Servicio"] = df_servicio.copy()
    if not df_flujo.empty:
        export_data["Flujo Funcionario-Destino"] = df_flujo.copy()
    
    # Botón de descarga
    excel_data = export_to_excel(export_data, "reporte_gestion_documental.xlsx")
    
    st.download_button(
        label="Descargar Reporte Completo (Excel)",
        data=excel_data,
        file_name="reporte_gestion_documental.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
