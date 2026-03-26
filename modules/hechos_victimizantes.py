import streamlit as st
import pandas as pd
import plotly.graph_objects as go


def render(df, tipo_texto, ubicacion_texto):
    st.header(f"Hechos Victimizantes - {tipo_texto}")
    st.caption(f"Ubicación: {ubicacion_texto}")
    st.caption("Muestra: Todos los hechos victimizantes registrados")

    # Identificar años disponibles
    years = sorted(df["ano_declara"].unique(), reverse=False)
    
    if not years:
        st.info(f"No hay datos registrados para {tipo_texto} en el dataset actual.")
        return
    
    # Colores para los años
    colors = ["#dc2626", "#ea580c", "#f97316", "#fbbf24"]

    # Crear columnas dinámicamente
    cols = st.columns(len(years))

    for i, year in enumerate(years):
        with cols[i]:
            st.subheader(f"Hechos Victimizantes {year}")
            
            df_year = df[df["ano_declara"] == year].copy()
            total_personas_year = len(df_year)
            
            st.caption(
                f"Filtro: TODOS LOS MOTIVOS | Total personas: {total_personas_year:,}"
            )

            if total_personas_year > 0:
                hechos_year = df_year["hecho_victimizante"].value_counts().head(20)
                hechos_year_df = pd.DataFrame(
                    {
                        "Hecho": hechos_year.index,
                        "Cantidad": hechos_year.values,
                        "Porcentaje": (hechos_year.values / total_personas_year * 100).round(1),
                    }
                )

                fig = go.Figure()
                fig.add_trace(
                    go.Bar(
                        y=hechos_year_df["Hecho"],
                        x=hechos_year_df["Cantidad"],
                        orientation="h",
                        text=[
                            f"{val:,}<br>({pct}%)"
                            for val, pct in zip(
                                hechos_year_df["Cantidad"], hechos_year_df["Porcentaje"]
                            )
                        ],
                        textposition="outside",
                        marker_color=colors[i % len(colors)],
                        hovertemplate="%{y}<br>Cantidad: %{x:,}<extra></extra>",
                    )
                )
                fig.update_layout(
                    height=700,
                    showlegend=False,
                    yaxis={"categoryorder": "total ascending"},
                    xaxis_title="Cantidad de Personas",
                    margin=dict(r=100, l=150, t=30, b=50),
                )
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(hechos_year_df, use_container_width=True, hide_index=True)
            else:
                st.info(f"No hay datos para el año {year}")
