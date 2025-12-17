import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from io import BytesIO
import re
from datetime import datetime
import numpy as np


def clean_html_tags(text):
    """Remove HTML tags and entities from text"""
    if pd.isna(text) or text == '':
        return ''
    text = str(text)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove HTML entities
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    # Clean up extra whitespace
    text = ' '.join(text.split())
    return text.strip()


def normalize_crime_type(delito):
    """Normalize and categorize crime types"""
    if pd.isna(delito) or delito == '':
        return 'NO ESPECIFICADO'
    
    delito = str(delito).upper().strip()
    
    # Group similar crimes
    if 'VIOLENCIA INTRAFAMILIAR' in delito or 'VIF' in delito:
        return 'VIOLENCIA INTRAFAMILIAR'
    elif 'HURTO' in delito:
        if 'AGRAVADO' in delito:
            return 'HURTO AGRAVADO'
        elif 'CALIFICADO' in delito:
            return 'HURTO CALIFICADO'
        else:
            return 'HURTO'
    elif 'TRAFICO' in delito or 'ESTUPEFACIENTES' in delito or 'DROGA' in delito:
        return 'TRÁFICO DE ESTUPEFACIENTES'
    elif 'FEMINICIDIO' in delito:
        return 'FEMINICIDIO'
    elif 'ESTAFA' in delito:
        return 'ESTAFA'
    elif 'ABUSO' in delito:
        return 'ABUSO'
    elif 'DOCUMENTO FALSO' in delito or 'FALSEDAD' in delito:
        return 'FALSEDAD EN DOCUMENTO'
    elif 'VIOLENCIA' in delito and 'SERVIDOR' in delito:
        return 'VIOLENCIA CONTRA SERVIDOR PÚBLICO'
    elif 'ABORTO' in delito:
        return 'ABORTO'
    elif 'RECEPTACION' in delito:
        return 'RECEPTACIÓN'
    else:
        return delito


