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
def load_data(filepath):
    """Carga y procesa el CSV de conciliación"""
    try:
        df = pd.read_csv(filepath)
        
        # Convertir fechas
        date_cols = ['fecha_estado_negocio', 'fecha_inicio_evento', 'fecha_fin_evento', 'fecha_inicio', 'fecha_entrega_auxiliar']
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
                df[col] = remove_timezone(df[col])
        
        # Extraer componentes temporales de fecha_inicio (fecha principal del caso)
        if 'fecha_inicio' in df.columns:
            df['ano'] = df['fecha_inicio'].dt.year
            df['mes'] = df['fecha_inicio'].dt.month
            df['mes_ano'] = df['fecha_inicio'].dt.to_period('M').astype(str)
            df['trimestre'] = df['fecha_inicio'].dt.quarter
            df['trimestre_ano'] = df['fecha_inicio'].dt.to_period('Q').astype(str)
        
        # Crear flags de éxito - mejor detección de resultados
        df['tiene_acuerdo'] = df['evento'].str.contains('ACUERDO CONCILIATORIO', case=False, na=False)
        df['tiene_no_acuerdo'] = (
            df['evento'].str.contains('NO ACUERDO', case=False, na=False) |
            df['evento'].str.contains('SIN ANIMO CONCILIATORIO', case=False, na=False)
        )
        df['tiene_inasistencia'] = (
            df['evento'].str.contains('INASISTENCIA', case=False, na=False) |
            df['evento'].str.contains('ACTA NO REALIZACIÓN', case=False, na=False) |
            df['evento'].str.contains('CONTANCIA DE NO REALIZACION', case=False, na=False) |
            df['evento'].str.contains('NO SE PRESENTAN', case=False, na=False)
        )
        df['tiene_retiro'] = df['evento'].str.contains('RETIRO', case=False, na=False)
        
        # Calcular tiempo de procesamiento (fecha_inicio_evento - fecha_inicio)
        df['dias_procesamiento'] = None
        mask_tiempo = df['fecha_inicio_evento'].notna() & df['fecha_inicio'].notna()
        if mask_tiempo.any():
            fecha_inicio_evento = remove_timezone(df.loc[mask_tiempo, 'fecha_inicio_evento'])
            fecha_inicio = remove_timezone(df.loc[mask_tiempo, 'fecha_inicio'])
            df.loc[mask_tiempo, 'dias_procesamiento'] = (fecha_inicio_evento - fecha_inicio).dt.days
        
        # Calcular tiempo hasta finalización (fecha_fin_evento - fecha_inicio_evento)
        df['dias_duracion_evento'] = None
        mask_duracion = df['fecha_fin_evento'].notna() & df['fecha_inicio_evento'].notna()
        if mask_duracion.any():
            fecha_fin = remove_timezone(df.loc[mask_duracion, 'fecha_fin_evento'])
            fecha_inicio_evt = remove_timezone(df.loc[mask_duracion, 'fecha_inicio_evento'])
            df.loc[mask_duracion, 'dias_duracion_evento'] = (fecha_fin - fecha_inicio_evt).dt.days
        
        # Limpiar campos de texto
        text_cols = ['responsable', 'estado', 'estado_negocio', 'estado_evento', 'evento', 'servicio']
        for col in text_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
                df[col] = df[col].replace('nan', '')
                df[col] = df[col].replace('None', '')
        
        return df
    except Exception as e:
        st.error(f"Error técnico al procesar el archivo: {e}")
        import traceback
        st.code(traceback.format_exc())
        return pd.DataFrame()


