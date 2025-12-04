import streamlit as st
import pandas as pd
import plotly.graph_objects as go


def render(df, tipo_texto, ubicacion_texto):
    st.header(f"Grupos Responsables - {tipo_texto}")
    st.caption(f"Ubicación: {ubicacion_texto}")
    st.caption(
        "Incluye: TODOS los hechos victimizantes (Desplazamiento, Homicidio, Amenaza, etc.)"
    )

    # Separar por años
    df_2024 = df[df["ano_declara"] == 2024].copy()
    df_2025 = df[df["ano_declara"] == 2025].copy()

    total_personas_2024 = len(df_2024)
    total_personas_2025 = len(df_2025)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Grupos Responsables 2024")
        st.caption(f"Filtro: TODOS LOS MOTIVOS | Total casos: {total_personas_2024:,}")

        grupos_2024 = df_2024["presunto_responsable"].value_counts().head(20)
        grupos_2024_df = pd.DataFrame(
            {
                "Grupo": grupos_2024.index,
                "Casos": grupos_2024.values,
                "Porcentaje": (grupos_2024.values / total_personas_2024 * 100).round(1),
            }
        )

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                y=grupos_2024_df["Grupo"],
                x=grupos_2024_df["Casos"],
                orientation="h",
                text=[
                    f"{val:,}<br>({pct}%)"
                    for val, pct in zip(
                        grupos_2024_df["Casos"], grupos_2024_df["Porcentaje"]
                    )
                ],
                textposition="outside",
                marker_color="#7c3aed",
                hovertemplate="%{y}<br>Casos: %{x:,}<extra></extra>",
            )
        )
        fig.update_layout(
            height=700,
            showlegend=False,
            yaxis={"categoryorder": "total ascending"},
            xaxis_title="Cantidad de Casos",
            margin=dict(r=150, l=250, t=30, b=50),
        )
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(grupos_2024_df, use_container_width=True, hide_index=True)

    with col2:
        st.subheader("Grupos Responsables 2025")
        st.caption(f"Filtro: TODOS LOS MOTIVOS | Total casos: {total_personas_2025:,}")

        grupos_2025 = df_2025["presunto_responsable"].value_counts().head(20)
        grupos_2025_df = pd.DataFrame(
            {
                "Grupo": grupos_2025.index,
                "Casos": grupos_2025.values,
                "Porcentaje": (grupos_2025.values / total_personas_2025 * 100).round(1),
            }
        )

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                y=grupos_2025_df["Grupo"],
                x=grupos_2025_df["Casos"],
                orientation="h",
                text=[
                    f"{val:,}<br>({pct}%)"
                    for val, pct in zip(
                        grupos_2025_df["Casos"], grupos_2025_df["Porcentaje"]
                    )
                ],
                textposition="outside",
                marker_color="#6366f1",
                hovertemplate="%{y}<br>Casos: %{x:,}<extra></extra>",
            )
        )
        fig.update_layout(
            height=700,
            showlegend=False,
            yaxis={"categoryorder": "total ascending"},
            xaxis_title="Cantidad de Casos",
            margin=dict(r=150, l=250, t=30, b=50),
        )
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(grupos_2025_df, use_container_width=True, hide_index=True)