@st.cache_data
def load_data(filepath):
    """Load and process the CSV file with comprehensive data cleaning"""
    try:
        # Try reading with different encodings for deployment compatibility
        try:
            df = pd.read_csv(filepath, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(filepath, encoding='latin-1')
            except Exception:
                df = pd.read_csv(filepath, encoding='utf-8', errors='ignore')
        
        # Clean HTML tags from observaciones
        if 'observaciones' in df.columns:
            df['observaciones_clean'] = df['observaciones'].apply(clean_html_tags)
        
        # Convert fecha_audiencia to datetime
        df['fecha_audiencia'] = pd.to_datetime(df['fecha_audiencia'], errors='coerce')
        
        # Extract temporal features
        df['ano'] = df['fecha_audiencia'].dt.year
        df['mes'] = df['fecha_audiencia'].dt.month
        df['mes_nombre'] = df['fecha_audiencia'].dt.strftime('%Y-%m')
        df['mes_ano'] = df['fecha_audiencia'].dt.to_period('M').astype(str)
        df['trimestre'] = df['fecha_audiencia'].dt.quarter
        df['trimestre_ano'] = df['fecha_audiencia'].dt.to_period('Q').astype(str)
        df['dia_semana'] = df['fecha_audiencia'].dt.day_name()
        df['semana'] = df['fecha_audiencia'].dt.isocalendar().week
        
        # Create hearing type category
        df['tipo_audiencia_categoria'] = df['tipo_proceso'].apply(
            lambda x: 'CONOCIMIENTO' if pd.notna(x) and 'CONOCIMIENTO' in str(x).upper() 
            else ('GARANTÍAS' if pd.notna(x) and 'GARANTÍAS' in str(x).upper() else 'OTRO')
        )
        
        # Normalize crime types
        df['delito_normalizado'] = df['delito'].apply(normalize_crime_type)
        
        # Clean and normalize text fields
        text_cols = ['juzgado', 'clase_audiencia', 'delegado', 'rol', 'nombre_persona', 'sexo', 'pais']
        for col in text_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
                df[col] = df[col].replace('nan', '')
                df[col] = df[col].replace('None', '')
        
        # Handle missing radicado
        df['radicado_clean'] = df['radicado'].fillna('SIN RADICADO')
        
        # Calculate audiencias per radicado
        df['audiencias_por_radicado'] = df.groupby('radicado_clean')['radicado_clean'].transform('count')
        
        # Create active delegate flag
        df['delegado_activo'] = df['delegado'].notna() & (df['delegado'] != '')
        
        return df
    except Exception as e:
        st.error(f"Error técnico al procesar el archivo: {e}")
        return pd.DataFrame()


def export_to_excel(df_dict, filename="reporte_audiencias.xlsx"):
    """Export multiple DataFrames to Excel with multiple sheets"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for sheet_name, df in df_dict.items():
            clean_name = sheet_name[:31] if len(sheet_name) > 31 else sheet_name
            df.to_excel(writer, sheet_name=clean_name, index=False)
    output.seek(0)
    return output.getvalue()


def run(project_info):
    """Main function to run the audiencias analysis project"""
    
    # Configuration - use same pattern as analisis_radicados.py
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Extract filename from archivo_datos path (e.g., "data/informacion-penal.csv" -> "informacion-penal.csv")
    archivo_datos = project_info.get("archivo_datos", "data/informacion-penal.csv")
    filename = os.path.basename(archivo_datos) if "/" in archivo_datos else archivo_datos
    data_path = os.path.join(current_dir, "..", "data", filename)
    
    # Header
    st.title("Análisis Integral de Audiencias y Diligencias")
    st.markdown("### Sistema de seguimiento y análisis de audiencias atendidas por delegados")
    st.markdown("---")
    
    # Load data
    if not os.path.exists(data_path):
        # Try alternative path (direct from root)
        alt_path = archivo_datos
        if os.path.exists(alt_path):
            data_path = alt_path
        else:
            st.error(f"No se encontró el archivo de datos en: {data_path}")
            st.info(f"También se intentó: {alt_path}")
            st.info(f"Directorio actual: {os.getcwd()}")
            return
    
    # Load data with error handling
    try:
        df = load_data(data_path)
    except Exception as e:
        st.error(f"Error al cargar los datos: {str(e)}")
        st.info("Intenta recargar la página o contacta al administrador del sistema.")
        import traceback
        with st.expander("Detalles técnicos del error"):
            st.code(traceback.format_exc())
        return
    
    if df.empty:
        st.warning("El archivo de datos está vacío o tiene un formato no válido.")
        st.info(f"Archivo cargado desde: {data_path}")
        return
    
    # Verify required columns exist
    required_columns = ['fecha_audiencia', 'tipo_proceso', 'delito', 'delegado']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        st.error(f"El archivo de datos no contiene las columnas requeridas: {', '.join(missing_columns)}")
        st.info(f"Columnas disponibles: {', '.join(df.columns.tolist())}")
        return
    
    # FILTROS GLOBALES (Sidebar)
    with st.sidebar:
        st.header("Filtros de Análisis")
        
        # Date range filter
        if df['fecha_audiencia'].notna().any():
            min_date = df['fecha_audiencia'].min().date()
            max_date = df['fecha_audiencia'].max().date()
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
        
        # Delegate filter
        lista_delegados = ["TODOS"] + sorted([
            d for d in df["delegado"].unique().tolist() 
            if pd.notna(d) and d != "" and d != "nan"
        ])
        filtro_delegado = st.selectbox("Delegado", lista_delegados)
        
        # Crime type filter
        lista_delitos = ["TODOS"] + sorted([
            d for d in df["delito_normalizado"].unique().tolist() 
            if pd.notna(d) and d != "" and d != "nan"
        ])
        filtro_delito = st.selectbox("Tipo de Delito", lista_delitos)
        
        # Hearing type filter
        lista_tipos = ["TODOS", "CONOCIMIENTO", "GARANTÍAS"]
        filtro_tipo = st.selectbox("Tipo de Proceso", lista_tipos)
        
        # Court filter
        lista_juzgados = ["TODOS"] + sorted([
            j for j in df["juzgado"].unique().tolist() 
            if pd.notna(j) and j != "" and j != "nan"
        ])
        filtro_juzgado = st.selectbox("Juzgado", lista_juzgados)
        
        # Role filter
        lista_roles = ["TODOS"] + sorted([
            r for r in df["rol"].unique().tolist() 
            if pd.notna(r) and r != "" and r != "nan"
        ])
        filtro_rol = st.selectbox("Rol", lista_roles)
    
    # Apply filters
    df_filtrado = df.copy()
    
    if fecha_inicio and fecha_fin:
        df_filtrado = df_filtrado[
            (df_filtrado['fecha_audiencia'].dt.date >= fecha_inicio) &
            (df_filtrado['fecha_audiencia'].dt.date <= fecha_fin)
        ]
    
    if filtro_delegado != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["delegado"] == filtro_delegado]
    if filtro_delito != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["delito_normalizado"] == filtro_delito]
    if filtro_tipo != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["tipo_audiencia_categoria"] == filtro_tipo]
    if filtro_juzgado != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["juzgado"] == filtro_juzgado]
    if filtro_rol != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["rol"] == filtro_rol]
    
    # KEY PERFORMANCE INDICATORS (KPIs)
    total_audiencias = len(df_filtrado)
    audiencias_conocimiento = len(df_filtrado[df_filtrado['tipo_audiencia_categoria'] == 'CONOCIMIENTO'])
    audiencias_garantias = len(df_filtrado[df_filtrado['tipo_audiencia_categoria'] == 'GARANTÍAS'])
    delegados_activos = df_filtrado['delegado'].nunique()
    delitos_unicos = df_filtrado['delito_normalizado'].nunique()
    juzgados_unicos = df_filtrado['juzgado'].nunique()
    
    # Calculate average hearings per delegate
    if delegados_activos > 0:
        promedio_por_delegado = total_audiencias / delegados_activos
    else:
        promedio_por_delegado = 0
    
    # Temporal coverage
    if df_filtrado['fecha_audiencia'].notna().any():
        fecha_min = df_filtrado['fecha_audiencia'].min().strftime('%Y-%m-%d')
        fecha_max = df_filtrado['fecha_audiencia'].max().strftime('%Y-%m-%d')
    else:
        fecha_min = fecha_max = "N/A"
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    col1.metric("Total Audiencias", f"{total_audiencias:,.0f}")
    col2.metric("Conocimiento", f"{audiencias_conocimiento:,.0f}")
    col3.metric("Control Garantías", f"{audiencias_garantias:,.0f}")
    col4.metric("Delegados Activos", delegados_activos)
    col5.metric("Tipos de Delito", delitos_unicos)
    col6.metric("Promedio/Delegado", f"{promedio_por_delegado:.1f}")
    
    st.markdown("---")
    
    # ANALYSIS TABS
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "Por Tipo de Delito",
        "Conocimiento vs Garantías",
        "Por Delegado",
        "Análisis Temporal",
        "Por Juzgado",
        "Análisis Demográfico",
        "Insights Ejecutivos",
        "Datos Detallados"
    ])
    
    # TAB 1: POR TIPO DE DELITO
    with tab1:
        st.subheader("Análisis por Tipo de Delito")
        st.markdown("Desglose completo de audiencias según el tipo de delito")
        
        # Summary by crime type
        df_delito = df_filtrado.groupby('delito_normalizado').agg({
            'fecha_audiencia': 'count',
            'delegado': 'nunique',
            'juzgado': 'nunique',
            'radicado_clean': 'nunique'
        }).reset_index()
        df_delito.columns = ['Delito', 'Total Audiencias', 'Delegados Únicos', 'Juzgados Únicos', 'Radicados Únicos']
        df_delito = df_delito.sort_values('Total Audiencias', ascending=False)
        
        # Add percentage
        df_delito['Porcentaje'] = (df_delito['Total Audiencias'] / df_delito['Total Audiencias'].sum() * 100).round(2)
        
        st.markdown("#### Resumen por Tipo de Delito")
        st.dataframe(df_delito, use_container_width=True, height=400)
        
        # Visualizations
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### Top 15 Delitos por Volumen")
            fig_delito = px.bar(
                df_delito.head(15),
                x='Total Audiencias',
                y='Delito',
                orientation='h',
                color='Total Audiencias',
                color_continuous_scale='Reds',
                labels={'Total Audiencias': 'Total de Audiencias', 'Delito': 'Tipo de Delito'},
                title="Top 15 Delitos por Volumen de Audiencias"
            )
            fig_delito.update_layout(height=600)
            st.plotly_chart(fig_delito, use_container_width=True)
        
        with col2:
            st.markdown("##### Distribución Porcentual (Top 10)")
            fig_pie = px.pie(
                df_delito.head(10),
                values='Total Audiencias',
                names='Delito',
                title="Distribución de Audiencias - Top 10 Delitos"
            )
            fig_pie.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig_pie, use_container_width=True)
        
        # Crime type by hearing type
        st.markdown("##### Distribución de Delitos: Conocimiento vs Garantías")
        df_delito_tipo = df_filtrado.groupby(['delito_normalizado', 'tipo_audiencia_categoria']).size().reset_index(name='Cantidad')
        df_delito_tipo_pivot = df_delito_tipo.pivot(index='delito_normalizado', columns='tipo_audiencia_categoria', values='Cantidad').fillna(0)
        df_delito_tipo_pivot = df_delito_tipo_pivot.sort_values(by=['CONOCIMIENTO', 'GARANTÍAS'], ascending=False).head(15)
        
        fig_stacked = px.bar(
            df_delito_tipo_pivot.reset_index(),
            x='delito_normalizado',
            y=['CONOCIMIENTO', 'GARANTÍAS'],
            title="Distribución de Delitos por Tipo de Audiencia (Top 15)",
            labels={'value': 'Cantidad', 'delito_normalizado': 'Tipo de Delito', 'variable': 'Tipo de Proceso'},
            color_discrete_map={'CONOCIMIENTO': '#1f77b4', 'GARANTÍAS': '#ff7f0e'}
        )
        fig_stacked.update_layout(barmode='stack', height=500, xaxis_tickangle=-45)
        st.plotly_chart(fig_stacked, use_container_width=True)
    
    # TAB 2: CONOCIMIENTO VS GARANTÍAS
    with tab2:
        st.subheader("Análisis: Audiencias de Conocimiento vs Control de Garantías")
        st.markdown("Comparación detallada entre audiencias de conocimiento y control de garantías")
        
        # Summary comparison
        df_tipo = df_filtrado.groupby('tipo_audiencia_categoria').agg({
            'fecha_audiencia': 'count',
            'delegado': 'nunique',
            'delito_normalizado': 'nunique',
            'juzgado': 'nunique',
            'radicado_clean': 'nunique'
        }).reset_index()
        df_tipo.columns = ['Tipo de Proceso', 'Total Audiencias', 'Delegados Únicos', 'Delitos Únicos', 'Juzgados Únicos', 'Radicados Únicos']
        df_tipo['Porcentaje'] = (df_tipo['Total Audiencias'] / df_tipo['Total Audiencias'].sum() * 100).round(2)
        
        st.markdown("#### Resumen Comparativo")
        st.dataframe(df_tipo, use_container_width=True)
        
        # Visualizations
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### Distribución por Tipo de Proceso")
            fig_pie_tipo = px.pie(
                df_tipo,
                values='Total Audiencias',
                names='Tipo de Proceso',
                title="Distribución de Audiencias por Tipo de Proceso",
                color_discrete_map={'CONOCIMIENTO': '#1f77b4', 'GARANTÍAS': '#ff7f0e'}
            )
            fig_pie_tipo.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig_pie_tipo, use_container_width=True)
        
        with col2:
            st.markdown("##### Comparación de Métricas")
            fig_bar_tipo = px.bar(
                df_tipo,
                x='Tipo de Proceso',
                y=['Total Audiencias', 'Delegados Únicos', 'Delitos Únicos', 'Juzgados Únicos'],
                title="Comparación de Métricas por Tipo de Proceso",
                labels={'value': 'Cantidad', 'variable': 'Métrica'},
                barmode='group'
            )
            st.plotly_chart(fig_bar_tipo, use_container_width=True)
        
        # Temporal comparison
        st.markdown("##### Tendencia Temporal: Conocimiento vs Garantías")
        df_temporal_tipo = df_filtrado.groupby(['mes_ano', 'tipo_audiencia_categoria']).size().reset_index(name='Cantidad')
        df_temporal_tipo_pivot = df_temporal_tipo.pivot(index='mes_ano', columns='tipo_audiencia_categoria', values='Cantidad').fillna(0)
        df_temporal_tipo_pivot = df_temporal_tipo_pivot.sort_index()
        
        fig_line_tipo = go.Figure()
        if 'CONOCIMIENTO' in df_temporal_tipo_pivot.columns:
            fig_line_tipo.add_trace(go.Scatter(
                x=df_temporal_tipo_pivot.index,
                y=df_temporal_tipo_pivot['CONOCIMIENTO'],
                mode='lines+markers',
                name='Conocimiento',
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=8)
            ))
        if 'GARANTÍAS' in df_temporal_tipo_pivot.columns:
            fig_line_tipo.add_trace(go.Scatter(
                x=df_temporal_tipo_pivot.index,
                y=df_temporal_tipo_pivot['GARANTÍAS'],
                mode='lines+markers',
                name='Control de Garantías',
                line=dict(color='#ff7f0e', width=3),
                marker=dict(size=8)
            ))
        fig_line_tipo.update_layout(
            title="Tendencia de Audiencias por Tipo de Proceso",
            xaxis_title="Mes",
            yaxis_title="Cantidad de Audiencias",
            hovermode='x unified',
            height=500
        )
        st.plotly_chart(fig_line_tipo, use_container_width=True)
        
        # Clase de audiencia analysis
        st.markdown("##### Tipos de Audiencia por Proceso")
        df_clase = df_filtrado.groupby(['tipo_audiencia_categoria', 'clase_audiencia']).size().reset_index(name='Cantidad')
        df_clase = df_clase.sort_values('Cantidad', ascending=False).head(20)
        
        fig_clase = px.bar(
            df_clase,
            x='Cantidad',
            y='clase_audiencia',
            color='tipo_audiencia_categoria',
            orientation='h',
            title="Top 20 Tipos de Audiencia por Proceso",
            labels={'Cantidad': 'Cantidad', 'clase_audiencia': 'Clase de Audiencia', 'tipo_audiencia_categoria': 'Tipo de Proceso'},
            color_discrete_map={'CONOCIMIENTO': '#1f77b4', 'GARANTÍAS': '#ff7f0e'}
        )
        fig_clase.update_layout(height=600)
        st.plotly_chart(fig_clase, use_container_width=True)
    
    # TAB 3: POR DELEGADO
    with tab3:
        st.subheader("Análisis por Delegado")
        st.markdown("Análisis de productividad y especialización de cada delegado")
        
        # Summary by delegate
        df_delegado = df_filtrado.groupby('delegado').agg({
            'fecha_audiencia': 'count',
            'delito_normalizado': 'nunique',
            'juzgado': 'nunique',
            'radicado_clean': 'nunique',
            'tipo_audiencia_categoria': lambda x: x.value_counts().to_dict()
        }).reset_index()
        df_delegado.columns = ['Delegado', 'Total Audiencias', 'Delitos Únicos', 'Juzgados Únicos', 'Radicados Únicos', 'Distribucion']
        
        # Calculate conocimiento vs garantias
        df_delegado['Conocimiento'] = df_delegado['Distribucion'].apply(
            lambda x: x.get('CONOCIMIENTO', 0) if isinstance(x, dict) else 0
        )
        df_delegado['Garantías'] = df_delegado['Distribucion'].apply(
            lambda x: x.get('GARANTÍAS', 0) if isinstance(x, dict) else 0
        )
        df_delegado = df_delegado.drop('Distribucion', axis=1)
        df_delegado = df_delegado.sort_values('Total Audiencias', ascending=False)
        
        st.markdown("#### Resumen por Delegado")
        st.dataframe(df_delegado, use_container_width=True, height=400)
        
        # Visualizations
        st.markdown("##### Top 20 Delegados por Productividad")
        fig_delegado = px.bar(
            df_delegado.head(20),
            x='Total Audiencias',
            y='Delegado',
            orientation='h',
            color='Total Audiencias',
            color_continuous_scale='Blues',
            labels={'Total Audiencias': 'Total de Audiencias', 'Delegado': 'Delegado'},
            title="Top 20 Delegados por Volumen de Audiencias"
        )
        fig_delegado.update_layout(height=600)
        st.plotly_chart(fig_delegado, use_container_width=True)
        
        # Scatter plot: Workload vs Specialization
        st.markdown("##### Análisis de Eficiencia: Volumen vs Diversidad")
        df_delegado['Diversidad'] = df_delegado['Delitos Únicos'] / df_delegado['Total Audiencias']
        
        fig_scatter = px.scatter(
            df_delegado,
            x='Total Audiencias',
            y='Diversidad',
            size='Juzgados Únicos',
            color='Delitos Únicos',
            hover_name='Delegado',
            hover_data=['Conocimiento', 'Garantías'],
            labels={
                'Total Audiencias': 'Total de Audiencias',
                'Diversidad': 'Diversidad (Delitos Únicos / Total)',
                'Juzgados Únicos': 'Juzgados Únicos',
                'Delitos Únicos': 'Tipos de Delito'
            },
            title="Matriz de Productividad: Volumen vs Diversidad de Casos",
            color_continuous_scale='Viridis'
        )
        fig_scatter.update_layout(height=500)
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        # Distribution: Conocimiento vs Garantías by delegate
        st.markdown("##### Distribución Conocimiento vs Garantías por Delegado (Top 15)")
        df_delegado_tipo = df_delegado.head(15)[['Delegado', 'Conocimiento', 'Garantías']].melt(
            id_vars='Delegado',
            value_vars=['Conocimiento', 'Garantías'],
            var_name='Tipo',
            value_name='Cantidad'
        )
        
        fig_delegado_tipo = px.bar(
            df_delegado_tipo,
            x='Delegado',
            y='Cantidad',
            color='Tipo',
            title="Distribución de Audiencias por Tipo de Proceso (Top 15 Delegados)",
            labels={'Cantidad': 'Cantidad de Audiencias', 'Delegado': 'Delegado', 'Tipo': 'Tipo de Proceso'},
            color_discrete_map={'Conocimiento': '#1f77b4', 'Garantías': '#ff7f0e'}
        )
        fig_delegado_tipo.update_layout(barmode='stack', height=500, xaxis_tickangle=-45)
        st.plotly_chart(fig_delegado_tipo, use_container_width=True)
    
    # TAB 4: ANÁLISIS TEMPORAL
    with tab4:
        st.subheader("Análisis Temporal")
        st.markdown("Tendencias, patrones y estacionalidad en las audiencias")
        
        # Monthly trends
        st.markdown("#### Tendencias Mensuales")
        df_mes = df_filtrado.groupby('mes_ano').agg({
            'fecha_audiencia': 'count',
            'delegado': 'nunique',
            'delito_normalizado': 'nunique'
        }).reset_index()
        df_mes.columns = ['Mes', 'Total Audiencias', 'Delegados Únicos', 'Delitos Únicos']
        df_mes = df_mes.sort_values('Mes')
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_mes = px.line(
                df_mes,
                x='Mes',
                y='Total Audiencias',
                markers=True,
                title="Tendencia Mensual de Audiencias",
                labels={'Total Audiencias': 'Total de Audiencias', 'Mes': 'Mes'}
            )
            fig_mes.update_layout(height=400)
            st.plotly_chart(fig_mes, use_container_width=True)
        
        with col2:
            fig_mes_delegados = px.line(
                df_mes,
                x='Mes',
                y='Delegados Únicos',
                markers=True,
                title="Delegados Activos por Mes",
                labels={'Delegados Únicos': 'Delegados Únicos', 'Mes': 'Mes'}
            )
            fig_mes_delegados.update_layout(height=400)
            st.plotly_chart(fig_mes_delegados, use_container_width=True)
        
        # Day of week patterns
        st.markdown("#### Patrones por Día de la Semana")
        df_semana = df_filtrado.groupby('dia_semana').agg({
            'fecha_audiencia': 'count',
            'delegado': 'nunique'
        }).reset_index()
        df_semana.columns = ['Día de la Semana', 'Total Audiencias', 'Delegados Únicos']
        orden_dias = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        df_semana['Día de la Semana'] = pd.Categorical(df_semana['Día de la Semana'], categories=orden_dias, ordered=True)
        df_semana = df_semana.sort_values('Día de la Semana')
        
        fig_semana = px.bar(
            df_semana,
            x='Día de la Semana',
            y='Total Audiencias',
            title="Distribución de Audiencias por Día de la Semana",
            labels={'Total Audiencias': 'Total de Audiencias', 'Día de la Semana': 'Día de la Semana'}
        )
        st.plotly_chart(fig_semana, use_container_width=True)
        
        # Quarterly analysis
        st.markdown("#### Análisis Trimestral")
        df_trimestre = df_filtrado.groupby('trimestre_ano').agg({
            'fecha_audiencia': 'count',
            'tipo_audiencia_categoria': lambda x: x.value_counts().to_dict()
        }).reset_index()
        df_trimestre.columns = ['Trimestre', 'Total Audiencias', 'Distribucion']
        df_trimestre['Conocimiento'] = df_trimestre['Distribucion'].apply(
            lambda x: x.get('CONOCIMIENTO', 0) if isinstance(x, dict) else 0
        )
        df_trimestre['Garantías'] = df_trimestre['Distribucion'].apply(
            lambda x: x.get('GARANTÍAS', 0) if isinstance(x, dict) else 0
        )
        df_trimestre = df_trimestre.drop('Distribucion', axis=1)
        df_trimestre = df_trimestre.sort_values('Trimestre')
        
        fig_trimestre = px.bar(
            df_trimestre,
            x='Trimestre',
            y=['Conocimiento', 'Garantías'],
            title="Distribución Trimestral: Conocimiento vs Garantías",
            labels={'value': 'Cantidad', 'variable': 'Tipo de Proceso'},
            color_discrete_map={'Conocimiento': '#1f77b4', 'Garantías': '#ff7f0e'}
        )
        fig_trimestre.update_layout(barmode='stack', height=500, xaxis_tickangle=-45)
        st.plotly_chart(fig_trimestre, use_container_width=True)
    
    # TAB 5: POR JUZGADO
    with tab5:
        st.subheader("Análisis por Juzgado")
        st.markdown("Análisis de audiencias por juzgado")
        
        # Summary by court
        df_juzgado = df_filtrado.groupby('juzgado').agg({
            'fecha_audiencia': 'count',
            'delegado': 'nunique',
            'delito_normalizado': 'nunique',
            'radicado_clean': 'nunique',
            'tipo_audiencia_categoria': lambda x: x.value_counts().to_dict()
        }).reset_index()
        df_juzgado.columns = ['Juzgado', 'Total Audiencias', 'Delegados Únicos', 'Delitos Únicos', 'Radicados Únicos', 'Distribucion']
        
        df_juzgado['Conocimiento'] = df_juzgado['Distribucion'].apply(
            lambda x: x.get('CONOCIMIENTO', 0) if isinstance(x, dict) else 0
        )
        df_juzgado['Garantías'] = df_juzgado['Distribucion'].apply(
            lambda x: x.get('GARANTÍAS', 0) if isinstance(x, dict) else 0
        )
        df_juzgado = df_juzgado.drop('Distribucion', axis=1)
        df_juzgado = df_juzgado.sort_values('Total Audiencias', ascending=False)
        
        st.markdown("#### Resumen por Juzgado")
        st.dataframe(df_juzgado, use_container_width=True, height=400)
        
        # Visualizations
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### Top 20 Juzgados por Volumen")
            fig_juzgado = px.bar(
                df_juzgado.head(20),
                x='Total Audiencias',
                y='Juzgado',
                orientation='h',
                color='Total Audiencias',
                color_continuous_scale='Greens',
                labels={'Total Audiencias': 'Total de Audiencias', 'Juzgado': 'Juzgado'},
                title="Top 20 Juzgados por Volumen de Audiencias"
            )
            fig_juzgado.update_layout(height=600)
            st.plotly_chart(fig_juzgado, use_container_width=True)
        
        with col2:
            st.markdown("##### Distribución Conocimiento vs Garantías (Top 15)")
            df_juzgado_tipo = df_juzgado.head(15)[['Juzgado', 'Conocimiento', 'Garantías']].melt(
                id_vars='Juzgado',
                value_vars=['Conocimiento', 'Garantías'],
                var_name='Tipo',
                value_name='Cantidad'
            )
            
            fig_juzgado_tipo = px.bar(
                df_juzgado_tipo,
                x='Juzgado',
                y='Cantidad',
                color='Tipo',
                title="Distribución por Tipo de Proceso (Top 15 Juzgados)",
                labels={'Cantidad': 'Cantidad de Audiencias', 'Juzgado': 'Juzgado', 'Tipo': 'Tipo de Proceso'},
                color_discrete_map={'Conocimiento': '#1f77b4', 'Garantías': '#ff7f0e'}
            )
            fig_juzgado_tipo.update_layout(barmode='stack', height=600, xaxis_tickangle=-45)
            st.plotly_chart(fig_juzgado_tipo, use_container_width=True)
    
    # TAB 6: ANÁLISIS DEMOGRÁFICO
    with tab6:
        st.subheader("Análisis Demográfico")
        st.markdown("Análisis por género, país y rol")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### Distribución por Género")
            df_sexo = df_filtrado.groupby('sexo').size().reset_index(name='Cantidad')
            df_sexo = df_sexo[df_sexo['sexo'] != '']
            
            fig_sexo = px.pie(
                df_sexo,
                values='Cantidad',
                names='sexo',
                title="Distribución de Audiencias por Género"
            )
            fig_sexo.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig_sexo, use_container_width=True)
        
        with col2:
            st.markdown("##### Distribución por Rol")
            df_rol = df_filtrado.groupby('rol').size().reset_index(name='Cantidad')
            df_rol = df_rol[df_rol['rol'] != '']
            df_rol = df_rol.sort_values('Cantidad', ascending=False).head(10)
            
            fig_rol = px.bar(
                df_rol,
                x='Cantidad',
                y='rol',
                orientation='h',
                title="Top 10 Roles en Audiencias",
                labels={'Cantidad': 'Cantidad', 'rol': 'Rol'}
            )
            st.plotly_chart(fig_rol, use_container_width=True)
        
        st.markdown("##### Distribución por País (Top 15)")
        df_pais = df_filtrado.groupby('pais').size().reset_index(name='Cantidad')
        df_pais = df_pais[df_pais['pais'] != '']
        df_pais = df_pais.sort_values('Cantidad', ascending=False).head(15)
        
        fig_pais = px.bar(
            df_pais,
            x='Cantidad',
            y='pais',
            orientation='h',
            title="Top 15 Países en Audiencias",
            labels={'Cantidad': 'Cantidad', 'pais': 'País'}
        )
        fig_pais.update_layout(height=500)
        st.plotly_chart(fig_pais, use_container_width=True)
        
        # Gender by crime type
        st.markdown("##### Género por Tipo de Delito (Top 10 Delitos)")
        df_sexo_delito = df_filtrado[
            (df_filtrado['sexo'] != '') & 
            (df_filtrado['delito_normalizado'].isin(df_delito.head(10)['Delito'].tolist()))
        ].groupby(['delito_normalizado', 'sexo']).size().reset_index(name='Cantidad')
        
        fig_sexo_delito = px.bar(
            df_sexo_delito,
            x='delito_normalizado',
            y='Cantidad',
            color='sexo',
            title="Distribución de Género por Tipo de Delito (Top 10)",
            labels={'Cantidad': 'Cantidad', 'delito_normalizado': 'Tipo de Delito', 'sexo': 'Género'},
            barmode='group'
        )
        fig_sexo_delito.update_layout(height=500, xaxis_tickangle=-45)
        st.plotly_chart(fig_sexo_delito, use_container_width=True)
    
    # TAB 7: INSIGHTS EJECUTIVOS
    with tab7:
        st.subheader("Insights Ejecutivos")
        st.markdown("Resumen ejecutivo con insights clave y recomendaciones")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Top 10 Delitos")
            st.dataframe(df_delito.head(10)[['Delito', 'Total Audiencias', 'Porcentaje']], use_container_width=True, hide_index=True)
        
        with col2:
            st.markdown("#### Top 10 Delegados")
            st.dataframe(df_delegado.head(10)[['Delegado', 'Total Audiencias', 'Delitos Únicos']], use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # Calculate insights
        mes_max = df_mes.loc[df_mes['Total Audiencias'].idxmax(), 'Mes'] if not df_mes.empty else "N/A"
        mes_max_count = df_mes['Total Audiencias'].max() if not df_mes.empty else 0
        delito_max = df_delito.iloc[0]['Delito'] if not df_delito.empty else "N/A"
        delito_max_count = df_delito.iloc[0]['Total Audiencias'] if not df_delito.empty else 0
        delegado_max = df_delegado.iloc[0]['Delegado'] if not df_delegado.empty else "N/A"
        delegado_max_count = df_delegado.iloc[0]['Total Audiencias'] if not df_delegado.empty else 0
        
        # Calculate trends
        if len(df_mes) >= 2:
            trend = "Aumentando" if df_mes.iloc[-1]['Total Audiencias'] > df_mes.iloc[-2]['Total Audiencias'] else "Disminuyendo"
        else:
            trend = "Datos insuficientes"
        
        # Distribution insights
        pct_conocimiento = (audiencias_conocimiento / total_audiencias * 100) if total_audiencias > 0 else 0
        pct_garantias = (audiencias_garantias / total_audiencias * 100) if total_audiencias > 0 else 0
        
        st.info(f"""
        **Insights Clave del Período Analizado:**
        
        - **Mes con más audiencias:** {mes_max} ({mes_max_count:,} audiencias)
        - **Delito más frecuente:** {delito_max} ({delito_max_count:,} audiencias)
        - **Delegado más activo:** {delegado_max} ({delegado_max_count:,} audiencias)
        - **Tendencia reciente:** {trend}
        - **Distribución:** {pct_conocimiento:.1f}% Conocimiento, {pct_garantias:.1f}% Control de Garantías
        - **Cobertura temporal:** {fecha_min} a {fecha_max}
        - **Promedio de audiencias por delegado:** {promedio_por_delegado:.1f}
        """)
        
        # Recommendations
        st.markdown("#### Recomendaciones")
        
        # Find delegates with high workload
        if not df_delegado.empty:
            workload_threshold = df_delegado['Total Audiencias'].quantile(0.75)
            high_workload = df_delegado[df_delegado['Total Audiencias'] > workload_threshold]
            if not high_workload.empty:
                st.warning(f"**Carga de trabajo alta:** {len(high_workload)} delegados tienen carga superior al percentil 75 ({workload_threshold:.0f} audiencias)")
        
        # Find low diversity crimes
        if not df_delegado.empty:
            low_diversity = df_delegado[df_delegado['Diversidad'] < 0.1]
            if not low_diversity.empty:
                st.info(f"**Especialización:** {len(low_diversity)} delegados muestran alta especialización (diversidad < 0.1)")
    
    # TAB 8: DATOS DETALLADOS
    with tab8:
        st.subheader("Datos Detallados")
        st.markdown("Vista completa de los datos filtrados")
        
        # Prepare display dataframe
        display_cols = ['fecha_audiencia', 'juzgado', 'tipo_proceso', 'clase_audiencia', 
                       'radicado', 'delito', 'delito_normalizado', 'delegado', 'rol', 
                       'nombre_persona', 'sexo', 'pais']
        display_cols = [col for col in display_cols if col in df_filtrado.columns]
        
        st.dataframe(df_filtrado[display_cols], use_container_width=True, height=600)
    
    # EXPORT FUNCTIONALITY
    st.markdown("---")
    st.subheader("Exportar Reportes")
    
    # Prepare export data
    export_data = {}
    
    # Clean columns for export
    cols_to_export = [c for c in df_filtrado.columns if not c.endswith('_num') and c != 'Distribucion']
    export_data["Datos Completos"] = df_filtrado[cols_to_export].copy()
    
    # Add summary sheets
    if not df_delito.empty:
        export_data["Resumen por Delito"] = df_delito.copy()
    if not df_delegado.empty:
        export_data["Resumen por Delegado"] = df_delegado.copy()
    if not df_juzgado.empty:
        export_data["Resumen por Juzgado"] = df_juzgado.copy()
    if not df_tipo.empty:
        export_data["Resumen por Tipo"] = df_tipo.copy()
    if not df_mes.empty:
        export_data["Resumen Mensual"] = df_mes.copy()
    
    # Export button
    excel_data = export_to_excel(export_data, "reporte_audiencias.xlsx")
    
    st.download_button(
        label="Descargar Reporte Completo (Excel)",
        data=excel_data,
        file_name="reporte_audiencias.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

