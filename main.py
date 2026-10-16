import streamlit as st

st.set_page_config(layout="wide")

# 1. Definimos las páginas apuntando a la ruta real de los archivos
pagina_inicio = st.Page("pages/inicio.py", title="Inicio del Laboratorio", icon="🌌", default=True)
pagina_tiro = st.Page("pages/tiro_parabolico.py", title="Tiro Parabólico", icon="🎯")
pagina_movimiento_circular = st.Page("pages/movimiento_circular.py", title="Movimiento Circular", icon="🔄")
pagina_torques = st.Page("pages/torques.py", title="Torques", icon="🧰")
pagina_bernoulli = st.Page("pages/bernoulli.py", title="Ecuación de Bernoulli", icon="💧")
pagina_osmosis = st.Page("pages/osmosis.py", title="Ósmosis", icon="🧫")
pagina_sedimentacion = st.Page("pages/sedimentacion.py", title="Sedimentación en centrífuga", icon="🌀")
pagina_jurin = st.Page("pages/jurin.py", title="Ley de Jurin", icon="🧪")
pagina_oscilador = st.Page("pages/oscilador.py", title="Movimiento oscilatorio", icon="〰️")
pagina_transmision = st.Page("pages/transmision_ondas.py", title="Transmisión entre medios", icon="🔊")
# 2. Inicializamos la navegación estructurada por secciones
# Puedes meter más páginas en la lista conforme vayas creando más laboratorios
nav = st.navigation({
    "Menú Principal": [pagina_inicio],
    "Tema 2: Cinemática y Dinámica": [pagina_tiro, pagina_movimiento_circular, pagina_torques],
    "Tema 3: Fluidos": [pagina_bernoulli, pagina_osmosis, pagina_sedimentacion, pagina_jurin],
    "Tema 4: Ondas": [pagina_oscilador, pagina_transmision]
})

# 3. Ejecutamos la navegación
nav.run()