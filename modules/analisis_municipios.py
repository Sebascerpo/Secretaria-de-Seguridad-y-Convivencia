import streamlit as st
import pandas as pd
import plotly.graph_objects as go


def render(df, tipo_texto, ubicacion_texto):
    st.header(f"Análisis por Ubicación - {tipo_texto}")
    st.caption(f"Ubicación: {ubicacion_texto}")
    st.caption("Incluye: Todos los hechos victimizantes")

    # Identificar años disponibles
    years = sorted(df["ano_declara"].unique(), reverse=False)
    
    # Determinar si es municipio o barrio
    if tipo_texto == "INTERMUNICIPAL":
        campo_ubicacion = "municipio_procede"
        texto_ubicacion = "Municipio"
    else:
        campo_ubicacion = "barrio_procede"
        texto_ubicacion = "Barrio"

    # Colores para los años
    colors = ["#dc2626", "#ea580c", "#f97316", "#fbbf24"]

    # Crear columnas dinámicamente
    cols = st.columns(len(years))

    for i, year in enumerate(years):
        with cols[i]:
            st.subheader(f"Top 15 {texto_ubicacion}s {year}")
            st.caption("Filtro: TODOS LOS MOTIVOS")

            df_year = df[df["ano_declara"] == year].copy()
            total_declaraciones_year = df_year["id_atencion"].nunique()

            if total_declaraciones_year > 0:
                ubicacion_year = (
                    df_year.groupby(campo_ubicacion)["id_atencion"]
                    .nunique()
                    .sort_values(ascending=False)
                    .head(15)
                )
                ubicacion_year_df = pd.DataFrame(
                    {
                        texto_ubicacion: ubicacion_year.index,
                        "Declaraciones": ubicacion_year.values,
                        "Porcentaje": (
                            ubicacion_year.values / total_declaraciones_year * 100
                        ).round(1),
                    }
                )

                fig = go.Figure()
                fig.add_trace(
                    go.Bar(
                        y=ubicacion_year_df[texto_ubicacion],
                        x=ubicacion_year_df["Declaraciones"],
                        orientation="h",
                        text=[
                            f"{val:,}<br>({pct}%)"
                            for val, pct in zip(
                                ubicacion_year_df["Declaraciones"],
                                ubicacion_year_df["Porcentaje"],
                            )
                        ],
                        textposition="outside",
                        marker_color=colors[i % len(colors)],
                        hovertemplate="%{y}<br>Declaraciones: %{x:,}<extra></extra>",
                    )
                )
                fig.update_layout(
                    height=600,
                    showlegend=False,
                    yaxis={"categoryorder": "total ascending"},
                    xaxis_title="Número de Declaraciones",
                    margin=dict(r=50, l=100, t=30, b=50),
                )
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(ubicacion_year_df, use_container_width=True, hide_index=True)
            else:
                st.info(f"No hay datos para el año {year}")
