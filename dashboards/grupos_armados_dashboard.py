import streamlit as st
import pandas as pd
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
    """Ejecuta el dashboard de grupos armados"""
    st.title("🎯 Análisis de Grupos Armados")
    st.markdown("Dashboard de análisis de grupos armados responsables")

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
        ubicacion_texto = "Municipios fuera de Medellín"
    else:
        df_seleccionado = df_intra.copy()
        tipo_texto = "INTRAURBANO"
        ubicacion_texto = "Dentro de Medellín"

    st.info(
        f"**Filtro activo:** {tipo_texto} - {ubicacion_texto} | Total registros: {len(df_seleccionado):,}"
    )

    st.markdown("---")

    # Análisis de grupos por hecho victimizante
    st.subheader("Grupos por Hecho Victimizante")

    # Crear matriz de grupos vs hechos
    grupos_hechos = pd.crosstab(
        df_seleccionado["presunto_responsable"], df_seleccionado["hecho_victimizante"]
    )

    # Top 10 grupos
    top_grupos = grupos_hechos.sum(axis=1).nlargest(10).index
    grupos_hechos_top = grupos_hechos.loc[top_grupos]

    # Top 5 hechos
    top_hechos = grupos_hechos.sum(axis=0).nlargest(5).index
    grupos_hechos_top = grupos_hechos_top[top_hechos]

    # Heatmap
    fig = go.Figure(
        data=go.Heatmap(
            z=grupos_hechos_top.values,
            x=grupos_hechos_top.columns,
            y=grupos_hechos_top.index,
            colorscale="Reds",
            text=grupos_hechos_top.values,
            texttemplate="%{text}",
            textfont={"size": 10},
            hoverongaps=False,
        )
    )

    fig.update_layout(
        title="Matriz: Grupos Armados vs Hechos Victimizantes (Top 10 Grupos, Top 5 Hechos)",
        xaxis_title="Hecho Victimizante",
        yaxis_title="Grupo Armado",
        height=600,
    )

    st.plotly_chart(fig, use_container_width=True)

    # Tabla detallada
    st.dataframe(grupos_hechos_top, use_container_width=True)

    st.markdown("---")

    # Usar módulos existentes
    from modules import grupos_responsables_todos

    grupos_responsables_todos.render(df_seleccionado, tipo_texto, ubicacion_texto)
