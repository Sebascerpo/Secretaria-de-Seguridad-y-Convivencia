import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os


def load_data():
    """Carga los datos desde el CSV"""
    csv_path = "datos.csv"
    if not os.path.exists(csv_path):
        st.error(f"No se encontró el archivo '{csv_path}'")
        return None

    df = pd.read_csv(csv_path)
    df["fecha_declaracion"] = pd.to_datetime(df["fecha_declaracion"])
    df["ano_declara"] = df["fecha_declaracion"].dt.year
    df["mes_declara"] = df["fecha_declaracion"].dt.month
    return df


def run():
    """Ejecuta el dashboard temporal"""
    st.title("📅 Análisis Temporal")
    st.markdown("Dashboard de tendencias y evolución temporal")

    # Cargar datos
    df = load_data()
    if df is None:
        return

    # Filtrar datos
    df_inter = df[df["origen_hecho"] == "INTERMUNICIPAL"].copy()
    df_intra = df[df["origen_hecho"] == "INTRAURBANO"].copy()

    # Selector de origen
    st.markdown("---")
    tipo_analisis = st.radio(
        "Selecciona el tipo de origen:",
        ["INTERMUNICIPAL (Fuera de Medellín)", "INTRAURBANO (Dentro de Medellín)"],
        horizontal=True,
    )

    if "INTERMUNICIPAL" in tipo_analisis:
        df_seleccionado = df_inter.copy()
        tipo_texto = "INTERMUNICIPAL"
    else:
        df_seleccionado = df_intra.copy()
        tipo_texto = "INTRAURBANO"

    st.info(
        f"**Filtro activo:** {tipo_texto} | Total registros: {len(df_seleccionado):,}"
    )

    st.markdown("---")

    # Tendencia mensual
    st.subheader("Tendencia Mensual de Casos")

    df_seleccionado["año_mes"] = (
        df_seleccionado["fecha_declaracion"].dt.to_period("M").astype(str)
    )
    monthly_cases = df_seleccionado.groupby("año_mes").size().reset_index(name="casos")

    fig = px.line(monthly_cases, x="año_mes", y="casos", markers=True)
    fig.update_layout(
        xaxis_title="Periodo",
        yaxis_title="Número de Casos",
        height=400,
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)

    # Comparación por año
    st.markdown("---")
    st.subheader("Comparación por Año y Mes")

    monthly_by_year = (
        df_seleccionado.groupby(["ano_declara", "mes_declara"])
        .size()
        .reset_index(name="casos")
    )

    fig = px.line(
        monthly_by_year,
        x="mes_declara",
        y="casos",
        color="ano_declara",
        markers=True,
        labels={"mes_declara": "Mes", "casos": "Casos", "ano_declara": "Año"},
    )
    fig.update_layout(height=400)
    fig.update_xaxes(tickmode="linear", tick0=1, dtick=1)
    st.plotly_chart(fig, use_container_width=True)

    # Heatmap por mes y año
    st.markdown("---")
    st.subheader("Mapa de Calor: Casos por Mes y Año")

    pivot_data = monthly_by_year.pivot(
        index="mes_declara", columns="ano_declara", values="casos"
    ).fillna(0)

    fig = go.Figure(
        data=go.Heatmap(
            z=pivot_data.values,
            x=pivot_data.columns,
            y=pivot_data.index,
            colorscale="Reds",
            text=pivot_data.values.astype(int),
            texttemplate="%{text}",
            hoverongaps=False,
        )
    )

    fig.update_layout(xaxis_title="Año", yaxis_title="Mes", height=500)

    st.plotly_chart(fig, use_container_width=True)

    # Estadísticas
    st.markdown("---")
    st.subheader("Estadísticas Temporales")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Mes con más casos",
            monthly_by_year.loc[monthly_by_year["casos"].idxmax(), "mes_declara"],
        )
    with col2:
        st.metric(
            "Año con más casos", df_seleccionado["ano_declara"].value_counts().idxmax()
        )
    with col3:
        promedio_mensual = monthly_cases["casos"].mean()
        st.metric("Promedio mensual", f"{promedio_mensual:.0f}")
    with col4:
        total_meses = len(monthly_cases)
        st.metric("Meses con datos", total_meses)
