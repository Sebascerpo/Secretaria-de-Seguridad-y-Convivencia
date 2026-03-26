import streamlit as st
import pandas as pd
import plotly.express as px


def render(df, tipo_texto, ubicacion_texto):
    st.header(f"Análisis Demográfico - {tipo_texto}")
    st.caption(f"Ubicación: {ubicacion_texto}")
    st.caption("Incluye: Todos los hechos victimizantes")

    # Identificar años disponibles
    years = sorted(df["ano_declara"].unique(), reverse=False)
    
    if not years:
        st.info(f"No hay datos registrados para {tipo_texto} en el dataset actual.")
        return
    
    # Colores para los años
    colors = ["#dc2626", "#ea580c", "#f97316", "#fbbf24"]

    # GÉNERO
    st.subheader("Análisis por Género")
    st.caption("Filtro: TODOS LOS MOTIVOS")

    gender_data_list = []
    
    # Mostrar tablas de género en columnas
    cols_gender = st.columns(len(years) + 1) # +1 for the chart column space if needed, but let's use 2 rows
    
    for i, year in enumerate(years):
        with cols_gender[i]:
            st.write(f"**Año {year}**")
            df_year = df[df["ano_declara"] == year]
            gender_counts = df_year["genero"].value_counts()
            gender_df_year = pd.DataFrame(
                {"Género": gender_counts.index, "Cantidad": gender_counts.values}
            )
            st.dataframe(gender_df_year, use_container_width=True, hide_index=True)
            
            # Preparar datos para la gráfica
            gender_df_year["Año"] = str(year)
            gender_data_list.append(gender_df_year)

    # Gráfica de Género
    st.write("**Comparativa de Género**")
    gender_data = pd.concat(gender_data_list, ignore_index=True)
    fig_gender = px.bar(
        gender_data,
        x="Género",
        y="Cantidad",
        color="Año",
        barmode="group",
        color_discrete_sequence=colors,
        text="Cantidad",
    )
    fig_gender.update_traces(texttemplate="%{text:,}", textposition="outside")
    fig_gender.update_layout(height=450, margin=dict(t=50))
    st.plotly_chart(fig_gender, use_container_width=True)

    st.markdown("---")

    # EDAD
    st.subheader("Análisis por Grupos de Edad")
    st.caption("Filtro: TODOS LOS MOTIVOS")

    edad_data_list = []
    edad_metrics = []

    for year in years:
        df_year = df[df["ano_declara"] == year].copy()
        df_year_edad = df_year[df_year["edad"].notna()].copy()
        
        if len(df_year_edad) > 0:
            df_year_edad["grupo_edad"] = pd.cut(
                df_year_edad["edad"],
                bins=[0, 17, 28, 40, 60, 150],
                labels=["0-17", "18-28", "29-40", "41-60", "60+"],
            )
            
            edad_counts = df_year_edad["grupo_edad"].value_counts().sort_index()
            edad_df_year = pd.DataFrame(
                {
                    "Grupo de Edad": edad_counts.index,
                    "Cantidad": edad_counts.values,
                    "Año": str(year)
                }
            )
            edad_data_list.append(edad_df_year)
            
            edad_metrics.append({
                "Año": year,
                "Promedio": df_year_edad["edad"].mean(),
                "Mediana": df_year_edad["edad"].median()
            })

    if edad_data_list:
        edad_data = pd.concat(edad_data_list, ignore_index=True)
        fig_edad = px.bar(
            edad_data,
            x="Grupo de Edad",
            y="Cantidad",
            color="Año",
            barmode="group",
            color_discrete_sequence=["#059669", "#10b981", "#34d399", "#6ee7b7"],
            text="Cantidad",
        )
        fig_edad.update_traces(texttemplate="%{text:,}", textposition="outside")
        fig_edad.update_layout(height=450, margin=dict(t=50))
        st.plotly_chart(fig_edad, use_container_width=True)

        # Métricas de edad en columnas
        cols_metrics = st.columns(len(edad_metrics) * 2)
        for i, m in enumerate(edad_metrics):
            with cols_metrics[i*2]:
                st.metric(f"Edad Promedio {m['Año']}", f"{m['Promedio']:.1f} años")
            with cols_metrics[i*2 + 1]:
                st.metric(f"Edad Mediana {m['Año']}", f"{m['Mediana']:.0f} años")

    st.markdown("---")

    # ENFOQUE DIFERENCIAL
    st.subheader("Enfoque Diferencial")
    st.caption("Filtro: TODOS LOS MOTIVOS")

    enfoque_data_list = []
    for year in years:
        df_year = df[df["ano_declara"] == year]
        enfoque_counts = df_year["enfoque_diferencial"].value_counts().head(10)
        enfoque_df_year = pd.DataFrame(
            {
                "Enfoque": enfoque_counts.index,
                "Cantidad": enfoque_counts.values,
                "Año": str(year)
            }
        )
        enfoque_data_list.append(enfoque_df_year)

    if enfoque_data_list:
        enfoque_data = pd.concat(enfoque_data_list, ignore_index=True)
        fig_enfoque = px.bar(
            enfoque_data,
            x="Enfoque",
            y="Cantidad",
            color="Año",
            barmode="group",
            color_discrete_sequence=colors,
            text="Cantidad",
        )
        fig_enfoque.update_traces(texttemplate="%{text:,}", textposition="outside")
        fig_enfoque.update_layout(height=500, margin=dict(t=50, b=100))
        fig_enfoque.update_xaxes(tickangle=-45)
        st.plotly_chart(fig_enfoque, use_container_width=True)
