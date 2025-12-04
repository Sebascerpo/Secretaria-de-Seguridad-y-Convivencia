import streamlit as st
import pandas as pd
import plotly.express as px


def render(df, tipo_texto, ubicacion_texto):
    st.header(f"Análisis Demográfico - {tipo_texto}")
    st.caption(f"Ubicación: {ubicacion_texto}")
    st.caption("Incluye: Todos los hechos victimizantes")

    # Separar por años
    df_2024 = df[df["ano_declara"] == 2024].copy()
    df_2025 = df[df["ano_declara"] == 2025].copy()

    # GÉNERO
    st.subheader("Análisis por Género")
    st.caption("Filtro: TODOS LOS MOTIVOS")

    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        st.write("**Año 2024**")
        gender_2024 = df_2024["genero"].value_counts()
        gender_2024_df = pd.DataFrame(
            {"Género": gender_2024.index, "Cantidad": gender_2024.values}
        )
        st.dataframe(gender_2024_df, use_container_width=True, hide_index=True)

    with col2:
        st.write("**Año 2025**")
        gender_2025 = df_2025["genero"].value_counts()
        gender_2025_df = pd.DataFrame(
            {"Género": gender_2025.index, "Cantidad": gender_2025.values}
        )
        st.dataframe(gender_2025_df, use_container_width=True, hide_index=True)

    with col3:
        gender_data = pd.DataFrame(
            {
                "Género": list(gender_2024.index) + list(gender_2025.index),
                "Cantidad": list(gender_2024.values) + list(gender_2025.values),
                "Año": ["2024"] * len(gender_2024) + ["2025"] * len(gender_2025),
            }
        )

        fig = px.bar(
            gender_data,
            x="Género",
            y="Cantidad",
            color="Año",
            barmode="group",
            color_discrete_map={"2024": "#dc2626", "2025": "#ea580c"},
            text="Cantidad",
        )
        fig.update_traces(texttemplate="%{text:,}", textposition="outside")
        fig.update_layout(height=400, margin=dict(t=50))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # EDAD
    st.subheader("Análisis por Grupos de Edad")
    st.caption("Filtro: TODOS LOS MOTIVOS")

    df_2024_edad = df_2024[df_2024["edad"].notna()].copy()
    df_2024_edad["grupo_edad"] = pd.cut(
        df_2024_edad["edad"],
        bins=[0, 17, 28, 40, 60, 150],
        labels=["0-17", "18-28", "29-40", "41-60", "60+"],
    )

    edad_counts_2024 = df_2024_edad["grupo_edad"].value_counts().sort_index()

    df_2025_edad = df_2025[df_2025["edad"].notna()].copy()
    df_2025_edad["grupo_edad"] = pd.cut(
        df_2025_edad["edad"],
        bins=[0, 17, 28, 40, 60, 150],
        labels=["0-17", "18-28", "29-40", "41-60", "60+"],
    )

    edad_counts_2025 = df_2025_edad["grupo_edad"].value_counts().sort_index()

    edad_df = pd.DataFrame(
        {
            "Grupo de Edad": list(edad_counts_2024.index)
            + list(edad_counts_2025.index),
            "Cantidad": list(edad_counts_2024.values) + list(edad_counts_2025.values),
            "Año": ["2024"] * len(edad_counts_2024) + ["2025"] * len(edad_counts_2025),
        }
    )

    fig = px.bar(
        edad_df,
        x="Grupo de Edad",
        y="Cantidad",
        color="Año",
        barmode="group",
        color_discrete_map={"2024": "#059669", "2025": "#10b981"},
        text="Cantidad",
    )
    fig.update_traces(texttemplate="%{text:,}", textposition="outside")
    fig.update_layout(height=450, margin=dict(t=50))
    st.plotly_chart(fig, use_container_width=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Edad Promedio 2024", f"{df_2024_edad['edad'].mean():.1f} años")
    with col2:
        st.metric("Edad Mediana 2024", f"{df_2024_edad['edad'].median():.0f} años")
    with col3:
        st.metric("Edad Promedio 2025", f"{df_2025_edad['edad'].mean():.1f} años")
    with col4:
        st.metric("Edad Mediana 2025", f"{df_2025_edad['edad'].median():.0f} años")

    st.markdown("---")

    # ENFOQUE DIFERENCIAL
    st.subheader("Enfoque Diferencial")
    st.caption("Filtro: TODOS LOS MOTIVOS")

    enfoque_2024 = df_2024["enfoque_diferencial"].value_counts().head(10)
    enfoque_2025 = df_2025["enfoque_diferencial"].value_counts().head(10)

    enfoque_data = pd.DataFrame(
        {
            "Enfoque": list(enfoque_2024.index) + list(enfoque_2025.index),
            "Cantidad": list(enfoque_2024.values) + list(enfoque_2025.values),
            "Año": ["2024"] * len(enfoque_2024) + ["2025"] * len(enfoque_2025),
        }
    )

    fig = px.bar(
        enfoque_data,
        x="Enfoque",
        y="Cantidad",
        color="Año",
        barmode="group",
        color_discrete_map={"2024": "#dc2626", "2025": "#ea580c"},
        text="Cantidad",
    )
    fig.update_traces(texttemplate="%{text:,}", textposition="outside")
    fig.update_layout(height=400, margin=dict(t=50, b=100))
    fig.update_xaxes(tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)
