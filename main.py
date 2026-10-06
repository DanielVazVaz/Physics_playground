import streamlit as st

st.set_page_config(layout="wide")

# 1. Definimos las páginas apuntando a la ruta real de los archivos
pagina_inicio = st.Page("pages/inicio.py", title="Inicio del Laboratorio", icon="🌌", default=True)
pagina_tiro = st.Page("pages/tiro_parabolico.py", title="Tiro Parabólico", icon="🎯")
pagina_movimiento_circular = st.Page("pages/movimiento_circular.py", title="Movimiento Circular", icon="🔄")
pagina_torques = st.Page("pages/torques.py", title="Torques", icon="🧰")
# 2. Inicializamos la navegación estructurada por secciones
# Puedes meter más páginas en la lista conforme vayas creando más laboratorios
nav = st.navigation({
    "Menú Principal": [pagina_inicio],
    "Tema 2: Cinemática y Dinámica": [pagina_tiro, pagina_movimiento_circular, pagina_torques]
})

# 3. Ejecutamos la navegación
nav.run()