import streamlit as st
import pandas as pd
import plotly.graph_objects as go


def render(df, tipo_texto, ubicacion_texto):
    st.header(f"Grupos Responsables - {tipo_texto}")
    st.caption(f"Ubicación: {ubicacion_texto}")
    st.caption(
        "Incluye: TODOS los hechos victimizantes (Desplazamiento, Homicidio, Amenaza, etc.)"
    )

    # Identificar años disponibles
    years = sorted(df["ano_declara"].unique(), reverse=False)
    
    # Colores para los años
    colors = ["#7c3aed", "#6366f1", "#4f46e5", "#4338ca"]

    # Crear columnas dinámicamente
    cols = st.columns(len(years))

    for i, year in enumerate(years):
        with cols[i]:
            st.subheader(f"Grupos Responsables {year}")
            
            df_year = df[df["ano_declara"] == year].copy()
            total_personas_year = len(df_year)
            
            st.caption(f"Filtro: TODOS LOS MOTIVOS | Total casos: {total_personas_year:,}")

            if total_personas_year > 0:
                grupos_year = df_year["presunto_responsable"].value_counts().head(20)
                grupos_year_df = pd.DataFrame(
                    {
                        "Grupo": grupos_year.index,
                        "Casos": grupos_year.values,
                        "Porcentaje": (grupos_year.values / total_personas_year * 100).round(1),
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
                                grupos_year_df["Casos"], grupos_year_df["Porcentaje"]
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
                st.info(f"No hay datos para el año {year}")
