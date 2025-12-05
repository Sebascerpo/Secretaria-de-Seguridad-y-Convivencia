import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from io import BytesIO


def parse_time_to_minutes(time_str):
    """
    Convierte una cadena de tiempo formato HH:MM:SS a minutos (float).
    Maneja valores nulos o formatos incorrectos devolviendo 0.
    """
    try:
        if pd.isna(time_str):
            return 0.0
        time_str = str(time_str).strip()
        parts = time_str.split(":")
        if len(parts) == 3:
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = int(parts[2])
            return hours * 60 + minutes + seconds / 60.0
        return 0.0
    except Exception:
        return 0.0


def format_minutes_to_time(minutes):
    """Convierte minutos a formato HH:MM:SS"""
    if pd.isna(minutes) or minutes == 0:
        return "00:00:00"
    hours = int(minutes // 60)
    mins = int(minutes % 60)
    secs = int((minutes % 1) * 60)
    return f"{hours:02d}:{mins:02d}:{secs:02d}"


def load_data(filepath):
    """Carga y procesa el CSV de resumen de atenciones."""
    try:
        df = pd.read_csv(filepath)

        # Convertir columnas de tiempo (texto) a valor numérico (minutos)
        time_cols = [
            "tiempo_promedio",
            "tiempo_total_dedicado",
            "tiempo_minimo",
            "tiempo_maximo",
        ]

        for col in time_cols:
            if col in df.columns:
                df[f"{col}_num"] = df[col].apply(parse_time_to_minutes)

        # Normalizar textos para evitar duplicados
        text_cols = [
            "funcionario_atendio",
            "tipo_atencion",
            "servicio",
            "area",
            "sede",
            "estado",
            "poblacion",
            "dia_semana",
        ]
        for col in text_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
                # Mantener formato original pero limpiar espacios

        return df
    except Exception as e:
        st.error(f"Error técnico al procesar el archivo: {e}")
        return pd.DataFrame()


def export_to_excel(df_dict, filename="reporte_atenciones.xlsx"):
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
    data_path = os.path.join(current_dir, "..", "data", "atenciones.csv")

    # --- Encabezado del Reporte ---
    st.title("Análisis Integral de Atenciones")
    st.markdown("### Sistema de seguimiento y análisis de productividad por funcionario y sede")
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

        # Filtro Sede
        lista_sedes = ["TODAS"] + sorted([s for s in df["sede"].unique().tolist() if pd.notna(s) and s != "NAN"])
        filtro_sede = st.selectbox("Seleccionar Sede", lista_sedes)

        # Filtro Funcionario
        lista_funcionarios = ["TODOS"] + sorted([f for f in df["funcionario_atendio"].unique().tolist() if pd.notna(f) and f != "NAN"])
        filtro_funcionario = st.selectbox("Seleccionar Funcionario", lista_funcionarios)

        # Filtro Servicio
        lista_servicios = ["TODOS"] + sorted([s for s in df["servicio"].unique().tolist() if pd.notna(s) and s != "NAN"])
        filtro_servicio = st.selectbox("Seleccionar Servicio", lista_servicios)

        # Filtro Área
        lista_areas = ["TODAS"] + sorted([a for a in df["area"].unique().tolist() if pd.notna(a) and a != "NAN"])
        filtro_area = st.selectbox("Seleccionar Área", lista_areas)

        # Filtro Estado
        lista_estados = ["TODOS"] + sorted([e for e in df["estado"].unique().tolist() if pd.notna(e) and e != "NAN"])
        filtro_estado = st.selectbox("Seleccionar Estado", lista_estados)

    # Aplicar filtros
    df_filtrado = df.copy()
    if filtro_sede != "TODAS":
        df_filtrado = df_filtrado[df_filtrado["sede"] == filtro_sede]
    if filtro_funcionario != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["funcionario_atendio"] == filtro_funcionario]
    if filtro_servicio != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["servicio"] == filtro_servicio]
    if filtro_area != "TODAS":
        df_filtrado = df_filtrado[df_filtrado["area"] == filtro_area]
    if filtro_estado != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["estado"] == filtro_estado]

    # --- INDICADORES CLAVE (KPIs) ---
    col1, col2, col3, col4, col5 = st.columns(5)

    total_casos = df_filtrado["cantidad_casos"].sum()

    # Cálculo de promedio ponderado real
    if total_casos > 0:
        tiempo_global_min = (
            df_filtrado["tiempo_promedio_num"] * df_filtrado["cantidad_casos"]
        ).sum() / total_casos
        tiempo_total_horas = df_filtrado["tiempo_total_dedicado_num"].sum() / 60
    else:
        tiempo_global_min = 0
        tiempo_total_horas = 0

    funcionarios_activos = df_filtrado["funcionario_atendio"].nunique()
    sedes_activas = df_filtrado["sede"].nunique()
    servicios_unicos = df_filtrado["servicio"].nunique()

    col1.metric("Total Atenciones", f"{total_casos:,.0f}")
    col2.metric("Tiempo Promedio", f"{tiempo_global_min:.1f} min")
    col3.metric("Tiempo Total", f"{tiempo_total_horas:.1f} hrs")
    col4.metric("Funcionarios", funcionarios_activos)
    col5.metric("Sedes Activas", sedes_activas)

    st.markdown("---")

    # --- CUERPO DEL ANÁLISIS CON PESTAÑAS ---
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        [
            "Por Funcionario y Sede",
            "Servicios Solicitados",
            "Análisis por Sede",
            "Análisis por Área",
            "Estados y Calidad",
            "Resumen Ejecutivo"
        ]
    )

    # --- TAB 1: POR FUNCIONARIO Y SEDE ---
    with tab1:
        st.subheader("Atenciones por Funcionario y Sede")
        st.markdown("Análisis detallado de la productividad de cada funcionario en cada sede")

        # Agrupar por funcionario y sede
        df_funcionario_sede = (
            df_filtrado.groupby(["funcionario_atendio", "sede"])
            .agg(
                {
                    "cantidad_casos": "sum",
                    "tiempo_total_dedicado_num": "sum",
                    "servicio": lambda x: ", ".join(str(s) for s in x.unique()[:5] if pd.notna(s)),
                    "estado": lambda x: x.value_counts().index[0] if len(x) > 0 else "",
                }
            )
            .reset_index()
        )

        # Calcular tiempo promedio real (promedio ponderado)
        df_funcionario_sede["tiempo_promedio_real"] = (
            df_funcionario_sede["tiempo_total_dedicado_num"] / 
            df_funcionario_sede["cantidad_casos"]
        )
        df_funcionario_sede["tiempo_total_horas"] = (
            df_funcionario_sede["tiempo_total_dedicado_num"] / 60
        )

        # Ordenar por cantidad de casos
        df_funcionario_sede = df_funcionario_sede.sort_values("cantidad_casos", ascending=False)

        # Mostrar tabla completa
        st.markdown("#### Tabla Completa de Funcionarios por Sede")
        display_df = df_funcionario_sede[[
            "funcionario_atendio", "sede", "cantidad_casos", 
            "tiempo_promedio_real", "tiempo_total_horas", "servicio", "estado"
        ]].copy()
        display_df.columns = [
            "Funcionario", "Sede", "Total Casos", 
            "Tiempo Promedio (min)", "Tiempo Total (hrs)", "Servicios Principales", "Estado Más Común"
        ]
        display_df["Tiempo Promedio (min)"] = display_df["Tiempo Promedio (min)"].round(2)
        display_df["Tiempo Total (hrs)"] = display_df["Tiempo Total (hrs)"].round(2)
        st.dataframe(display_df, use_container_width=True, height=400)

        # Gráfico de barras: Top funcionarios por sede
        st.markdown("#### Top 15 Funcionarios por Volumen de Atenciones")
        top_funcionarios = df_funcionario_sede.head(15)
        fig_bar = px.bar(
            top_funcionarios,
            x="cantidad_casos",
            y="funcionario_atendio",
            color="sede",
            orientation="h",
            labels={
                "cantidad_casos": "Total de Casos",
                "funcionario_atendio": "Funcionario",
                "sede": "Sede"
            },
            title="Top 15 Funcionarios por Volumen de Atenciones",
        )
        fig_bar.update_layout(height=600)
        st.plotly_chart(fig_bar, use_container_width=True)

        # Gráfico de dispersión: Volumen vs Tiempo por Sede
        st.markdown("#### Análisis de Eficiencia: Volumen vs Tiempo Promedio")
        fig_scatter = px.scatter(
            df_funcionario_sede,
            x="cantidad_casos",
            y="tiempo_promedio_real",
            size="tiempo_total_horas",
            color="sede",
            hover_name="funcionario_atendio",
            hover_data=["sede", "cantidad_casos", "tiempo_promedio_real"],
            labels={
                "cantidad_casos": "Volumen de Atenciones",
                "tiempo_promedio_real": "Tiempo Promedio (Minutos)",
                "sede": "Sede",
                "tiempo_total_horas": "Tiempo Total (Horas)"
            },
            title="Matriz de Productividad: Volumen vs Velocidad por Sede",
        )
        # Líneas promedio
        mean_x = df_funcionario_sede["cantidad_casos"].mean()
        mean_y = df_funcionario_sede["tiempo_promedio_real"].mean()
        fig_scatter.add_hline(
            y=mean_y, line_dash="dash", line_color="gray", annotation_text="Promedio Tiempo"
        )
        fig_scatter.add_vline(
            x=mean_x, line_dash="dash", line_color="gray", annotation_text="Promedio Volumen"
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    # --- TAB 2: SERVICIOS SOLICITADOS ---
    with tab2:
        st.subheader("Análisis de Servicios Solicitados")
        st.markdown("Desglose completo de todos los servicios solicitados")

        # Análisis por servicio
        df_servicios = (
            df_filtrado.groupby("servicio")
            .agg(
                {
                    "cantidad_casos": "sum",
                    "tiempo_total_dedicado_num": "sum",
                    "funcionario_atendio": "nunique",
                    "sede": lambda x: ", ".join(x.unique()[:3]),
                }
            )
            .reset_index()
        )
        df_servicios["tiempo_promedio"] = (
            df_servicios["tiempo_total_dedicado_num"] / df_servicios["cantidad_casos"]
        )
        df_servicios["tiempo_total_horas"] = df_servicios["tiempo_total_dedicado_num"] / 60
        df_servicios = df_servicios.sort_values("cantidad_casos", ascending=False)

        # Tabla completa de servicios
        st.markdown("#### Todos los Servicios Solicitados")
        display_servicios = df_servicios[[
            "servicio", "cantidad_casos", "tiempo_promedio", 
            "tiempo_total_horas", "funcionario_atendio", "sede"
        ]].copy()
        display_servicios.columns = [
            "Servicio", "Total Casos", "Tiempo Promedio (min)", 
            "Tiempo Total (hrs)", "Funcionarios Involucrados", "Sedes"
        ]
        display_servicios["Tiempo Promedio (min)"] = display_servicios["Tiempo Promedio (min)"].round(2)
        display_servicios["Tiempo Total (hrs)"] = display_servicios["Tiempo Total (hrs)"].round(2)
        st.dataframe(display_servicios, use_container_width=True, height=400)

        # Gráfico de servicios
        st.markdown("#### Distribución de Servicios por Volumen")
        fig_servicios = px.bar(
            df_servicios.head(20),
            x="cantidad_casos",
            y="servicio",
            orientation="h",
            color="tiempo_promedio",
            color_continuous_scale="Viridis",
            labels={
                "cantidad_casos": "Total de Casos",
                "servicio": "Servicio",
                "tiempo_promedio": "Tiempo Promedio (min)"
            },
            title="Top 20 Servicios por Volumen de Atenciones",
        )
        fig_servicios.update_layout(height=600)
        st.plotly_chart(fig_servicios, use_container_width=True)

        # Gráfico de torta: Distribución porcentual
        st.markdown("#### Distribución Porcentual de Servicios")
        fig_pie_servicios = px.pie(
            df_servicios,
            values="cantidad_casos",
            names="servicio",
            title="Distribución de Atenciones por Tipo de Servicio",
        )
        fig_pie_servicios.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig_pie_servicios, use_container_width=True)

    # --- TAB 3: ANÁLISIS POR SEDE ---
    with tab3:
        st.subheader("Análisis Detallado por Sede")
        
        # Agrupar por sede
        df_sede = (
            df_filtrado.groupby("sede")
            .agg(
                {
                    "cantidad_casos": "sum",
                    "tiempo_total_dedicado_num": "sum",
                    "funcionario_atendio": "nunique",
                    "servicio": "nunique",
                    "area": "nunique",
                }
            )
            .reset_index()
        )
        df_sede["tiempo_promedio"] = (
            df_sede["tiempo_total_dedicado_num"] / df_sede["cantidad_casos"]
        )
        df_sede["tiempo_total_horas"] = df_sede["tiempo_total_dedicado_num"] / 60
        df_sede = df_sede.sort_values("cantidad_casos", ascending=False)

        # Tabla de sedes
        st.markdown("#### Resumen por Sede")
        display_sede = df_sede[[
            "sede", "cantidad_casos", "funcionario_atendio", 
            "servicio", "tiempo_promedio", "tiempo_total_horas"
        ]].copy()
        display_sede.columns = [
            "Sede", "Total Casos", "Funcionarios", 
            "Servicios Únicos", "Tiempo Promedio (min)", "Tiempo Total (hrs)"
        ]
        display_sede["Tiempo Promedio (min)"] = display_sede["Tiempo Promedio (min)"].round(2)
        display_sede["Tiempo Total (hrs)"] = display_sede["Tiempo Total (hrs)"].round(2)
        st.dataframe(display_sede, use_container_width=True)

        # Gráficos
        col1, col2 = st.columns(2)

        with col1:
            fig_sede_casos = px.bar(
                df_sede,
                x="sede",
                y="cantidad_casos",
                labels={"sede": "Sede", "cantidad_casos": "Total de Casos"},
                title="Carga Laboral por Sede",
            )
            st.plotly_chart(fig_sede_casos, use_container_width=True)

        with col2:
            fig_sede_funcionarios = px.bar(
                df_sede,
                x="sede",
                y="funcionario_atendio",
                labels={"sede": "Sede", "funcionario_atendio": "Número de Funcionarios"},
                title="Funcionarios Activos por Sede",
            )
            st.plotly_chart(fig_sede_funcionarios, use_container_width=True)

        # Detalle por sede: Funcionarios en cada sede
        st.markdown("#### Funcionarios por Sede")
        for sede in df_sede["sede"].head(10):
            st.markdown(f"**{sede}**")
            df_sede_func = (
                df_filtrado[df_filtrado["sede"] == sede]
                .groupby("funcionario_atendio")
                .agg({"cantidad_casos": "sum", "tiempo_total_dedicado_num": "sum"})
                .reset_index()
            )
            df_sede_func["tiempo_promedio"] = (
                df_sede_func["tiempo_total_dedicado_num"] / df_sede_func["cantidad_casos"]
            )
            df_sede_func = df_sede_func.sort_values("cantidad_casos", ascending=False)
            df_sede_func.columns = ["Funcionario", "Total Casos", "Tiempo Total (min)", "Tiempo Promedio (min)"]
            df_sede_func["Tiempo Promedio (min)"] = df_sede_func["Tiempo Promedio (min)"].round(2)
            st.dataframe(df_sede_func, use_container_width=True, hide_index=True)
            st.markdown("---")

    # --- TAB 4: ANÁLISIS POR ÁREA ---
    with tab4:
        st.subheader("Análisis por Área")
        
        df_area = (
            df_filtrado.groupby("area")
            .agg(
                {
                    "cantidad_casos": "sum",
                    "tiempo_total_dedicado_num": "sum",
                    "funcionario_atendio": "nunique",
                    "servicio": "nunique",
                }
            )
            .reset_index()
        )
        df_area["tiempo_promedio"] = (
            df_area["tiempo_total_dedicado_num"] / df_area["cantidad_casos"]
        )
        df_area["tiempo_total_horas"] = df_area["tiempo_total_dedicado_num"] / 60
        df_area = df_area.sort_values("cantidad_casos", ascending=False)

        st.markdown("#### Resumen por Área")
        display_area = df_area[[
            "area", "cantidad_casos", "funcionario_atendio", 
            "servicio", "tiempo_promedio", "tiempo_total_horas"
        ]].copy()
        display_area.columns = [
            "Área", "Total Casos", "Funcionarios", 
            "Servicios Únicos", "Tiempo Promedio (min)", "Tiempo Total (hrs)"
        ]
        display_area["Tiempo Promedio (min)"] = display_area["Tiempo Promedio (min)"].round(2)
        display_area["Tiempo Total (hrs)"] = display_area["Tiempo Total (hrs)"].round(2)
        st.dataframe(display_area, use_container_width=True)

        fig_area = px.bar(
            df_area,
            x="area",
            y="tiempo_promedio",
            color="cantidad_casos",
            color_continuous_scale="Reds",
            labels={
                "area": "Área",
                "tiempo_promedio": "Tiempo Promedio (Minutos)",
                "cantidad_casos": "Total Casos"
            },
            title="Tiempo Promedio de Atención por Área",
        )
        st.plotly_chart(fig_area, use_container_width=True)

    # --- TAB 5: ESTADOS Y CALIDAD ---
    with tab5:
        st.subheader("Análisis de Estados y Calidad de Atención")
        
        col1, col2 = st.columns(2)

        with col1:
            df_estado = (
                df_filtrado.groupby("estado")["cantidad_casos"].sum().reset_index()
            )
            fig_pie = px.pie(
                df_estado,
                values="cantidad_casos",
                names="estado",
                title="Distribución por Estado de Atención",
            )
            fig_pie.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig_pie, use_container_width=True)

        with col2:
            # Calcular tiempo promedio ponderado por población
            df_poblacion = df_filtrado.groupby("poblacion").agg({
                "cantidad_casos": "sum",
                "tiempo_total_dedicado_num": "sum",
            }).reset_index()
            df_poblacion["tiempo_promedio"] = (
                df_poblacion["tiempo_total_dedicado_num"] / df_poblacion["cantidad_casos"]
            )
            df_poblacion = df_poblacion.sort_values("cantidad_casos", ascending=False).head(10)
            fig_pob = px.bar(
                df_poblacion,
                x="cantidad_casos",
                y="poblacion",
                orientation="h",
                labels={"cantidad_casos": "Total Casos", "poblacion": "Tipo de Población"},
                title="Atenciones por Tipo de Población",
            )
            st.plotly_chart(fig_pob, use_container_width=True)

        # Tabla de estados
        st.markdown("#### Detalle por Estado")
        df_estado_detalle = (
            df_filtrado.groupby("estado")
            .agg({
                "cantidad_casos": "sum",
                "tiempo_total_dedicado_num": "sum",
            })
            .reset_index()
        )
        df_estado_detalle["tiempo_promedio"] = (
            df_estado_detalle["tiempo_total_dedicado_num"] / 
            df_estado_detalle["cantidad_casos"]
        )
        df_estado_detalle = df_estado_detalle[["estado", "cantidad_casos", "tiempo_promedio"]]
        df_estado_detalle.columns = ["Estado", "Total Casos", "Tiempo Promedio (min)"]
        df_estado_detalle["Tiempo Promedio (min)"] = df_estado_detalle["Tiempo Promedio (min)"].round(2)
        st.dataframe(df_estado_detalle, use_container_width=True)

    # --- TAB 6: RESUMEN EJECUTIVO ---
    with tab6:
        st.subheader("Resumen Ejecutivo")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Top 10 Funcionarios por Productividad")
            top_func = (
                df_filtrado.groupby("funcionario_atendio")
                .agg({"cantidad_casos": "sum", "tiempo_total_dedicado_num": "sum"})
                .reset_index()
            )
            top_func["tiempo_promedio"] = (
                top_func["tiempo_total_dedicado_num"] / top_func["cantidad_casos"]
            )
            top_func = top_func.sort_values("cantidad_casos", ascending=False).head(10)
            top_func.columns = ["Funcionario", "Total Casos", "Tiempo Total (min)", "Tiempo Promedio (min)"]
            top_func["Tiempo Promedio (min)"] = top_func["Tiempo Promedio (min)"].round(2)
            st.dataframe(top_func, use_container_width=True, hide_index=True)

        with col2:
            st.markdown("#### Top 10 Servicios Más Solicitados")
            top_serv = (
                df_filtrado.groupby("servicio")["cantidad_casos"]
                .sum()
                .reset_index()
                .sort_values("cantidad_casos", ascending=False)
                .head(10)
            )
            top_serv.columns = ["Servicio", "Total Casos"]
            st.dataframe(top_serv, use_container_width=True, hide_index=True)

    # --- EXPORTACIÓN A EXCEL ---
    st.markdown("---")
    st.subheader("Exportar Reportes")

    # Preparar datos para exportación
    export_data = {}
    
    # Limpiar columnas numéricas auxiliares para exportación
    cols_to_export = [c for c in df_filtrado.columns if not c.endswith("_num")]
    export_data["Datos Completos"] = df_filtrado[cols_to_export].copy()
    
    # Agregar hojas adicionales
    if not df_funcionario_sede.empty:
        export_data["Funcionarios por Sede"] = df_funcionario_sede.copy()
    if not df_servicios.empty:
        export_data["Servicios"] = df_servicios.copy()
    if not df_sede.empty:
        export_data["Resumen por Sede"] = df_sede.copy()
    if not df_area.empty:
        export_data["Resumen por Área"] = df_area.copy()

    # Botón de descarga
    excel_data = export_to_excel(export_data, "reporte_atenciones.xlsx")
    
    st.download_button(
        label="Descargar Reporte Completo (Excel)",
        data=excel_data,
        file_name="reporte_atenciones.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
