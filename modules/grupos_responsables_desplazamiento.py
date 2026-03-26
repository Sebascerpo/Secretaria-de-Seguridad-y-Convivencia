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

    # Identificar años disponibles
    years = sorted(df["ano_declara"].unique(), reverse=False)
    
    if not years:
        st.info(f"No hay datos registrados para {tipo_texto} en el dataset actual.")
        return
    
    # Filtrar solo desplazamiento
    df_desplaz = df[df["hecho_victimizante"] == "Desplazamiento forzado"].copy()

    if len(df_desplaz) == 0:
        st.warning(
            "No hay registros de desplazamiento forzado para este tipo de origen."
        )
        return

    # Colores para los años
    colors = ["#dc2626", "#ea580c", "#f97316", "#fbbf24"]

    # Crear columnas dinámicamente
    cols = st.columns(len(years))

    for i, year in enumerate(years):
        with cols[i]:
            st.subheader(f"Grupos Responsables {year}")
            
            df_year = df_desplaz[df_desplaz["ano_declara"] == year].copy()
            total_casos_year = len(df_year)
            
            st.caption(f"Filtro: SOLO DESPLAZAMIENTO | Total casos: {total_casos_year:,}")

            if total_casos_year > 0:
                grupos_year = df_year["presunto_responsable"].value_counts().head(20)
                grupos_year_df = pd.DataFrame(
                    {
                        "Grupo": grupos_year.index,
                        "Casos": grupos_year.values,
                        "Porcentaje": (grupos_year.values / total_casos_year * 100).round(1),
                    }
                )

                fig = go.Figure()
                fig.add_trace(
                    go.Bar(
                        y=grupos_year_df["Grupo"],
                        x=grupos_year_df["Casos"],
                        orientation="h",
                        text=[
                            f"{val:,}<br>({pct}%)"
                            for val, pct in zip(
                                grupos_year_df["Casos"],
                                grupos_year_df["Porcentaje"],
                            )
                        ],
                        textposition="outside",
                        marker_color=colors[i % len(colors)],
                        hovertemplate="%{y}<br>Casos: %{x:,}<extra></extra>",
                    )
                )
                fig.update_layout(
                    height=700,
                    showlegend=False,
                    yaxis={"categoryorder": "total ascending"},
                    xaxis_title="Cantidad de Casos",
                    margin=dict(r=100, l=200, t=30, b=50),
                )
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(grupos_year_df, use_container_width=True, hide_index=True)
            else:
                st.info(f"No hay datos de desplazamiento para {year}")
