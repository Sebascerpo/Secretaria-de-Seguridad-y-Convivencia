import streamlit as st
import pandas as pd
import plotly.graph_objects as go


def render(df, tipo_texto, ubicacion_texto):
    st.header(f"Datos Generales - {tipo_texto}")
    st.caption(f"Ubicación: {ubicacion_texto}")
    st.caption(
        "Incluye: Desplazamiento forzado, Homicidio, Amenaza, y todos los demás hechos victimizantes"
    )

    # Separar por años
    df_2024 = df[df["ano_declara"] == 2024].copy()
    df_2025 = df[df["ano_declara"] == 2025].copy()

    # Calcular totales - TODOS LOS MOTIVOS
    total_declaraciones_2024 = df_2024["id_atencion"].nunique()
    total_personas_2024 = len(df_2024)
    total_declaraciones_2025 = df_2025["id_atencion"].nunique()
    total_personas_2025 = len(df_2025)

    st.subheader("TODOS LOS MOTIVOS")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Declaraciones 2024",
            f"{total_declaraciones_2024:,}",
            help="Total de ID de atención únicos en 2024 - Todos los motivos",
        )
    with col2:
        st.metric(
            "Personas 2024",
            f"{total_personas_2024:,}",
            help="Total de registros en 2024 - Todos los motivos",
        )
    with col3:
        st.metric(
            "Declaraciones 2025",
            f"{total_declaraciones_2025:,}",
            help="Total de ID de atención únicos en 2025 - Todos los motivos",
        )
    with col4:
        st.metric(
            "Personas 2025",
            f"{total_personas_2025:,}",
            help="Total de registros en 2025 - Todos los motivos",
        )

    st.markdown("---")

    # SOLO DESPLAZAMIENTO
    st.header("SOLO DESPLAZAMIENTO FORZADO")

    df_desplaz_2024 = df_2024[
        df_2024["hecho_victimizante"] == "Desplazamiento forzado"
    ].copy()
    df_desplaz_2025 = df_2025[
        df_2025["hecho_victimizante"] == "Desplazamiento forzado"
    ].copy()

    desplaz_decl_2024 = df_desplaz_2024["id_atencion"].nunique()
    desplaz_pers_2024 = len(df_desplaz_2024)
    desplaz_decl_2025 = df_desplaz_2025["id_atencion"].nunique()
    desplaz_pers_2025 = len(df_desplaz_2025)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Declaraciones 2024", f"{desplaz_decl_2024:,}", help="Solo desplazamiento"
        )
    with col2:
        st.metric("Personas 2024", f"{desplaz_pers_2024:,}", help="Solo desplazamiento")
    with col3:
        st.metric(
            "Declaraciones 2025", f"{desplaz_decl_2025:,}", help="Solo desplazamiento"
        )
    with col4:
        st.metric("Personas 2025", f"{desplaz_pers_2025:,}", help="Solo desplazamiento")

    # Tabla y gráfica comparativa
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Tabla Comparativa")
        comparison_table = pd.DataFrame(
            {
                "Año": ["2024", "2025"],
                "Declaraciones": [desplaz_decl_2024, desplaz_decl_2025],
                "Personas": [desplaz_pers_2024, desplaz_pers_2025],
            }
        )
        st.dataframe(comparison_table, use_container_width=True, hide_index=True)

    with col2:
        st.subheader("Comparación Visual")
        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                name="Declaraciones",
                x=["2024", "2025"],
                y=[desplaz_decl_2024, desplaz_decl_2025],
                text=[f"{desplaz_decl_2024:,}", f"{desplaz_decl_2025:,}"],
                textposition="outside",
                marker_color="#dc2626",
            )
        )
        fig.add_trace(
            go.Bar(
                name="Personas",
                x=["2024", "2025"],
                y=[desplaz_pers_2024, desplaz_pers_2025],
                text=[f"{desplaz_pers_2024:,}", f"{desplaz_pers_2025:,}"],
                textposition="outside",
                marker_color="#ea580c",
            )
        )
        fig.update_layout(
            barmode="group", height=400, yaxis_title="Cantidad", margin=dict(t=50)
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Datos mensuales
    st.subheader("Datos Mensuales 2024 - TODOS LOS MOTIVOS")

    monthly_2024 = (
        df_2024.groupby("mes_declara")
        .agg({"id_atencion": "nunique", "documento_anonimizado": "count"})
        .reset_index()
    )
    monthly_2024.columns = ["Mes", "Total Declaraciones", "Total Personas"]

    meses_nombres = {
        1: "Enero",
        2: "Febrero",
        3: "Marzo",
        4: "Abril",
        5: "Mayo",
        6: "Junio",
        7: "Julio",
        8: "Agosto",
        9: "Septiembre",
        10: "Octubre",
        11: "Noviembre",
        12: "Diciembre",
    }
    monthly_2024["Nombre Mes"] = monthly_2024["Mes"].map(meses_nombres)
    monthly_2024 = monthly_2024[
        ["Mes", "Nombre Mes", "Total Declaraciones", "Total Personas"]
    ]

    total_row = pd.DataFrame(
        {
            "Mes": ["TOTAL"],
            "Nombre Mes": [""],
            "Total Declaraciones": [total_declaraciones_2024],
            "Total Personas": [total_personas_2024],
        }
    )
    monthly_2024_display = pd.concat([monthly_2024, total_row], ignore_index=True)
    st.dataframe(monthly_2024_display, use_container_width=True, hide_index=True)

    st.markdown("---")

    st.subheader("Datos Mensuales 2025 - TODOS LOS MOTIVOS")

    monthly_2025 = (
        df_2025.groupby("mes_declara")
        .agg({"id_atencion": "nunique", "documento_anonimizado": "count"})
        .reset_index()
    )
    monthly_2025.columns = ["Mes", "Total Declaraciones", "Total Personas"]
    monthly_2025["Nombre Mes"] = monthly_2025["Mes"].map(meses_nombres)
    monthly_2025 = monthly_2025[
        ["Mes", "Nombre Mes", "Total Declaraciones", "Total Personas"]
    ]

    total_row_2025 = pd.DataFrame(
        {
            "Mes": ["TOTAL"],
            "Nombre Mes": [""],
            "Total Declaraciones": [total_declaraciones_2025],
            "Total Personas": [total_personas_2025],
        }
    )
    monthly_2025_display = pd.concat([monthly_2025, total_row_2025], ignore_index=True)
    st.dataframe(monthly_2025_display, use_container_width=True, hide_index=True)
