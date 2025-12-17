import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from io import BytesIO
from datetime import datetime


def remove_timezone(series):
    """Remueve timezone de una serie de datetime de forma segura"""
    if series.empty or series.isna().all():
        return series
    try:
        # Verificar si la serie tiene timezone
        tz_info = series.dt.tz
        if tz_info is not None:
            # Es timezone-aware: remover timezone de cada valor
            # La forma más directa es usar apply para remover tzinfo de cada timestamp
            return series.apply(lambda x: x.replace(tzinfo=None) if pd.notna(x) and hasattr(x, 'tz') and x.tz is not None else x)
        else:
            # Ya es naive, retornar tal cual
            return series
    except (AttributeError, TypeError, ValueError):
        # Si falla, intentar método alternativo más simple
        try:
            # Convertir a string y luego a datetime sin timezone (esto automáticamente remueve timezone)
            return pd.to_datetime(series.astype(str), errors='coerce')
        except:
            return series


@st.cache_data
def load_data(filepath):
    """Carga y procesa el CSV de radicados."""
    try:
        df = pd.read_csv(filepath)
        
        # Convertir fecha_radicado a datetime
        df['fecha_radicado'] = pd.to_datetime(df['fecha_radicado'], errors='coerce')
        # Remover timezone si existe (convertir a naive)
        df['fecha_radicado'] = remove_timezone(df['fecha_radicado'])
        
        # Extraer componentes de fecha
        df['ano'] = df['fecha_radicado'].dt.year
        df['mes'] = df['fecha_radicado'].dt.month
        df['mes_nombre'] = df['fecha_radicado'].dt.strftime('%Y-%m')
        df['mes_ano'] = df['fecha_radicado'].dt.to_period('M').astype(str)
        df['dia_semana'] = df['fecha_radicado'].dt.day_name()
        df['semana'] = df['fecha_radicado'].dt.isocalendar().week
        
        # Convertir fecha_atencion a datetime si existe
        if 'fecha_atencion' in df.columns:
            df['fecha_atencion'] = pd.to_datetime(df['fecha_atencion'], errors='coerce')
            # Remover timezone si existe (convertir a naive)
            df['fecha_atencion'] = remove_timezone(df['fecha_atencion'])
        
        # Crear flag de atención
        df['tiene_atencion'] = df['id_atencion'].notna() & (df['id_atencion'] != '')
        
        # Calcular tiempo hasta atención (en días)
        df['dias_hasta_atencion'] = None
        mask_atencion = df['tiene_atencion'] & df['fecha_atencion'].notna() & df['fecha_radicado'].notna()
        if mask_atencion.any():
            # Asegurar que ambas sean timezone-naive antes de restar
            fecha_atencion = remove_timezone(df.loc[mask_atencion, 'fecha_atencion'])
            fecha_radicado = remove_timezone(df.loc[mask_atencion, 'fecha_radicado'])
            
            # Calcular diferencia en días
            df.loc[mask_atencion, 'dias_hasta_atencion'] = (
                fecha_atencion - fecha_radicado
            ).dt.days
        
        # Limpiar y normalizar campos de texto
        text_cols = ['origen', 'destino', 'servicio', 'radicador', 'funcionario_atendio', 'asunto']
        for col in text_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
                df[col] = df[col].replace('nan', '')
                df[col] = df[col].replace('None', '')
        
        return df
    except Exception as e:
        st.error(f"Error técnico al procesar el archivo: {e}")
        return pd.DataFrame()


