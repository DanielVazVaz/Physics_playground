# pages/inicio.py
import streamlit as st

st.title("🌌 Laboratorio de Física Virtual")
st.markdown("""
¡Bienvenido al entorno de simulación física! 
Usa el menú interactivo de la barra lateral izquierda para explorar los diferentes módulos experimentales.
""")

st.markdown("""## Tema 2: Cinemática y Dinámica""")

col1, col2= st.columns(2)
with col1:
    #? Tiro parabólico
    st.info("### 🎯 Módulo de Tiro Parabólico\nConfigura las condiciones de un movimiento parabólico")
    st.page_link("pages/tiro_parabolico.py", label="Ir al simulador de Tiro Parabólico", icon="🎯")
    #? Torques en 2D
    st.info("### 🧰 Módulo de Torques\nIntroduce fuerzas aplicadas en puntos cartesianos y calcula su momento resultante.")
    st.page_link("pages/torques.py", label="Ir al simulador de Torques", icon="🧰")
    
    
with col2:
    #? Movimiento circular
    st.info('### 🌕 Módulo de Movimiento Circular\nConfigura las condiciones de un movimiento circular uniformemente acelerado  \n')
    st.page_link("pages/movimiento_circular.py", label="Ir al simulador de Movimiento Circular", icon="🌕")

# st.markdown("""## Tema 3: Fluidos""")
# col3, col4 = st.columns(2)
# with col3:
#     pass
# with col4:
#     pass

# st.markdown("""## Tema 4: Ondas""")
# col5, col6 = st.columns(2)
# with col5:
#     pass
# with col6:
#     pass

# st.markdown("""## Tema 5: Electromagnetismo""")
# col7, col8 = st.columns(2)
# with col7:
#     pass
# with col8:
#     pass

# st.markdown("""## Tema 6: Óptica""")
# col9, col10 = st.columns(2)
# with col9:
#     pass
# with col10:
#     pass