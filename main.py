import streamlit as st
import hashlib
import json
import os
import secrets
from datetime import datetime, timedelta

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Análisis - Personería de Medellín",
    page_icon=None,
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

# Archivo de usuarios
USERS_FILE = "users.json"
SESSIONS_FILE = "sessions.json"
SESSION_DURATION_HOURS = 24  # Duración de la sesión en horas


def load_users():
    """Carga usuarios desde archivo"""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    else:
        default_users = {
            "admin": {
                "password": hashlib.sha256("admin123".encode()).hexdigest(),
                "nombre": "Administrador",
                "rol": "admin",
                "proyectos_permitidos": ["all"],
            },
            "analista": {
                "password": hashlib.sha256("analista123".encode()).hexdigest(),
                "nombre": "Analista",
                "rol": "analista",
                "proyectos_permitidos": ["conflicto_armado"],
            },
        }
        with open(USERS_FILE, "w") as f:
            json.dump(default_users, f, indent=4)
        return default_users


def load_sessions():
    """Carga sesiones desde archivo"""
    if os.path.exists(SESSIONS_FILE):
        try:
            with open(SESSIONS_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_sessions(sessions):
    """Guarda sesiones en archivo"""
    with open(SESSIONS_FILE, "w") as f:
        json.dump(sessions, f, indent=4, default=str)


def create_session(username, user_data):
    """Crea una nueva sesión y retorna el token"""
    sessions = load_sessions()
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(hours=SESSION_DURATION_HOURS)
    
    sessions[token] = {
        "username": username,
        "user_data": user_data,
        "login_time": datetime.now().isoformat(),
        "expires_at": expires_at.isoformat(),
    }
    
    save_sessions(sessions)
    return token


def get_session(token):
    """Obtiene la sesión asociada a un token si es válida"""
    sessions = load_sessions()
    
    if token not in sessions:
        return None
    
    session = sessions[token]
    expires_at = datetime.fromisoformat(session["expires_at"])
    
    # Verificar si la sesión expiró
    if datetime.now() > expires_at:
        # Eliminar sesión expirada
        del sessions[token]
        save_sessions(sessions)
        return None
    
    return session


def delete_session(token):
    """Elimina una sesión"""
    sessions = load_sessions()
    if token in sessions:
        del sessions[token]
        save_sessions(sessions)


def cleanup_expired_sessions():
    """Elimina sesiones expiradas"""
    sessions = load_sessions()
    now = datetime.now()
    expired_tokens = []
    
    for token, session in sessions.items():
        expires_at = datetime.fromisoformat(session["expires_at"])
        if now > expires_at:
            expired_tokens.append(token)
    
    for token in expired_tokens:
        del sessions[token]
    
    if expired_tokens:
        save_sessions(sessions)


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
                        # Crear sesión persistente
                        token = create_session(username, user_data)
                        st.session_state["authenticated"] = True
                        st.session_state["username"] = username
                        st.session_state["user_data"] = user_data
                        st.session_state["login_time"] = datetime.now()
                        st.session_state["session_token"] = token
                        # Agregar token a URL para persistencia en recargas
                        st.query_params["token"] = token
                        st.rerun()
                    else:
                        st.error("Usuario o contraseña incorrectos")
                else:
                    st.warning("Por favor ingresa usuario y contraseña")

        st.markdown("---")


def get_available_projects():
    """Detecta automáticamente todos los proyectos en la carpeta proyectos/"""
    projects = {}

    # Configuración de proyectos (metadata)
    # Aquí defines la info de cada proyecto
    projects_config = {
        "conflicto_armado": {
            "nombre": "Conflicto Armado y Desplazamiento",
            "descripcion": "Análisis completo de desplazamiento forzado y hechos victimizantes",
            "icon": "",
            "color": "#dc2626",
            "archivo_datos": "data/datos.csv",
        },
        # Agrega más proyectos aquí
        # "otro_proyecto": {
        #     "nombre": "Otro Proyecto",
        #     "descripcion": "Descripción del proyecto",
        #     "icon": "",
        #     "color": "#059669",
        #     "archivo_datos": "data/otros_datos.csv",
        # },
    }

    # Detectar archivos .py en la carpeta proyectos/
    proyectos_dir = "proyectos"
    if os.path.exists(proyectos_dir):
        for filename in os.listdir(proyectos_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                project_id = filename[:-3]  # Quitar .py

                # Si el proyecto tiene configuración, usarla
                if project_id in projects_config:
                    projects[project_id] = projects_config[project_id]
                else:
                    # Si no tiene config, crear una por defecto
                    projects[project_id] = {
                        "nombre": project_id.replace("_", " ").title(),
                        "descripcion": f"Proyecto de análisis: {project_id}",
                        "icon": "",
                        "color": "#6366f1",
                        "archivo_datos": f"data/{project_id}.csv",
                    }

    return projects


def project_selector():
    """Selector de proyectos disponibles"""

    # Sidebar con información de usuario
    with st.sidebar:
        st.markdown("### Usuario")
        st.write(f"**{st.session_state['user_data']['nombre']}**")
        st.write(f"Rol: {st.session_state['user_data']['rol']}")
        st.markdown("---")

        if st.button("Cerrar Sesión", use_container_width=True):
            # Eliminar sesión persistente
            token = st.session_state.get("session_token") or st.query_params.get("token", [None])[0]
            if token:
                delete_session(token)
            # Limpiar query params
            if "token" in st.query_params:
                del st.query_params["token"]
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    # Título principal
    st.title("Sistema de Proyectos de Análisis")
    st.markdown("Selecciona el proyecto que deseas visualizar")
    st.markdown("---")

    # Obtener proyectos disponibles automáticamente
    all_projects = get_available_projects()

    # Filtrar proyectos según permisos de usuario
    user_permissions = st.session_state["user_data"]["proyectos_permitidos"]

    if "all" in user_permissions:
        available_projects = all_projects
    else:
        available_projects = {
            k: v for k, v in all_projects.items() if k in user_permissions
        }

    # Mostrar proyectos en grid
    cols = st.columns(3)

    for idx, (project_id, project_info) in enumerate(available_projects.items()):
        with cols[idx % 3]:
            with st.container():
                st.markdown(
                    f"""
                <div style='
                    padding: 20px;
                    border-radius: 10px;
                    border: 2px solid {project_info['color']};
                    background-color: {project_info['color']}15;
                    margin-bottom: 20px;
                    height: 200px;
                '>
                    <h3 style='margin: 10px 0; color: {project_info['color']};'>{project_info['nombre']}</h3>
                    <p style='color: #666;'>{project_info['descripcion']}</p>
                </div>
                """,
                    unsafe_allow_html=True,
                )

                if st.button(
                    f"Abrir Proyecto", key=f"btn_{project_id}", use_container_width=True
                ):
                    st.session_state["selected_project"] = project_id
                    st.session_state["project_info"] = project_info
                    st.rerun()

    # Información adicional
    st.markdown("---")
    st.markdown("### Información")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Proyectos Disponibles", len(available_projects))
    with col2:
        st.metric("Rol de Usuario", st.session_state["user_data"]["rol"])
    with col3:
        login_time = st.session_state.get("login_time", datetime.now())
        st.metric("Sesión Iniciada", login_time.strftime("%H:%M"))


def run_selected_project():
    """Ejecuta el proyecto seleccionado"""
    project_id = st.session_state.get("selected_project")
    project_info = st.session_state.get("project_info")

    # Sidebar con navegación
    with st.sidebar:
        st.markdown("### Usuario")
        st.write(f"**{st.session_state['user_data']['nombre']}**")
        st.markdown("---")

        st.markdown("### Proyecto Actual")
        st.write(f"**{project_info['nombre']}**")
        st.markdown("---")

        if st.button("Volver al Menú", use_container_width=True):
            del st.session_state["selected_project"]
            del st.session_state["project_info"]
            st.rerun()

        if st.button("Cerrar Sesión", use_container_width=True):
            # Eliminar sesión persistente
            token = st.session_state.get("session_token") or st.query_params.get("token", [None])[0]
            if token:
                delete_session(token)
            # Limpiar query params
            if "token" in st.query_params:
                del st.query_params["token"]
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    # Importar y ejecutar el proyecto dinámicamente
    try:
        # Importar el módulo del proyecto
        project_module = __import__(f"proyectos.{project_id}", fromlist=["run"])

        # Ejecutar la función run() del proyecto
        if hasattr(project_module, "run"):
            project_module.run(project_info)
        else:
            st.error(f"El proyecto '{project_id}' no tiene una función run()")
    except ImportError as e:
        st.error(f"Error al cargar el proyecto '{project_id}': {e}")
        st.info(
            "Asegúrate de que el archivo del proyecto existe en la carpeta 'proyectos/'"
        )
    except Exception as e:
        st.error(f"Error al ejecutar el proyecto: {e}")


# Lógica principal
def main():
    # Limpiar sesiones expiradas
    cleanup_expired_sessions()
    
    # PRIORIDAD 1: Obtener token de query params (persiste en recargas de página)
    # Esto es crítico porque session_state se pierde al recargar la página
    query_params = st.query_params
    token_from_url = None
    
    # Manejar query params - Streamlit puede devolver lista o string
    try:
        if "token" in query_params:
            token_value = query_params["token"]
            if isinstance(token_value, list):
                token_from_url = token_value[0] if len(token_value) > 0 else None
            elif isinstance(token_value, str):
                token_from_url = token_value
    except Exception:
        token_from_url = None
    
    # PRIORIDAD 2: Obtener token de session state (solo válido durante la sesión actual)
    token_from_session = st.session_state.get("session_token")
    
    # Usar token de URL si existe (tiene prioridad porque persiste en recargas), sino del session state
    token = token_from_url or token_from_session
    
    # Si encontramos un token (de URL o session), intentar restaurar la sesión
    if token:
        session = get_session(token)
        if session:
            # Restaurar sesión desde el token
            st.session_state["authenticated"] = True
            st.session_state["username"] = session["username"]
            st.session_state["user_data"] = session["user_data"]
            st.session_state["login_time"] = datetime.fromisoformat(session["login_time"])
            st.session_state["session_token"] = token
            
            # CRÍTICO: Asegurar que el token esté SIEMPRE en query params para persistencia
            # Esto garantiza que al recargar la página, el token esté disponible
            current_url_token = query_params.get("token")
            if not current_url_token or (isinstance(current_url_token, list) and token not in current_url_token) or (not isinstance(current_url_token, list) and current_url_token != token):
                st.query_params["token"] = token
        else:
            # Sesión expirada o inválida - limpiar todo
            if "authenticated" in st.session_state:
                del st.session_state["authenticated"]
            if "session_token" in st.session_state:
                del st.session_state["session_token"]
            if "token" in query_params:
                del st.query_params["token"]
    
    # Si ya estamos autenticados, asegurar que el token esté en la URL
    if st.session_state.get("authenticated") and st.session_state.get("session_token"):
        current_token = st.session_state["session_token"]
        current_url_token = query_params.get("token")
        # Verificar si el token en la URL es diferente o no existe
        needs_update = False
        if not current_url_token:
            needs_update = True
        elif isinstance(current_url_token, list):
            if current_token not in current_url_token:
                needs_update = True
        elif current_url_token != current_token:
            needs_update = True
        
        if needs_update:
            st.query_params["token"] = current_token
    
    # Verificar autenticación DESPUÉS de intentar restaurar la sesión
    is_authenticated = st.session_state.get("authenticated", False)
    
    if not is_authenticated:
        login_page()
    else:
        # Usuario autenticado
        if "selected_project" in st.session_state:
            # Mostrar proyecto seleccionado
            run_selected_project()
        else:
            # Mostrar selector de proyectos
            project_selector()


if __name__ == "__main__":
    main()
