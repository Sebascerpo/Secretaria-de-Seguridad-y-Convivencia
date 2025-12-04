import streamlit as st
import pandas as pd
import plotly.express as px
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
    """Ejecuta el dashboard de mapas"""
    st.title("🗺️ Visualización Geográfica")
    st.markdown("Dashboard de mapas y distribución geográfica")

    # Cargar datos
    df = load_data()
    if df is None:
        return

    st.markdown("---")

    # Análisis intermunicipal
    st.subheader("Distribución por Municipios (INTERMUNICIPAL)")

    df_inter = df[df["origen_hecho"] == "INTERMUNICIPAL"].copy()

    if len(df_inter) > 0:
        # Agrupar por municipio
        municipios = (
            df_inter.groupby("municipio_procede")
            .agg({"id_atencion": "nunique", "documento_anonimizado": "count"})
            .reset_index()
        )
        municipios.columns = ["Municipio", "Declaraciones", "Personas"]
        municipios = municipios.sort_values("Personas", ascending=False).head(20)

        # Gráfico de árbol
        fig = px.treemap(
            municipios,
            path=["Municipio"],
            values="Personas",
            title="Mapa de Árbol: Distribución por Municipios (Top 20)",
            color="Personas",
            color_continuous_scale="Reds",
        )
        fig.update_layout(height=600)
        st.plotly_chart(fig, use_container_width=True)

        # Tabla
        st.dataframe(municipios, use_container_width=True, hide_index=True)
    else:
        st.info("No hay datos intermunicipales disponibles")

    st.markdown("---")

    # Análisis intraurbano
    st.subheader("Distribución por Barrios (INTRAURBANO)")

    df_intra = df[df["origen_hecho"] == "INTRAURBANO"].copy()

    if len(df_intra) > 0:
        # Agrupar por barrio
        barrios = (
            df_intra.groupby("barrio_procede")
            .agg({"id_atencion": "nunique", "documento_anonimizado": "count"})
            .reset_index()
        )
        barrios.columns = ["Barrio", "Declaraciones", "Personas"]
        barrios = barrios.sort_values("Personas", ascending=False).head(20)

        # Gráfico de árbol
        fig = px.treemap(
            barrios,
            path=["Barrio"],
            values="Personas",
            title="Mapa de Árbol: Distribución por Barrios (Top 20)",
            color="Personas",
            color_continuous_scale="Oranges",
        )
        fig.update_layout(height=600)
        st.plotly_chart(fig, use_container_width=True)

        # Tabla
        st.dataframe(barrios, use_container_width=True, hide_index=True)

        st.markdown("---")

        # Por comuna
        st.subheader("Distribución por Comunas")

        comunas = df_intra.groupby("comuna_procede").size().reset_index(name="Casos")
        comunas = comunas.sort_values("Casos", ascending=False)

        fig = px.bar(
            comunas,
            x="comuna_procede",
            y="Casos",
            labels={"comuna_procede": "Comuna", "Casos": "Número de Casos"},
            color="Casos",
            color_continuous_scale="Reds",
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("No hay datos intraurbanos disponibles")

    st.markdown("---")
    st.info(
        "💡 **Nota:** Para visualización en mapas reales (con coordenadas), necesitarías agregar latitud/longitud a los datos o usar un servicio de geocodificación."
    )