def export_to_excel(df_dict, filename="reporte_radicados.xlsx"):
    """Exporta múltiples DataFrames a un archivo Excel con múltiples hojas"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for sheet_name, df in df_dict.items():
            # Limpiar nombre de hoja (Excel tiene límites)
            clean_name = sheet_name[:31] if len(sheet_name) > 31 else sheet_name
            df.to_excel(writer, sheet_name=clean_name, index=False)
    output.seek(0)
    return output.getvalue()


def run(project_info):
    # --- Configuración de Rutas ---
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(current_dir, "..", "data", "radicados.csv")

    # --- Encabezado del Reporte ---
    st.title("Análisis Integral de Radicados")
    st.markdown("### Sistema de seguimiento y análisis de radicados ingresados a la entidad")
    st.markdown("---")

    # --- Carga de Datos ---
    if not os.path.exists(data_path):
        st.error(f"No se encontró el archivo de datos en: {data_path}")
        return

    df = load_data(data_path)

    if df.empty:
        st.warning("El archivo de datos está vacío o tiene un formato no válido.")
        return

    # --- FILTROS GLOBALES (Sidebar) ---
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

        # Filtro Canal de Ingreso (Origen)
        lista_origenes = ["TODOS"] + sorted([
            o for o in df["origen"].unique().tolist() 
            if pd.notna(o) and o != "" and o != "nan"
        ])
        filtro_origen = st.selectbox("Canal de Ingreso (Origen)", lista_origenes)

        # Filtro Destino
        lista_destinos = ["TODOS"] + sorted([
            d for d in df["destino"].unique().tolist() 
            if pd.notna(d) and d != "" and d != "nan"
        ])
        filtro_destino = st.selectbox("Destino", lista_destinos)

        # Filtro Estado de Atención
        filtro_atencion = st.selectbox(
            "Estado de Atención",
            ["TODOS", "Con Atención", "Sin Atención"]
        )

        # Filtro Servicio
        lista_servicios = ["TODOS"] + sorted([
            s for s in df["servicio"].unique().tolist() 
            if pd.notna(s) and s != "" and s != "nan"
        ])
        filtro_servicio = st.selectbox("Servicio", lista_servicios)

        # Filtro Radicador
        lista_radicadores = ["TODOS"] + sorted([
            r for r in df["radicador"].unique().tolist() 
            if pd.notna(r) and r != "" and r != "nan"
        ])
        filtro_radicador = st.selectbox("Radicador", lista_radicadores)

    # Aplicar filtros
    df_filtrado = df.copy()
    
    if fecha_inicio and fecha_fin:
        df_filtrado = df_filtrado[
            (df_filtrado['fecha_radicado'].dt.date >= fecha_inicio) &
            (df_filtrado['fecha_radicado'].dt.date <= fecha_fin)
        ]
    
    if filtro_origen != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["origen"] == filtro_origen]
    if filtro_destino != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["destino"] == filtro_destino]
    if filtro_atencion == "Con Atención":
        df_filtrado = df_filtrado[df_filtrado["tiene_atencion"] == True]
    elif filtro_atencion == "Sin Atención":
        df_filtrado = df_filtrado[df_filtrado["tiene_atencion"] == False]
    if filtro_servicio != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["servicio"] == filtro_servicio]
    if filtro_radicador != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["radicador"] == filtro_radicador]

    # --- INDICADORES CLAVE (KPIs) ---
    total_radicados = len(df_filtrado)
    radicados_con_atencion = df_filtrado['tiene_atencion'].sum()
    radicados_sin_atencion = total_radicados - radicados_con_atencion
    tasa_atencion = (radicados_con_atencion / total_radicados * 100) if total_radicados > 0 else 0
    
    # Radicados del mes actual
    mes_actual = datetime.now().strftime('%Y-%m')
    radicados_mes_actual = len(df_filtrado[df_filtrado['mes_ano'] == mes_actual])
    
    # Canales de ingreso únicos
    canales_unicos = df_filtrado['origen'].nunique()

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    col1.metric("Total Radicados", f"{total_radicados:,.0f}")
    col2.metric("Con Atención", f"{radicados_con_atencion:,.0f}")
    col3.metric("Sin Atención", f"{radicados_sin_atencion:,.0f}")
    col4.metric("Tasa de Atención", f"{tasa_atencion:.1f}%")
    col5.metric("Este Mes", f"{radicados_mes_actual:,.0f}")
    col6.metric("Canales Únicos", f"{canales_unicos:,.0f}")

    st.markdown("---")

    # --- CUERPO DEL ANÁLISIS CON PESTAÑAS ---
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
        [
            "Por Mes y Canal de Ingreso",
            "Análisis por Canal de Ingreso",
            "Análisis por Destino",
            "Análisis Temporal",
            "Análisis de Servicios",
            "Análisis por Radicador",
            "Resumen Ejecutivo"
        ]
    )

    # --- TAB 1: POR MES Y CANAL DE INGRESO (REQUERIMIENTO PRINCIPAL) ---
    with tab1:
        st.subheader("Radicados por Mes y Canal de Ingreso")
        st.markdown("""
        **Análisis principal:** Esta sección muestra el número de radicados ingresados a la entidad, 
        discriminados por mes y por canal de ingreso (origen), indicando cuáles tienen atención y cuáles no.
        """)

        # Tabla principal: Radicados por mes y origen
        st.markdown("#### Tabla: Radicados por Mes y Canal de Ingreso")
        
        # Agrupar por mes y origen
        df_mes_origen = df_filtrado.groupby(['mes_ano', 'origen']).agg({
            'numero_radicado': 'count',
            'tiene_atencion': 'sum'
        }).reset_index()
        df_mes_origen.columns = ['Mes', 'Canal de Ingreso', 'Total Radicados', 'Con Atención']
        df_mes_origen['Sin Atención'] = df_mes_origen['Total Radicados'] - df_mes_origen['Con Atención']
        df_mes_origen['Tasa de Atención (%)'] = (
            df_mes_origen['Con Atención'] / df_mes_origen['Total Radicados'] * 100
        ).round(2)
        df_mes_origen = df_mes_origen.sort_values(['Mes', 'Total Radicados'], ascending=[True, False])
        
        st.dataframe(df_mes_origen, use_container_width=True, height=400)

        # Visualizaciones
        st.markdown("---")
        st.markdown("#### Visualizaciones Interactivas")

        # Gráfico 1: Tendencia de radicados por mes
        st.markdown("##### Tendencia de Radicados por Mes")
        df_mes = df_filtrado.groupby('mes_ano').agg({
            'numero_radicado': 'count',
            'tiene_atencion': 'sum'
        }).reset_index()
        df_mes.columns = ['Mes', 'Total', 'Con Atención']
        df_mes['Sin Atención'] = df_mes['Total'] - df_mes['Con Atención']
        df_mes = df_mes.sort_values('Mes')

        fig_tendencia = go.Figure()
        fig_tendencia.add_trace(go.Scatter(
            x=df_mes['Mes'],
            y=df_mes['Total'],
            mode='lines+markers',
            name='Total Radicados',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=8)
        ))
        fig_tendencia.add_trace(go.Scatter(
            x=df_mes['Mes'],
            y=df_mes['Con Atención'],
            mode='lines+markers',
            name='Con Atención',
            line=dict(color='#2ca02c', width=2),
            marker=dict(size=6)
        ))
        fig_tendencia.add_trace(go.Scatter(
            x=df_mes['Mes'],
            y=df_mes['Sin Atención'],
            mode='lines+markers',
            name='Sin Atención',
            line=dict(color='#d62728', width=2),
            marker=dict(size=6)
        ))
        fig_tendencia.update_layout(
            title="Tendencia de Radicados por Mes",
            xaxis_title="Mes",
            yaxis_title="Número de Radicados",
            hovermode='x unified',
            height=500
        )
        st.plotly_chart(fig_tendencia, use_container_width=True)

        # Gráfico 2: Barras apiladas por mes
        st.markdown("##### Distribución de Radicados con y sin Atención por Mes")
        fig_barras = px.bar(
            df_mes,
            x='Mes',
            y=['Con Atención', 'Sin Atención'],
            title="Radicados con y sin Atención por Mes",
            labels={'value': 'Número de Radicados', 'variable': 'Estado'},
            color_discrete_map={'Con Atención': '#2ca02c', 'Sin Atención': '#d62728'}
        )
        fig_barras.update_layout(barmode='stack', height=500)
        st.plotly_chart(fig_barras, use_container_width=True)

        # Gráfico 4: Top canales de ingreso
        st.markdown("##### Top 20 Canales de Ingreso por Volumen")
        df_top_origenes = df_filtrado.groupby('origen').agg({
            'numero_radicado': 'count',
            'tiene_atencion': 'sum'
        }).reset_index()
        df_top_origenes.columns = ['Canal de Ingreso', 'Total', 'Con Atención']
        df_top_origenes['Tasa Atención (%)'] = (df_top_origenes['Con Atención'] / df_top_origenes['Total'] * 100).round(2)
        df_top_origenes = df_top_origenes.sort_values('Total', ascending=False).head(20)

        fig_top = px.bar(
            df_top_origenes,
            x='Total',
            y='Canal de Ingreso',
            orientation='h',
            color='Tasa Atención (%)',
            color_continuous_scale='RdYlGn',
            labels={'Total': 'Total de Radicados', 'Canal de Ingreso': 'Canal de Ingreso'},
            title="Top 20 Canales de Ingreso por Volumen de Radicados"
        )
        fig_top.update_layout(height=600)
        st.plotly_chart(fig_top, use_container_width=True)

    # --- TAB 2: ANÁLISIS POR CANAL DE INGRESO ---
    with tab2:
        st.subheader("Análisis Detallado por Canal de Ingreso")
        st.markdown("""
        Análisis completo de los canales de ingreso (origen) de los radicados, incluyendo distribución, 
        tasas de atención y comparaciones entre canales.
        """)

        # Resumen por canal de ingreso
        df_origen = df_filtrado.groupby('origen').agg({
            'numero_radicado': 'count',
            'tiene_atencion': 'sum',
            'dias_hasta_atencion': 'mean'
        }).reset_index()
        df_origen.columns = ['Canal de Ingreso', 'Total Radicados', 'Con Atención', 'Días Promedio hasta Atención']
        df_origen['Sin Atención'] = df_origen['Total Radicados'] - df_origen['Con Atención']
        df_origen['Tasa de Atención (%)'] = (df_origen['Con Atención'] / df_origen['Total Radicados'] * 100).round(2)
        df_origen['Días Promedio hasta Atención'] = df_origen['Días Promedio hasta Atención'].round(1)
        df_origen = df_origen.sort_values('Total Radicados', ascending=False)

        st.markdown("#### Resumen por Canal de Ingreso")
        st.dataframe(df_origen, use_container_width=True, height=400)

        # Visualizaciones
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("##### Distribución de Radicados por Canal de Ingreso (Top 15)")
            fig_pie = px.pie(
                df_origen.head(15),
                values='Total Radicados',
                names='Canal de Ingreso',
                title="Distribución de Radicados - Top 15 Canales"
            )
            fig_pie.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig_pie, use_container_width=True)

        with col2:
            st.markdown("##### Tasa de Atención por Canal de Ingreso (Top 15)")
            df_tasa = df_origen[df_origen['Total Radicados'] >= 10].head(15).sort_values('Tasa de Atención (%)', ascending=True)
            fig_tasa = px.bar(
                df_tasa,
                x='Tasa de Atención (%)',
                y='Canal de Ingreso',
                orientation='h',
                title="Tasa de Atención por Canal de Ingreso",
                color='Tasa de Atención (%)',
                color_continuous_scale='RdYlGn'
            )
            st.plotly_chart(fig_tasa, use_container_width=True)

        # Comparación de canales
        st.markdown("##### Comparación: Volumen vs Tasa de Atención")
        fig_scatter = px.scatter(
            df_origen[df_origen['Total Radicados'] >= 5],
            x='Total Radicados',
            y='Tasa de Atención (%)',
            size='Total Radicados',
            hover_name='Canal de Ingreso',
            hover_data=['Con Atención', 'Sin Atención'],
            title="Matriz: Volumen vs Tasa de Atención por Canal de Ingreso",
            labels={
                'Total Radicados': 'Total de Radicados',
                'Tasa de Atención (%)': 'Tasa de Atención (%)'
            }
        )
        fig_scatter.update_layout(height=500)
        st.plotly_chart(fig_scatter, use_container_width=True)

    # --- TAB 3: ANÁLISIS POR DESTINO ---
    with tab3:
        st.subheader("Análisis por Destino")
        st.markdown("""
        Análisis de los radicados según su destino (unidad que procesa el radicado), 
        incluyendo flujo desde origen hasta destino.
        """)

        # Resumen por destino
        df_destino = df_filtrado.groupby('destino').agg({
            'numero_radicado': 'count',
            'tiene_atencion': 'sum'
        }).reset_index()
        df_destino.columns = ['Destino', 'Total Radicados', 'Con Atención']
        df_destino['Sin Atención'] = df_destino['Total Radicados'] - df_destino['Con Atención']
        df_destino['Tasa de Atención (%)'] = (df_destino['Con Atención'] / df_destino['Total Radicados'] * 100).round(2)
        df_destino = df_destino.sort_values('Total Radicados', ascending=False)

        st.markdown("#### Resumen por Destino")
        st.dataframe(df_destino, use_container_width=True, height=400)

        # Visualizaciones
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("##### Radicados por Destino (Top 15)")
            fig_dest = px.bar(
                df_destino.head(15),
                x='Total Radicados',
                y='Destino',
                orientation='h',
                color='Tasa de Atención (%)',
                color_continuous_scale='Blues',
                title="Top 15 Destinos por Volumen"
            )
            fig_dest.update_layout(height=500)
            st.plotly_chart(fig_dest, use_container_width=True)

        with col2:
            st.markdown("##### Distribución Porcentual por Destino (Top 10)")
            fig_pie_dest = px.pie(
                df_destino.head(10),
                values='Total Radicados',
                names='Destino',
                title="Distribución de Radicados - Top 10 Destinos"
            )
            fig_pie_dest.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig_pie_dest, use_container_width=True)

        # Flujo Origen -> Destino
        st.markdown("##### Flujo: Canal de Ingreso → Destino (Top 20 combinaciones)")
        df_flujo = df_filtrado.groupby(['origen', 'destino']).size().reset_index(name='Cantidad')
        df_flujo = df_flujo.sort_values('Cantidad', ascending=False).head(20)
        df_flujo.columns = ['Canal de Ingreso', 'Destino', 'Cantidad']
        
        st.dataframe(df_flujo, use_container_width=True)

    # --- TAB 4: ANÁLISIS TEMPORAL ---
    with tab4:
        st.subheader("Análisis Temporal")
        st.markdown("""
        Análisis de patrones temporales: tendencias mensuales, patrones semanales, 
        tiempo hasta atención y períodos pico.
        """)

        # Tendencias mensuales
        st.markdown("#### Tendencias Mensuales")
        df_mes_detalle = df_filtrado.groupby('mes_ano').agg({
            'numero_radicado': 'count',
            'tiene_atencion': 'sum',
            'dias_hasta_atencion': 'mean'
        }).reset_index()
        df_mes_detalle.columns = ['Mes', 'Total', 'Con Atención', 'Días Promedio hasta Atención']
        df_mes_detalle['Días Promedio hasta Atención'] = df_mes_detalle['Días Promedio hasta Atención'].round(1)
        df_mes_detalle = df_mes_detalle.sort_values('Mes')

        col1, col2 = st.columns(2)
        with col1:
            fig_mes = px.line(
                df_mes_detalle,
                x='Mes',
                y='Total',
                markers=True,
                title="Tendencia Mensual de Radicados",
                labels={'Total': 'Total de Radicados'}
            )
            st.plotly_chart(fig_mes, use_container_width=True)

        with col2:
            fig_dias = px.bar(
                df_mes_detalle[df_mes_detalle['Días Promedio hasta Atención'].notna()],
                x='Mes',
                y='Días Promedio hasta Atención',
                title="Días Promedio hasta Atención por Mes",
                labels={'Días Promedio hasta Atención': 'Días'}
            )
            st.plotly_chart(fig_dias, use_container_width=True)

        # Patrones semanales
        st.markdown("#### Patrones por Día de la Semana")
        df_semana = df_filtrado.groupby('dia_semana').agg({
            'numero_radicado': 'count',
            'tiene_atencion': 'sum'
        }).reset_index()
        df_semana.columns = ['Día de la Semana', 'Total', 'Con Atención']
        orden_dias = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        df_semana['Día de la Semana'] = pd.Categorical(df_semana['Día de la Semana'], categories=orden_dias, ordered=True)
        df_semana = df_semana.sort_values('Día de la Semana')

        fig_semana = px.bar(
            df_semana,
            x='Día de la Semana',
            y='Total',
            title="Distribución de Radicados por Día de la Semana",
            labels={'Total': 'Total de Radicados'}
        )
        st.plotly_chart(fig_semana, use_container_width=True)

    # --- TAB 5: ANÁLISIS DE SERVICIOS ---
    with tab5:
        st.subheader("Análisis de Servicios")
        st.markdown("""
        Análisis de los tipos de servicios solicitados, su distribución y relación 
        con canales de ingreso y tasas de atención.
        """)

        # Resumen por servicio - Filtrar servicios válidos
        df_servicio_filtrado = df_filtrado[
            df_filtrado['servicio'].notna() & 
            (df_filtrado['servicio'] != '') & 
            (df_filtrado['servicio'] != 'nan')
        ].copy()
        
        if len(df_servicio_filtrado) > 0:
            df_servicio = df_servicio_filtrado.groupby('servicio').agg({
                'numero_radicado': 'count',
                'tiene_atencion': 'sum'
            }).reset_index()
            df_servicio.columns = ['Servicio', 'Total Radicados', 'Con Atención']
            df_servicio['Sin Atención'] = df_servicio['Total Radicados'] - df_servicio['Con Atención']
            df_servicio['Tasa de Atención (%)'] = (df_servicio['Con Atención'] / df_servicio['Total Radicados'] * 100).round(2)
            df_servicio = df_servicio.sort_values('Total Radicados', ascending=False)

            st.markdown("#### Resumen por Servicio")
            st.dataframe(df_servicio, use_container_width=True, height=400)

            # Visualizaciones
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("##### Top 15 Servicios por Volumen")
                if len(df_servicio) > 0:
                    fig_serv = px.bar(
                        df_servicio.head(15),
                        x='Total Radicados',
                        y='Servicio',
                        orientation='h',
                        color='Tasa de Atención (%)',
                        color_continuous_scale='Greens',
                        title="Top 15 Servicios por Volumen"
                    )
                    fig_serv.update_layout(height=500)
                    st.plotly_chart(fig_serv, use_container_width=True)
                else:
                    st.info("No hay datos de servicios para mostrar.")

            with col2:
                st.markdown("##### Distribución Porcentual de Servicios (Top 10)")
                if len(df_servicio) > 0:
                    # Preparar datos para el pie chart (top 10)
                    df_pie = df_servicio.head(10).copy()
                    # Asegurar que los valores sean numéricos
                    df_pie['Total Radicados'] = pd.to_numeric(df_pie['Total Radicados'], errors='coerce')
                    # Filtrar filas con valores válidos
                    df_pie = df_pie[df_pie['Total Radicados'] > 0]
                    
                    if len(df_pie) > 0:
                        fig_pie_serv = px.pie(
                            df_pie,
                            values='Total Radicados',
                            names='Servicio',
                            title="Distribución de Radicados - Top 10 Servicios"
                        )
                        fig_pie_serv.update_traces(
                            textposition="inside", 
                            textinfo="percent+label",
                            hovertemplate="<b>%{label}</b><br>Total: %{value}<br>Porcentaje: %{percent}<extra></extra>"
                        )
                        fig_pie_serv.update_layout(height=500)
                        st.plotly_chart(fig_pie_serv, use_container_width=True)
                    else:
                        st.info("No hay datos válidos para el gráfico de pastel.")
                else:
                    st.info("No hay datos de servicios para mostrar.")
        else:
            st.warning("No hay datos disponibles con servicios definidos.")

        # Servicios por canal de ingreso
        st.markdown("##### Servicios por Canal de Ingreso (Top 20 combinaciones)")
        # Filtrar filas donde servicio no sea nulo o vacío
        df_serv_origen = df_filtrado[
            df_filtrado['servicio'].notna() & 
            (df_filtrado['servicio'] != '') & 
            (df_filtrado['servicio'] != 'nan')
        ].copy()
        
        if len(df_serv_origen) > 0:
            # Agrupar y contar (origen primero para que sea la primera columna)
            df_serv_origen = df_serv_origen.groupby(['origen', 'servicio']).agg({
                'numero_radicado': 'count',
                'tiene_atencion': 'sum'
            }).reset_index()
            df_serv_origen.columns = ['Canal de Ingreso', 'Servicio', 'Total Radicados', 'Con Atención']
            df_serv_origen['Sin Atención'] = df_serv_origen['Total Radicados'] - df_serv_origen['Con Atención']
            df_serv_origen['Tasa de Atención (%)'] = (
                df_serv_origen['Con Atención'] / df_serv_origen['Total Radicados'] * 100
            ).round(2)
            # Reordenar columnas para asegurar que Canal de Ingreso esté primero
            df_serv_origen = df_serv_origen[['Canal de Ingreso', 'Servicio', 'Total Radicados', 'Con Atención', 'Sin Atención', 'Tasa de Atención (%)']]
            df_serv_origen = df_serv_origen.sort_values('Total Radicados', ascending=False).head(20)
            st.dataframe(df_serv_origen, use_container_width=True)
        else:
            st.info("No hay datos disponibles con servicio definido para mostrar.")

    # --- TAB 6: ANÁLISIS POR RADICADOR ---
    with tab6:
        st.subheader("Análisis por Radicador")
        st.markdown("""
        Análisis de productividad y distribución de radicados por radicador 
        (persona que registra el radicado).
        """)

        # Resumen por radicador
        df_radicador = df_filtrado.groupby('radicador').agg({
            'numero_radicado': 'count',
            'tiene_atencion': 'sum',
            'origen': lambda x: x.nunique()
        }).reset_index()
        df_radicador.columns = ['Radicador', 'Total Radicados', 'Con Atención', 'Canales Únicos']
        df_radicador['Sin Atención'] = df_radicador['Total Radicados'] - df_radicador['Con Atención']
        df_radicador['Tasa de Atención (%)'] = (df_radicador['Con Atención'] / df_radicador['Total Radicados'] * 100).round(2)
        df_radicador = df_radicador.sort_values('Total Radicados', ascending=False)

        st.markdown("#### Resumen por Radicador")
        st.dataframe(df_radicador, use_container_width=True, height=400)

        # Visualizaciones
        st.markdown("##### Top 20 Radicadores por Productividad")
        fig_rad = px.bar(
            df_radicador.head(20),
            x='Total Radicados',
            y='Radicador',
            orientation='h',
            color='Tasa de Atención (%)',
            color_continuous_scale='Purples',
            title="Top 20 Radicadores por Volumen de Radicados",
            labels={'Total Radicados': 'Total de Radicados'}
        )
        fig_rad.update_layout(height=600)
        st.plotly_chart(fig_rad, use_container_width=True)

    # --- TAB 7: RESUMEN EJECUTIVO ---
    with tab7:
        st.subheader("Resumen Ejecutivo")
        st.markdown("""
        Resumen ejecutivo con los principales indicadores, insights y métricas clave 
        del análisis de radicados.
        """)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Top 10 Canales de Ingreso")
            top_origenes = df_filtrado.groupby('origen').size().reset_index(name='Total')
            top_origenes = top_origenes.sort_values('Total', ascending=False).head(10)
            top_origenes.columns = ['Canal de Ingreso', 'Total Radicados']
            st.dataframe(top_origenes, use_container_width=True, hide_index=True)

        with col2:
            st.markdown("#### Top 10 Destinos")
            top_destinos = df_filtrado.groupby('destino').size().reset_index(name='Total')
            top_destinos = top_destinos.sort_values('Total', ascending=False).head(10)
            top_destinos.columns = ['Destino', 'Total Radicados']
            st.dataframe(top_destinos, use_container_width=True, hide_index=True)

        st.markdown("---")

        col3, col4 = st.columns(2)

        with col3:
            st.markdown("#### Top 10 Servicios")
            top_servicios = df_filtrado.groupby('servicio').size().reset_index(name='Total')
            top_servicios = top_servicios.sort_values('Total', ascending=False).head(10)
            top_servicios.columns = ['Servicio', 'Total Radicados']
            st.dataframe(top_servicios, use_container_width=True, hide_index=True)

        with col4:
            st.markdown("#### Top 10 Radicadores")
            top_radicadores = df_filtrado.groupby('radicador').size().reset_index(name='Total')
            top_radicadores = top_radicadores.sort_values('Total', ascending=False).head(10)
            top_radicadores.columns = ['Radicador', 'Total Radicados']
            st.dataframe(top_radicadores, use_container_width=True, hide_index=True)

        # Insights
        st.markdown("---")
        st.markdown("#### Insights Clave")
        
        # Calcular insights
        mes_max = df_filtrado.groupby('mes_ano').size().idxmax()
        mes_max_count = df_filtrado.groupby('mes_ano').size().max()
        origen_max = df_filtrado.groupby('origen').size().idxmax()
        origen_max_count = df_filtrado.groupby('origen').size().max()
        
        st.info(f"""
        **Insights del Período Analizado:**
        
        - **Mes con más radicados:** {mes_max} ({mes_max_count:,} radicados)
        - **Canal de ingreso principal:** {origen_max} ({origen_max_count:,} radicados)
        - **Tasa general de atención:** {tasa_atencion:.1f}%
        - **Total de canales de ingreso únicos:** {canales_unicos:,}
        """)

    # --- EXPORTACIÓN A EXCEL ---
    st.markdown("---")
    st.subheader("Exportar Reportes")

    # Preparar datos para exportación
    export_data = {}
    
    # Datos completos filtrados
    cols_to_export = [c for c in df_filtrado.columns if not c.endswith('_num')]
    export_data["Datos Completos"] = df_filtrado[cols_to_export].copy()
    
    # Resumen por mes y origen
    if not df_mes_origen.empty:
        export_data["Resumen Mes y Canal"] = df_mes_origen.copy()
    
    # Resumen por destino
    if not df_destino.empty:
        export_data["Resumen por Destino"] = df_destino.copy()
    
    # Resumen por servicio
    if not df_servicio.empty:
        export_data["Resumen por Servicio"] = df_servicio.copy()
    
    # Resumen por radicador
    if not df_radicador.empty:
        export_data["Resumen por Radicador"] = df_radicador.copy()
    
    # Resumen por origen
    if not df_origen.empty:
        export_data["Resumen por Canal Ingreso"] = df_origen.copy()

    # Botón de descarga
    excel_data = export_to_excel(export_data, "reporte_radicados.xlsx")
    
    st.download_button(
        label="Descargar Reporte Completo (Excel)",
        data=excel_data,
        file_name="reporte_radicados.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
