import streamlit as st
import pandas as pd
import plotly.graph_objects as go


def render(df, tipo_texto, ubicacion_texto):
    st.header(f"Análisis por Ubicación - {tipo_texto}")
    st.caption(f"Ubicación: {ubicacion_texto}")
    st.caption("Incluye: Todos los hechos victimizantes")

    # Separar por años
    df_2024 = df[df["ano_declara"] == 2024].copy()
    df_2025 = df[df["ano_declara"] == 2025].copy()

    total_declaraciones_2024 = df_2024["id_atencion"].nunique()
    total_declaraciones_2025 = df_2025["id_atencion"].nunique()

    # Determinar si es municipio o barrio
    if tipo_texto == "INTERMUNICIPAL":
        campo_ubicacion = "municipio_procede"
        texto_ubicacion = "Municipio"
    else:
        campo_ubicacion = "barrio_procede"
        texto_ubicacion = "Barrio"

    col1, col2 = st.columns(2)

    with col1:
        st.subheader(f"Top 15 {texto_ubicacion}s 2024")
        st.caption("Filtro: TODOS LOS MOTIVOS")

        ubicacion_2024 = (
            df_2024.groupby(campo_ubicacion)["id_atencion"]
            .nunique()
            .sort_values(ascending=False)
            .head(15)
        )
        ubicacion_2024_df = pd.DataFrame(
            {
                texto_ubicacion: ubicacion_2024.index,
                "Declaraciones": ubicacion_2024.values,
                "Porcentaje": (
                    ubicacion_2024.values / total_declaraciones_2024 * 100
                ).round(1),
            }
        )

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                y=ubicacion_2024_df[texto_ubicacion],
                x=ubicacion_2024_df["Declaraciones"],
                orientation="h",
                text=[
                    f"{val:,}<br>({pct}%)"
                    for val, pct in zip(
                        ubicacion_2024_df["Declaraciones"],
                        ubicacion_2024_df["Porcentaje"],
                    )
                ],
                textposition="outside",
                marker_color="#dc2626",
                hovertemplate="%{y}<br>Declaraciones: %{x:,}<extra></extra>",
            )
        )
        fig.update_layout(
            height=600,
            showlegend=False,
            yaxis={"categoryorder": "total ascending"},
            xaxis_title="Número de Declaraciones",
            margin=dict(r=150, l=150, t=30, b=50),
        )
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(ubicacion_2024_df, use_container_width=True, hide_index=True)

    with col2:
        st.subheader(f"Top 15 {texto_ubicacion}s 2025")
        st.caption("Filtro: TODOS LOS MOTIVOS")

        ubicacion_2025 = (
            df_2025.groupby(campo_ubicacion)["id_atencion"]
            .nunique()
            .sort_values(ascending=False)
            .head(15)
        )
        ubicacion_2025_df = pd.DataFrame(
            {
                texto_ubicacion: ubicacion_2025.index,
                "Declaraciones": ubicacion_2025.values,
                "Porcentaje": (
                    ubicacion_2025.values / total_declaraciones_2025 * 100
                ).round(1),
            }
        )

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                y=ubicacion_2025_df[texto_ubicacion],
                x=ubicacion_2025_df["Declaraciones"],
                orientation="h",
                text=[
                    f"{val:,}<br>({pct}%)"
                    for val, pct in zip(
                        ubicacion_2025_df["Declaraciones"],
                        ubicacion_2025_df["Porcentaje"],
                    )
                ],
                textposition="outside",
                marker_color="#ea580c",
                hovertemplate="%{y}<br>Declaraciones: %{x:,}<extra></extra>",
            )
        )
        fig.update_layout(
            height=600,
            showlegend=False,
            yaxis={"categoryorder": "total ascending"},
            xaxis_title="Número de Declaraciones",
            margin=dict(r=150, l=150, t=30, b=50),
        )
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(ubicacion_2025_df, use_container_width=True, hide_index=True)