def export_to_excel(df_dict, filename="reporte_conciliacion.xlsx"):
    """Exporta múltiples DataFrames a un archivo Excel con múltiples hojas"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for sheet_name, df in df_dict.items():
            clean_name = sheet_name[:31] if len(sheet_name) > 31 else sheet_name
            df.to_excel(writer, sheet_name=clean_name, index=False)
    output.seek(0)
    return output.getvalue()


def run(project_info):
    """Función principal para ejecutar el análisis de conciliación"""
    
    # Configuración de rutas
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(current_dir, "..", project_info.get("archivo_datos", "data/conciliacion.csv"))
    
    # Encabezado
    st.title("Análisis de Conciliación")
    st.markdown("### Sistema de análisis de procesos de conciliación extrajudicial")
    st.markdown("---")
    
    # Cargar datos
    if not os.path.exists(data_path):
        st.error(f"No se encontró el archivo de datos en: {data_path}")
        return
    
    df = load_data(data_path)
    
    if df.empty:
        st.warning("El archivo de datos está vacío o tiene un formato no válido.")
        return
    
    # FILTROS GLOBALES (Sidebar)
    with st.sidebar:
        st.header("Filtros de Análisis")
        
        # Filtro de rango de fechas
        if 'fecha_inicio' in df.columns and df['fecha_inicio'].notna().any():
            min_date = df['fecha_inicio'].min().date()
            max_date = df['fecha_inicio'].max().date()
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
        
        # Filtro Responsable
        lista_responsables = ["TODOS"] + sorted([
            r for r in df["responsable"].unique().tolist() 
            if pd.notna(r) and r != "" and r != "nan"
        ])
        filtro_responsable = st.selectbox("Responsable", lista_responsables)
        
        # Filtro Estado
        lista_estados = ["TODOS"] + sorted([
            e for e in df["estado"].unique().tolist() 
            if pd.notna(e) and e != "" and e != "nan"
        ])
        filtro_estado = st.selectbox("Estado", lista_estados)
        
        # Filtro Estado Negocio
        lista_estados_negocio = ["TODOS"] + sorted([
            e for e in df["estado_negocio"].unique().tolist() 
            if pd.notna(e) and e != "" and e != "nan"
        ])
        filtro_estado_negocio = st.selectbox("Estado Negocio", lista_estados_negocio)
        
        # Filtro Evento
        lista_eventos = ["TODOS"] + sorted([
            e for e in df["evento"].unique().tolist() 
            if pd.notna(e) and e != "" and e != "nan"
        ])
        filtro_evento = st.selectbox("Evento", lista_eventos)
    
    # Aplicar filtros
    df_filtrado = df.copy()
    
    if fecha_inicio and fecha_fin and 'fecha_inicio' in df_filtrado.columns:
        df_filtrado = df_filtrado[
            (df_filtrado['fecha_inicio'].dt.date >= fecha_inicio) &
            (df_filtrado['fecha_inicio'].dt.date <= fecha_fin)
        ]
    
    if filtro_responsable != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["responsable"] == filtro_responsable]
    if filtro_estado != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["estado"] == filtro_estado]
    if filtro_estado_negocio != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["estado_negocio"] == filtro_estado_negocio]
    if filtro_evento != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["evento"] == filtro_evento]
    
    # INDICADORES CLAVE (KPIs)
    total_eventos = len(df_filtrado)
    total_casos_unicos = df_filtrado['id_caso'].nunique() if 'id_caso' in df_filtrado.columns else 0
    
    # Contar acuerdos, no acuerdos, inasistencias (a nivel de caso único)
    df_casos = df_filtrado.groupby('id_caso').agg({
        'tiene_acuerdo': 'any',
        'tiene_no_acuerdo': 'any',
        'tiene_inasistencia': 'any',
        'tiene_retiro': 'any'
    }).reset_index()
    
    casos_con_acuerdo = df_casos['tiene_acuerdo'].sum()
    casos_sin_acuerdo = df_casos['tiene_no_acuerdo'].sum()
    casos_inasistencia = df_casos['tiene_inasistencia'].sum()
    casos_retirados = df_casos['tiene_retiro'].sum()
    
    tasa_acuerdos = (casos_con_acuerdo / total_casos_unicos * 100) if total_casos_unicos > 0 else 0
    responsables_unicos = df_filtrado['responsable'].nunique()
    
    # Tiempo promedio de procesamiento
    tiempo_promedio = df_filtrado['dias_procesamiento'].mean() if df_filtrado['dias_procesamiento'].notna().any() else 0
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    col1.metric("Total Eventos", f"{total_eventos:,.0f}")
    col2.metric("Casos Únicos", f"{total_casos_unicos:,.0f}")
    col3.metric("Con Acuerdo", f"{casos_con_acuerdo:,.0f}")
    col4.metric("Tasa Acuerdos", f"{tasa_acuerdos:.1f}%")
    col5.metric("Tiempo Promedio", f"{tiempo_promedio:.1f} días")
    
    st.markdown("---")
    
    # ANÁLISIS CON PESTAÑAS
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Resumen Ejecutivo",
        "Tasa de Éxito",
        "Por Responsable",
        "Análisis Temporal",
        "Eventos y Estados"
    ])
    
    # TAB 1: RESUMEN EJECUTIVO
    with tab1:
        st.subheader("Resumen Ejecutivo")
        st.markdown("Indicadores clave y métricas principales de conciliación")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Top 10 Responsables")
            df_responsable_summary = df_filtrado.groupby('responsable').agg({
                'id_caso': 'nunique',
                'tiene_acuerdo': 'sum'
            }).reset_index()
            df_responsable_summary.columns = ['Responsable', 'Total Casos', 'Eventos con Acuerdo']
            df_responsable_summary = df_responsable_summary.sort_values('Total Casos', ascending=False).head(10)
            st.dataframe(df_responsable_summary, use_container_width=True, hide_index=True)
        
        with col2:
            st.markdown("#### Top 10 Eventos")
            df_evento_summary = df_filtrado.groupby('evento').size().reset_index(name='Total')
            df_evento_summary = df_evento_summary.sort_values('Total', ascending=False).head(10)
            df_evento_summary.columns = ['Evento', 'Total Ocurrencias']
            st.dataframe(df_evento_summary, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # Resumen de estados
        col3, col4 = st.columns(2)
        
        with col3:
            st.markdown("#### Distribución por Estado")
            df_estado_summary = df_filtrado.groupby('estado').size().reset_index(name='Total')
            df_estado_summary = df_estado_summary.sort_values('Total', ascending=False)
            fig_estado = px.pie(
                df_estado_summary,
                values='Total',
                names='estado',
                title="Distribución de Eventos por Estado"
            )
            fig_estado.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig_estado, use_container_width=True)
        
        with col4:
            st.markdown("#### Distribución por Estado Negocio")
            df_estado_negocio_summary = df_filtrado.groupby('estado_negocio').size().reset_index(name='Total')
            df_estado_negocio_summary = df_estado_negocio_summary.sort_values('Total', ascending=False)
            fig_estado_negocio = px.pie(
                df_estado_negocio_summary,
                values='Total',
                names='estado_negocio',
                title="Distribución por Estado de Negocio"
            )
            fig_estado_negocio.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig_estado_negocio, use_container_width=True)
        
        # Insights
        st.markdown("---")
        st.markdown("#### Insights Clave")
        
        mes_max = df_filtrado.groupby('mes_ano').size().idxmax() if 'mes_ano' in df_filtrado.columns and not df_filtrado.empty else "N/A"
        mes_max_count = df_filtrado.groupby('mes_ano').size().max() if 'mes_ano' in df_filtrado.columns and not df_filtrado.empty else 0
        responsable_max = df_filtrado.groupby('responsable').size().idxmax() if not df_filtrado.empty else "N/A"
        responsable_max_count = df_filtrado.groupby('responsable').size().max() if not df_filtrado.empty else 0
        
        st.info(f"""
        **Resumen del Período Analizado:**
        
        - **Mes con más eventos:** {mes_max} ({mes_max_count:,} eventos)
        - **Responsable más activo:** {responsable_max} ({responsable_max_count:,} eventos)
        - **Tasa de acuerdos:** {tasa_acuerdos:.1f}%
        - **Casos con acuerdo:** {casos_con_acuerdo:,} de {total_casos_unicos:,}
        - **Casos sin acuerdo:** {casos_sin_acuerdo:,}
        - **Casos con inasistencia:** {casos_inasistencia:,}
        - **Tiempo promedio de procesamiento:** {tiempo_promedio:.1f} días
        """)
    
    # TAB 2: TASA DE ÉXITO
    with tab2:
        st.subheader("Análisis de Tasa de Éxito")
        st.markdown("Análisis detallado de acuerdos conciliatorios vs no acuerdos")
        
        # Resumen por caso
        df_casos_detalle = df_filtrado.groupby('id_caso').agg({
            'tiene_acuerdo': 'any',
            'tiene_no_acuerdo': 'any',
            'tiene_inasistencia': 'any',
            'dias_procesamiento': 'mean',
            'responsable': lambda x: x.iloc[0] if len(x) > 0 else ''
        }).reset_index()
        
        # Clasificar casos - priorizar resultados finales
        # Primero obtener información de estado del negocio para cada caso
        df_estado_caso = df_filtrado.groupby('id_caso').agg({
            'estado_negocio': lambda x: x.iloc[0] if len(x) > 0 else '',
            'tiene_retiro': 'any'
        }).reset_index()
        
        df_casos_detalle = df_casos_detalle.merge(df_estado_caso[['id_caso', 'estado_negocio', 'tiene_retiro']], on='id_caso', how='left')
        
        # Clasificar con prioridad: Acuerdo > No Acuerdo > Inasistencia > Retiro > En Proceso > Otro
        df_casos_detalle['resultado'] = 'Otro'
        
        # Casos en proceso (Proceso Vigente o En Trámite sin resultado final)
        mask_en_proceso = (
            (df_casos_detalle['estado_negocio'].str.contains('Vigente|Trámite', case=False, na=False)) &
            (~df_casos_detalle['tiene_acuerdo']) &
            (~df_casos_detalle['tiene_no_acuerdo']) &
            (~df_casos_detalle['tiene_inasistencia']) &
            (~df_casos_detalle['tiene_retiro'])
        )
        df_casos_detalle.loc[mask_en_proceso, 'resultado'] = 'En Proceso'
        
        # Retiro oficioso
        df_casos_detalle.loc[df_casos_detalle['tiene_retiro'], 'resultado'] = 'Retirado'
        
        # Inasistencia (sobrescribe En Proceso y Retirado)
        df_casos_detalle.loc[df_casos_detalle['tiene_inasistencia'], 'resultado'] = 'Inasistencia'
        
        # Sin Acuerdo (sobrescribe Inasistencia, En Proceso y Retirado)
        df_casos_detalle.loc[df_casos_detalle['tiene_no_acuerdo'], 'resultado'] = 'Sin Acuerdo'
        
        # Con Acuerdo (prioridad máxima - sobrescribe todo)
        df_casos_detalle.loc[df_casos_detalle['tiene_acuerdo'], 'resultado'] = 'Con Acuerdo'
        
        # Resumen por resultado
        df_resultado = df_casos_detalle.groupby('resultado').agg({
            'id_caso': 'count',
            'dias_procesamiento': 'mean'
        }).reset_index()
        df_resultado.columns = ['Resultado', 'Total Casos', 'Días Promedio']
        df_resultado['Días Promedio'] = df_resultado['Días Promedio'].round(1)
        df_resultado['Porcentaje'] = (df_resultado['Total Casos'] / df_resultado['Total Casos'].sum() * 100).round(2)
        df_resultado = df_resultado.sort_values('Total Casos', ascending=False)
        
        st.markdown("#### Resumen por Resultado")
        st.dataframe(df_resultado, use_container_width=True)
        
        # Visualizaciones
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### Distribución de Resultados")
            fig_resultado = px.pie(
                df_resultado,
                values='Total Casos',
                names='Resultado',
                title="Distribución de Casos por Resultado"
            )
            fig_resultado.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig_resultado, use_container_width=True)
        
        with col2:
            st.markdown("##### Comparación de Resultados")
            fig_bar_resultado = px.bar(
                df_resultado,
                x='Resultado',
                y='Total Casos',
                color='Días Promedio',
                color_continuous_scale='RdYlGn',
                title="Casos por Resultado y Tiempo Promedio",
                labels={'Total Casos': 'Total de Casos', 'Resultado': 'Resultado', 'Días Promedio': 'Días Promedio'}
            )
            st.plotly_chart(fig_bar_resultado, use_container_width=True)
        
        # Tendencias mensuales de éxito
        st.markdown("##### Tendencia Mensual de Acuerdos")
        if 'mes_ano' in df_filtrado.columns:
            df_mes_acuerdo = df_filtrado.groupby('mes_ano').agg({
                'tiene_acuerdo': 'sum',
                'tiene_no_acuerdo': 'sum',
                'tiene_inasistencia': 'sum',
                'id_caso': 'nunique'
            }).reset_index()
            df_mes_acuerdo.columns = ['Mes', 'Con Acuerdo', 'Sin Acuerdo', 'Inasistencia', 'Total Casos']
            df_mes_acuerdo = df_mes_acuerdo.sort_values('Mes')
            df_mes_acuerdo['Tasa Acuerdos (%)'] = (df_mes_acuerdo['Con Acuerdo'] / df_mes_acuerdo['Total Casos'] * 100).round(2)
            
            fig_tendencia = go.Figure()
            fig_tendencia.add_trace(go.Scatter(
                x=df_mes_acuerdo['Mes'],
                y=df_mes_acuerdo['Con Acuerdo'],
                mode='lines+markers',
                name='Con Acuerdo',
                line=dict(color='#2ca02c', width=3)
            ))
            fig_tendencia.add_trace(go.Scatter(
                x=df_mes_acuerdo['Mes'],
                y=df_mes_acuerdo['Sin Acuerdo'],
                mode='lines+markers',
                name='Sin Acuerdo',
                line=dict(color='#d62728', width=2)
            ))
            fig_tendencia.add_trace(go.Scatter(
                x=df_mes_acuerdo['Mes'],
                y=df_mes_acuerdo['Inasistencia'],
                mode='lines+markers',
                name='Inasistencia',
                line=dict(color='#ff7f0e', width=2)
            ))
            fig_tendencia.update_layout(
                title="Tendencia de Resultados por Mes",
                xaxis_title="Mes",
                yaxis_title="Cantidad de Casos",
                hovermode='x unified',
                height=500
            )
            st.plotly_chart(fig_tendencia, use_container_width=True)
    
    # TAB 3: POR RESPONSABLE
    with tab3:
        st.subheader("Análisis por Responsable")
        st.markdown("Análisis de desempeño y productividad por responsable")
        
        # Resumen por responsable
        df_responsable = df_filtrado.groupby('responsable').agg({
            'id_caso': 'nunique',
            'tiene_acuerdo': 'sum',
            'tiene_no_acuerdo': 'sum',
            'tiene_inasistencia': 'sum',
            'dias_procesamiento': 'mean'
        }).reset_index()
        df_responsable.columns = ['Responsable', 'Total Casos', 'Eventos con Acuerdo', 
                                 'Eventos sin Acuerdo', 'Eventos Inasistencia', 'Días Promedio']
        df_responsable['Días Promedio'] = df_responsable['Días Promedio'].round(1)
        
        # Calcular tasa de éxito (casos con acuerdo / total casos)
        df_casos_resp = df_filtrado.groupby(['responsable', 'id_caso']).agg({
            'tiene_acuerdo': 'any'
        }).reset_index()
        df_tasa_resp = df_casos_resp.groupby('responsable').agg({
            'id_caso': 'count',
            'tiene_acuerdo': 'sum'
        }).reset_index()
        df_tasa_resp.columns = ['Responsable', 'Total Casos', 'Casos con Acuerdo']
        df_tasa_resp['Tasa Éxito (%)'] = (df_tasa_resp['Casos con Acuerdo'] / df_tasa_resp['Total Casos'] * 100).round(2)
        
        df_responsable = df_responsable.merge(df_tasa_resp[['Responsable', 'Tasa Éxito (%)']], on='Responsable', how='left')
        df_responsable = df_responsable.sort_values('Total Casos', ascending=False)
        
        st.markdown("#### Resumen por Responsable")
        st.dataframe(df_responsable, use_container_width=True, height=400)
        
        # Visualizaciones
        st.markdown("##### Top 20 Responsables por Volumen de Casos")
        fig_responsable = px.bar(
            df_responsable.head(20),
            x='Total Casos',
            y='Responsable',
            orientation='h',
            color='Tasa Éxito (%)',
            color_continuous_scale='RdYlGn',
            title="Top 20 Responsables por Volumen y Tasa de Éxito",
            labels={'Total Casos': 'Total de Casos', 'Responsable': 'Responsable', 'Tasa Éxito (%)': 'Tasa de Éxito (%)'}
        )
        fig_responsable.update_layout(height=600)
        st.plotly_chart(fig_responsable, use_container_width=True)
        
        # Análisis de eficiencia
        st.markdown("##### Análisis de Eficiencia: Volumen vs Tasa de Éxito")
        df_responsable_eff = df_responsable[df_responsable['Total Casos'] >= 5].copy()
        if not df_responsable_eff.empty:
            # Asegurar que Días Promedio sea numérico
            df_responsable_eff['Días Promedio'] = pd.to_numeric(df_responsable_eff['Días Promedio'], errors='coerce')
            df_responsable_eff = df_responsable_eff[df_responsable_eff['Días Promedio'].notna()]
            
            if not df_responsable_eff.empty:
                fig_scatter = px.scatter(
                    df_responsable_eff,
                    x='Total Casos',
                    y='Tasa Éxito (%)',
                    size='Días Promedio',
                    hover_name='Responsable',
                    hover_data=['Eventos con Acuerdo', 'Eventos sin Acuerdo'],
                    title="Eficiencia: Volumen vs Tasa de Éxito",
                    labels={
                        'Total Casos': 'Total de Casos',
                        'Tasa Éxito (%)': 'Tasa de Éxito (%)',
                        'Días Promedio': 'Días Promedio'
                    }
                )
                st.plotly_chart(fig_scatter, use_container_width=True)
    
    # TAB 4: ANÁLISIS TEMPORAL
    with tab4:
        st.subheader("Análisis Temporal")
        st.markdown("Tendencias y análisis de tiempos de procesamiento")
        
        if 'mes_ano' in df_filtrado.columns:
            # Tendencias mensuales
            st.markdown("#### Tendencias Mensuales")
            df_mes = df_filtrado.groupby('mes_ano').agg({
                'id_caso': 'nunique',
                'dias_procesamiento': 'mean',
                'tiene_acuerdo': 'sum'
            }).reset_index()
            df_mes.columns = ['Mes', 'Total Casos', 'Días Promedio', 'Eventos con Acuerdo']
            df_mes['Días Promedio'] = df_mes['Días Promedio'].round(1)
            df_mes = df_mes.sort_values('Mes')
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig_mes_casos = px.line(
                    df_mes,
                    x='Mes',
                    y='Total Casos',
                    markers=True,
                    title="Tendencia Mensual de Casos",
                    labels={'Total Casos': 'Total de Casos', 'Mes': 'Mes'}
                )
                st.plotly_chart(fig_mes_casos, use_container_width=True)
            
            with col2:
                fig_mes_tiempo = px.line(
                    df_mes[df_mes['Días Promedio'].notna()],
                    x='Mes',
                    y='Días Promedio',
                    markers=True,
                    title="Tiempo Promedio de Procesamiento por Mes",
                    labels={'Días Promedio': 'Días', 'Mes': 'Mes'}
                )
                st.plotly_chart(fig_mes_tiempo, use_container_width=True)
        
        # Tiempos por resultado
        st.markdown("#### Tiempo Promedio por Resultado")
        
        # Recrear la clasificación de casos para este tab
        df_casos_temporal = df_filtrado.groupby('id_caso').agg({
            'tiene_acuerdo': 'any',
            'tiene_no_acuerdo': 'any',
            'tiene_inasistencia': 'any',
            'dias_procesamiento': 'mean',
            'tiene_retiro': 'any'
        }).reset_index()
        
        # Obtener estado del negocio
        df_estado_temporal = df_filtrado.groupby('id_caso').agg({
            'estado_negocio': lambda x: x.iloc[0] if len(x) > 0 else ''
        }).reset_index()
        
        df_casos_temporal = df_casos_temporal.merge(df_estado_temporal[['id_caso', 'estado_negocio']], on='id_caso', how='left')
        
        # Clasificar casos
        df_casos_temporal['resultado'] = 'Otro'
        mask_en_proceso = (
            (df_casos_temporal['estado_negocio'].str.contains('Vigente|Trámite', case=False, na=False)) &
            (~df_casos_temporal['tiene_acuerdo']) &
            (~df_casos_temporal['tiene_no_acuerdo']) &
            (~df_casos_temporal['tiene_inasistencia']) &
            (~df_casos_temporal['tiene_retiro'])
        )
        df_casos_temporal.loc[mask_en_proceso, 'resultado'] = 'En Proceso'
        df_casos_temporal.loc[df_casos_temporal['tiene_retiro'], 'resultado'] = 'Retirado'
        df_casos_temporal.loc[df_casos_temporal['tiene_inasistencia'], 'resultado'] = 'Inasistencia'
        df_casos_temporal.loc[df_casos_temporal['tiene_no_acuerdo'], 'resultado'] = 'Sin Acuerdo'
        df_casos_temporal.loc[df_casos_temporal['tiene_acuerdo'], 'resultado'] = 'Con Acuerdo'
        
        # Agrupar por resultado con conteo y tiempo promedio
        df_tiempo_resultado = df_casos_temporal.groupby('resultado').agg({
            'id_caso': 'count',
            'dias_procesamiento': 'mean'
        }).reset_index()
        df_tiempo_resultado.columns = ['Resultado', 'Cantidad', 'Días Promedio']
        df_tiempo_resultado = df_tiempo_resultado[df_tiempo_resultado['Días Promedio'].notna()]
        df_tiempo_resultado['Días Promedio'] = df_tiempo_resultado['Días Promedio'].round(1)
        df_tiempo_resultado = df_tiempo_resultado.sort_values('Cantidad', ascending=False)
        
        # Mostrar tabla con cantidades
        st.dataframe(df_tiempo_resultado, use_container_width=True, hide_index=True)
        
        # Gráfico
        fig_tiempo = px.bar(
            df_tiempo_resultado,
            x='Resultado',
            y='Días Promedio',
            text='Cantidad',
            title="Tiempo Promedio de Procesamiento por Resultado",
            labels={'Días Promedio': 'Días Promedio', 'Resultado': 'Resultado', 'Cantidad': 'Cantidad de Casos'},
            color='Cantidad',
            color_continuous_scale='Blues'
        )
        fig_tiempo.update_traces(texttemplate='%{text} casos', textposition='outside')
        st.plotly_chart(fig_tiempo, use_container_width=True)
    
    # TAB 5: EVENTOS Y ESTADOS
    with tab5:
        st.subheader("Análisis de Eventos y Estados")
        st.markdown("Análisis de tipos de eventos y flujo de estados")
        
        # Resumen por evento
        df_evento = df_filtrado.groupby('evento').agg({
            'id_caso': 'nunique',
            'dias_procesamiento': 'mean',
            'dias_duracion_evento': 'mean'
        }).reset_index()
        df_evento.columns = ['Evento', 'Total Casos', 'Días Prom. Inicio', 'Días Duración']
        df_evento['Días Prom. Inicio'] = df_evento['Días Prom. Inicio'].round(1)
        df_evento['Días Duración'] = df_evento['Días Duración'].round(1)
        df_evento = df_evento.sort_values('Total Casos', ascending=False)
        
        st.markdown("#### Resumen por Tipo de Evento")
        st.dataframe(df_evento.head(20), use_container_width=True, height=400)
        
        # Visualizaciones
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### Top 15 Eventos por Volumen")
            fig_evento = px.bar(
                df_evento.head(15),
                x='Total Casos',
                y='Evento',
                orientation='h',
                color='Total Casos',
                color_continuous_scale='Blues',
                title="Top 15 Eventos por Volumen"
            )
            fig_evento.update_layout(height=600)
            st.plotly_chart(fig_evento, use_container_width=True)
        
        with col2:
            st.markdown("##### Distribución Porcentual (Top 10)")
            fig_pie_evento = px.pie(
                df_evento.head(10),
                values='Total Casos',
                names='Evento',
                title="Distribución de Eventos - Top 10"
            )
            fig_pie_evento.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig_pie_evento, use_container_width=True)
        
        # Eventos por estado
        st.markdown("##### Eventos por Estado")
        df_evento_estado = df_filtrado.groupby(['evento', 'estado']).size().reset_index(name='Cantidad')
        df_evento_estado = df_evento_estado.sort_values('Cantidad', ascending=False).head(20)
        df_evento_estado.columns = ['Evento', 'Estado', 'Cantidad']
        st.dataframe(df_evento_estado, use_container_width=True)
    
    # EXPORTACIÓN
    st.markdown("---")
    st.subheader("Exportar Reportes")
    
    # Preparar datos para exportación
    export_data = {}
    
    # Datos completos
    cols_to_export = [c for c in df_filtrado.columns]
    export_data["Datos Completos"] = df_filtrado[cols_to_export].copy()
    
    # Agregar hojas de resumen
    if not df_responsable.empty:
        export_data["Resumen por Responsable"] = df_responsable.copy()
    if not df_resultado.empty:
        export_data["Resumen por Resultado"] = df_resultado.copy()
    if not df_evento.empty:
        export_data["Resumen por Evento"] = df_evento.copy()
    
    # Botón de descarga
    excel_data = export_to_excel(export_data, "reporte_conciliacion.xlsx")
    
    st.download_button(
        label="Descargar Reporte Completo (Excel)",
        data=excel_data,
        file_name="reporte_conciliacion.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

