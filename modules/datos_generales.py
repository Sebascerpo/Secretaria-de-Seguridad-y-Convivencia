import streamlit as st
import pandas as pd
import plotly.graph_objects as go


def render(df, tipo_texto, ubicacion_texto):
    st.header(f"Datos Generales - {tipo_texto}")
    st.caption(f"Ubicación: {ubicacion_texto}")
    st.caption(
        "Incluye: Desplazamiento forzado, Homicidio, Amenaza, y todos los demás hechos victimizantes"
    )

    # Identificar años disponibles
    years = sorted(df["ano_declara"].unique(), reverse=False)

    # Calcular totales - TODOS LOS MOTIVOS
    metrics_data = {}
    for year in years:
        df_year = df[df["ano_declara"] == year]
        metrics_data[year] = {
            "declaraciones": df_year["id_atencion"].nunique(),
            "personas": len(df_year)
        }

    st.subheader("TODOS LOS MOTIVOS")
    
    # Mostrar métricas dinámicamente
    # Determinamos cuántas filas necesitamos para 2 métricas por año
    num_years = len(years)
    cols = st.columns(num_years * 2)
    for i, year in enumerate(years):
        with cols[i*2]:
            st.metric(
                f"Declaraciones {year}",
                f"{metrics_data[year]['declaraciones']:,}",
                help=f"Total de ID de atención únicos en {year} - Todos los motivos",
            )
        with cols[i*2 + 1]:
            st.metric(
                f"Personas {year}",
                f"{metrics_data[year]['personas']:,}",
                help=f"Total de registros en {year} - Todos los motivos",
            )

    st.markdown("---")

    # SOLO DESPLAZAMIENTO FORZADO
    st.header("SOLO DESPLAZAMIENTO FORZADO")

    desplaz_metrics = {}
    for year in years:
        df_year = df_desplaz = df[
            (df["ano_declara"] == year) & (df["hecho_victimizante"] == "Desplazamiento forzado")
        ].copy()
        desplaz_metrics[year] = {
            "declaraciones": df_year["id_atencion"].nunique(),
            "personas": len(df_year)
        }

    cols_desplaz = st.columns(num_years * 2)
    for i, year in enumerate(years):
        with cols_desplaz[i*2]:
            st.metric(
                f"Declaraciones {year}", f"{desplaz_metrics[year]['declaraciones']:,}", help="Solo desplazamiento"
            )
        with cols_desplaz[i*2 + 1]:
            st.metric(f"Personas {year}", f"{desplaz_metrics[year]['personas']:,}", help="Solo desplazamiento")

    # Tabla y gráfica comparativa
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Tabla Comparativa")
        comparison_table = pd.DataFrame(
            {
                "Año": [str(y) for y in years],
                "Declaraciones": [desplaz_metrics[y]["declaraciones"] for y in years],
                "Personas": [desplaz_metrics[y]["personas"] for y in years],
            }
        )
        st.dataframe(comparison_table, use_container_width=True, hide_index=True)

    with col2:
        st.subheader("Comparación Visual")
        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                name="Declaraciones",
                x=[str(y) for y in years],
                y=[desplaz_metrics[y]["declaraciones"] for y in years],
                text=[f"{desplaz_metrics[y]['declaraciones']:,}" for y in years],
                textposition="outside",
                marker_color="#dc2626",
            )
        )
        fig.add_trace(
            go.Bar(
                name="Personas",
                x=[str(y) for y in years],
                y=[desplaz_metrics[y]["personas"] for y in years],
                text=[f"{desplaz_metrics[y]['personas']:,}" for y in years],
                textposition="outside",
                marker_color="#ea580c",
            )
        )
        fig.update_layout(
            barmode="group", height=400, yaxis_title="Cantidad", margin=dict(t=50)
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # --- DATOS MENSUALES ---
    meses_nombres = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
        7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
    }

    st.subheader("Datos Mensuales - TODOS LOS MOTIVOS")
    
    tabs_years = st.tabs([f"Año {year}" for year in years])
    
    for i, year in enumerate(years):
        with tabs_years[i]:
            df_year = df[df["ano_declara"] == year]
            monthly = (
                df_year.groupby("mes_declara")
                .agg({"id_atencion": "nunique", "documento_anonimizado": "count"})
                .reset_index()
            )
            monthly.columns = ["Mes", "Total Declaraciones", "Total Personas"]
            monthly["Nombre Mes"] = monthly["Mes"].map(meses_nombres)
            
            # Convertir Mes a string para evitar errores con Arrow al añadir fila TOTAL
            monthly["Mes"] = monthly["Mes"].astype(str)
            
            monthly = monthly[["Mes", "Nombre Mes", "Total Declaraciones", "Total Personas"]]
            
            total_row = pd.DataFrame({
                "Mes": ["TOTAL"],
                "Nombre Mes": [""],
                "Total Declaraciones": [metrics_data[year]["declaraciones"]],
                "Total Personas": [metrics_data[year]["personas"]],
            })
            monthly_display = pd.concat([monthly, total_row], ignore_index=True)
            st.dataframe(monthly_display, use_container_width=True, hide_index=True)
