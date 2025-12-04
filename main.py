import streamlit as st
import hashlib
import json
import os
from datetime import datetime

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Análisis - Personería de Medellín",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Ocultar navegación de Streamlit
st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] {
            display: none;
        }
    </style>
""",
    unsafe_allow_html=True,
)

# Archivo de usuarios (en producción usa base de datos)
USERS_FILE = "users.json"


def load_users():
    """Carga usuarios desde archivo"""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    else:
        # Usuarios por defecto
        default_users = {
            "admin": {
                "password": hashlib.sha256("admin123".encode()).hexdigest(),
                "nombre": "Administrador",
                "rol": "admin",
                "dashboards_permitidos": ["all"],
            },
            "analista": {
                "password": hashlib.sha256("analista123".encode()).hexdigest(),
                "nombre": "Analista",
                "rol": "analista",
                "dashboards_permitidos": [
                    "desplazamiento",
                    "hechos_victimizantes",
                    "demografico",
                ],
            },
        }
        with open(USERS_FILE, "w") as f:
            json.dump(default_users, f, indent=4)
        return default_users


def verify_login(username, password):
    """Verifica credenciales de login"""
    users = load_users()
    if username in users:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if users[username]["password"] == password_hash:
            return users[username]
    return None


def login_page():
    """Página de login"""
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("<h1 style='text-align: center;'>🏛️</h1>", unsafe_allow_html=True)
        st.markdown(
            "<h2 style='text-align: center;'>Sistema de Análisis</h2>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<h4 style='text-align: center;'>Personería de Medellín</h4>",
            unsafe_allow_html=True,
        )
        st.markdown("---")

        with st.form("login_form"):
            username = st.text_input("Usuario", placeholder="Ingresa tu usuario")
            password = st.text_input(
                "Contraseña", type="password", placeholder="Ingresa tu contraseña"
            )
            submit = st.form_submit_button("Iniciar Sesión", use_container_width=True)

            if submit:
                if username and password:
                    user_data = verify_login(username, password)
                    if user_data:
                        st.session_state["authenticated"] = True
                        st.session_state["username"] = username
                        st.session_state["user_data"] = user_data
                        st.session_state["login_time"] = datetime.now()
                        st.rerun()
                    else:
                        st.error("❌ Usuario o contraseña incorrectos")
                else:
                    st.warning("⚠️ Por favor ingresa usuario y contraseña")

        st.markdown("---")
        st.info(
            """
        **Usuarios de prueba:**
        - Usuario: `admin` / Contraseña: `admin123`
        - Usuario: `analista` / Contraseña: `analista123`
        """
        )


def dashboard_selector():
    """Selector de dashboards disponibles"""

    # Sidebar con información de usuario
    with st.sidebar:
        st.markdown("### 👤 Usuario")
        st.write(f"**{st.session_state['user_data']['nombre']}**")
        st.write(f"Rol: {st.session_state['user_data']['rol']}")
        st.markdown("---")

        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    # Título principal
    st.title("📊 Sistema de Dashboards")
    st.markdown("Selecciona el análisis que deseas visualizar")
    st.markdown("---")

    # Definir dashboards disponibles
    all_dashboards = {
        "desplazamiento": {
            "nombre": "📍 Análisis de Desplazamiento",
            "descripcion": "Análisis completo de desplazamiento forzado por municipios",
            "icon": "🚨",
            "color": "#dc2626",
        },
        "hechos_victimizantes": {
            "nombre": "⚠️ Hechos Victimizantes",
            "descripcion": "Análisis de todos los hechos victimizantes del conflicto armado",
            "icon": "⚔️",
            "color": "#ea580c",
        },
        "demografico": {
            "nombre": "👥 Análisis Demográfico",
            "descripcion": "Distribución por género, edad y enfoque diferencial",
            "icon": "📊",
            "color": "#059669",
        },
        "grupos_armados": {
            "nombre": "🎯 Grupos Armados",
            "descripcion": "Análisis de grupos armados responsables",
            "icon": "🔫",
            "color": "#7c3aed",
        },
        "temporal": {
            "nombre": "📅 Análisis Temporal",
            "descripcion": "Tendencias y evolución temporal de los datos",
            "icon": "📈",
            "color": "#0891b2",
        },
        "mapas": {
            "nombre": "🗺️ Mapas Geográficos",
            "descripcion": "Visualización geográfica de los datos",
            "icon": "🌍",
            "color": "#16a34a",
        },
    }

    # Filtrar dashboards según permisos de usuario
    user_permissions = st.session_state["user_data"]["dashboards_permitidos"]

    if "all" in user_permissions:
        available_dashboards = all_dashboards
    else:
        available_dashboards = {
            k: v for k, v in all_dashboards.items() if k in user_permissions
        }

    # Mostrar dashboards en grid
    cols = st.columns(3)

    for idx, (dashboard_id, dashboard_info) in enumerate(available_dashboards.items()):
        with cols[idx % 3]:
            with st.container():
                st.markdown(
                    f"""
                <div style='
                    padding: 20px;
                    border-radius: 10px;
                    border: 2px solid {dashboard_info['color']};
                    background-color: {dashboard_info['color']}15;
                    margin-bottom: 20px;
                    height: 200px;
                '>
                    <h2 style='margin: 0; color: {dashboard_info['color']};'>{dashboard_info['icon']}</h2>
                    <h3 style='margin: 10px 0;'>{dashboard_info['nombre']}</h3>
                    <p style='color: #666;'>{dashboard_info['descripcion']}</p>
                </div>
                """,
                    unsafe_allow_html=True,
                )

                if st.button(
                    f"Abrir", key=f"btn_{dashboard_id}", use_container_width=True
                ):
                    st.session_state["selected_dashboard"] = dashboard_id
                    st.rerun()

    # Información adicional
    st.markdown("---")
    st.markdown("### 📌 Información")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Dashboards Disponibles", len(available_dashboards))
    with col2:
        st.metric("Rol de Usuario", st.session_state["user_data"]["rol"])
    with col3:
        login_time = st.session_state.get("login_time", datetime.now())
        st.metric("Sesión Iniciada", login_time.strftime("%H:%M"))


def run_selected_dashboard():
    """Ejecuta el dashboard seleccionado"""
    dashboard_id = st.session_state.get("selected_dashboard")

    # Sidebar con navegación
    with st.sidebar:
        st.markdown("### 👤 Usuario")
        st.write(f"**{st.session_state['user_data']['nombre']}**")
        st.markdown("---")

        if st.button("⬅️ Volver al Menú", use_container_width=True):
            del st.session_state["selected_dashboard"]
            st.rerun()

        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    if dashboard_id == "demografico":
        from dashboards import demografico_dashboard

        demografico_dashboard.run()

    elif dashboard_id == "grupos_armados":
        from dashboards import grupos_armados_dashboard

        grupos_armados_dashboard.run()

    elif dashboard_id == "temporal":
        from dashboards import temporal_dashboard

        temporal_dashboard.run()

    elif dashboard_id == "mapas":
        from dashboards import mapas_dashboard

        mapas_dashboard.run()

    else:
        st.error(f"Dashboard '{dashboard_id}' no encontrado")


# Lógica principal
def main():
    # Verificar autenticación
    if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
        login_page()
    else:
        # Usuario autenticado
        if "selected_dashboard" in st.session_state:
            # Mostrar dashboard seleccionado
            run_selected_dashboard()
        else:
            # Mostrar selector de dashboards
            dashboard_selector()


if __name__ == "__main__":
    main()
