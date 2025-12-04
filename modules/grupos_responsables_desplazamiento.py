import streamlit as st
import pandas as pd
import plotly.graph_objects as go


def render(df, tipo_texto, ubicacion_texto):
    """
    Renderiza la página de grupos responsables solo para desplazamiento forzado

    Args:
        df: DataFrame con los datos filtrados
        tipo_texto: Tipo de origen (INTERMUNICIPAL o INTRAURBANO)
        ubicacion_texto: Descripción de la ubicación
    """
    st.header(f"Grupos Responsables - Solo Desplazamiento - {tipo_texto}")
    st.caption(f"Ubicación: {ubicacion_texto}")
    st.caption("Filtro: ÚNICAMENTE casos de Desplazamiento Forzado")

    # Filtrar solo desplazamiento
    df_desplaz = df[df["hecho_victimizante"] == "Desplazamiento forzado"].copy()

    df_desplaz_2024 = df_desplaz[df_desplaz["ano_declara"] == 2024].copy()
    df_desplaz_2025 = df_desplaz[df_desplaz["ano_declara"] == 2025].copy()

    desplaz_pers_2024 = len(df_desplaz_2024)
    desplaz_pers_2025 = len(df_desplaz_2025)

    if desplaz_pers_2024 == 0 and desplaz_pers_2025 == 0:
        st.warning(
            "No hay registros de desplazamiento forzado para este tipo de origen."
        )
        return

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Grupos Responsables 2024")
        st.caption(f"Filtro: SOLO DESPLAZAMIENTO | Total casos: {desplaz_pers_2024:,}")

        if desplaz_pers_2024 > 0:
            grupos_despl_2024 = (
                df_desplaz_2024["presunto_responsable"].value_counts().head(20)
            )
            grupos_despl_2024_df = pd.DataFrame(
                {
                    "Grupo": grupos_despl_2024.index,
                    "Casos": grupos_despl_2024.values,
                    "Porcentaje": (
                        grupos_despl_2024.values / desplaz_pers_2024 * 100
                    ).round(1),
                }
            )

            fig = go.Figure()
            fig.add_trace(
                go.Bar(
                    y=grupos_despl_2024_df["Grupo"],
                    x=grupos_despl_2024_df["Casos"],
                    orientation="h",
                    text=[
                        f"{val:,}<br>({pct}%)"
                        for val, pct in zip(
                            grupos_despl_2024_df["Casos"],
                            grupos_despl_2024_df["Porcentaje"],
                        )
                    ],
                    textposition="outside",
                    marker_color="#dc2626",
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
            st.dataframe(
                grupos_despl_2024_df, use_container_width=True, hide_index=True
            )
        else:
            st.info("No hay datos de desplazamiento para 2024")

    with col2:
        st.subheader("Grupos Responsables 2025")
        st.caption(f"Filtro: SOLO DESPLAZAMIENTO | Total casos: {desplaz_pers_2025:,}")

        if desplaz_pers_2025 > 0:
            grupos_despl_2025 = (
                df_desplaz_2025["presunto_responsable"].value_counts().head(20)
            )
            grupos_despl_2025_df = pd.DataFrame(
                {
                    "Grupo": grupos_despl_2025.index,
                    "Casos": grupos_despl_2025.values,
                    "Porcentaje": (
                        grupos_despl_2025.values / desplaz_pers_2025 * 100
                    ).round(1),
                }
            )

            fig = go.Figure()
            fig.add_trace(
                go.Bar(
                    y=grupos_despl_2025_df["Grupo"],
                    x=grupos_despl_2025_df["Casos"],
                    orientation="h",
                    text=[
                        f"{val:,}<br>({pct}%)"
                        for val, pct in zip(
                            grupos_despl_2025_df["Casos"],
                            grupos_despl_2025_df["Porcentaje"],
                        )
                    ],
                    textposition="outside",
                    marker_color="#ea580c",
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
            st.dataframe(
                grupos_despl_2025_df, use_container_width=True, hide_index=True
            )
        else:
            st.info("No hay datos de desplazamiento para 2025")
