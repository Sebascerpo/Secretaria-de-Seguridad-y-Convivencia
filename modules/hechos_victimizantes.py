import streamlit as st
import pandas as pd
import plotly.graph_objects as go


def render(df, tipo_texto, ubicacion_texto):
    st.header(f"Hechos Victimizantes - {tipo_texto}")
    st.caption(f"Ubicación: {ubicacion_texto}")
    st.caption("Muestra: Todos los hechos victimizantes registrados")

    # Separar por años
    df_2024 = df[df["ano_declara"] == 2024].copy()
    df_2025 = df[df["ano_declara"] == 2025].copy()

    total_personas_2024 = len(df_2024)
    total_personas_2025 = len(df_2025)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Hechos Victimizantes 2024")
        st.caption(
            f"Filtro: TODOS LOS MOTIVOS | Total personas: {total_personas_2024:,}"
        )

        hechos_2024 = df_2024["hecho_victimizante"].value_counts().head(20)
        hechos_2024_df = pd.DataFrame(
            {
                "Hecho": hechos_2024.index,
                "Cantidad": hechos_2024.values,
                "Porcentaje": (hechos_2024.values / total_personas_2024 * 100).round(1),
            }
        )

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                y=hechos_2024_df["Hecho"],
                x=hechos_2024_df["Cantidad"],
                orientation="h",
                text=[
                    f"{val:,}<br>({pct}%)"
                    for val, pct in zip(
                        hechos_2024_df["Cantidad"], hechos_2024_df["Porcentaje"]
                    )
                ],
                textposition="outside",
                marker_color="#dc2626",
                hovertemplate="%{y}<br>Cantidad: %{x:,}<extra></extra>",
            )
        )
        fig.update_layout(
            height=700,
            showlegend=False,
            yaxis={"categoryorder": "total ascending"},
            xaxis_title="Cantidad de Personas",
            margin=dict(r=150, l=200, t=30, b=50),
        )
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(hechos_2024_df, use_container_width=True, hide_index=True)

    with col2:
        st.subheader("Hechos Victimizantes 2025")
        st.caption(
            f"Filtro: TODOS LOS MOTIVOS | Total personas: {total_personas_2025:,}"
        )

        hechos_2025 = df_2025["hecho_victimizante"].value_counts().head(20)
        hechos_2025_df = pd.DataFrame(
            {
                "Hecho": hechos_2025.index,
                "Cantidad": hechos_2025.values,
                "Porcentaje": (hechos_2025.values / total_personas_2025 * 100).round(1),
            }
        )

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                y=hechos_2025_df["Hecho"],
                x=hechos_2025_df["Cantidad"],
                orientation="h",
                text=[
                    f"{val:,}<br>({pct}%)"
                    for val, pct in zip(
                        hechos_2025_df["Cantidad"], hechos_2025_df["Porcentaje"]
                    )
                ],
                textposition="outside",
                marker_color="#ea580c",
                hovertemplate="%{y}<br>Cantidad: %{x:,}<extra></extra>",
            )
        )
        fig.update_layout(
            height=700,
            showlegend=False,
            yaxis={"categoryorder": "total ascending"},
            xaxis_title="Cantidad de Personas",
            margin=dict(r=150, l=200, t=30, b=50),
        )
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(hechos_2025_df, use_container_width=True, hide_index=True)
