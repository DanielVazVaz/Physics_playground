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

st.markdown("""## Tema 3: Fluidos""")

col1, col2= st.columns(2)
with col1:
    st.info("### 💧 Módulo de Bernoulli\nResuelve el balance mecánico y la continuidad para varios puntos de un fluido. Se asume fluido no compresible ideal")
    st.page_link("pages/bernoulli.py", label="Ir al simulador de Bernoulli", icon="💧")
    st.info("### 🌀 Módulo de Sedimentación\nVelocidad de sedimentación de una partícula en una centrífuga a partir del balance de fuerzas centrífuga, empuje y arrastre.")
    st.page_link("pages/sedimentacion.py", label="Ir al simulador de Sedimentación", icon="🌀")

with col2:
    st.info("### 🧫 Módulo de Ósmosis\nCalcula el sentido del flujo de agua a través de una membrana semipermeable (ΔP vs ΔΠ) o el valor que anula el flujo.")
    st.page_link("pages/osmosis.py", label="Ir al simulador de Ósmosis", icon="🧫")
    st.info("### 🧪 Módulo de Capilaridad\nAltura de capilaridad de un líquido en un tubo estrecho a partir de la tensión superficial usando la Ley de Jurin.")
    st.page_link("pages/jurin.py", label="Ir al simulador de la Ley de Jurin", icon="🧪")



st.markdown("""## Tema 4: Ondas""")
st.info("### 〰️ Movimiento oscilatorio\nVisualiza posición, velocidad y aceleración de un oscilador simple o amortiguado al cambiar sus parámetros.")
st.page_link("pages/oscilador.py", label="Ir al visor de movimiento oscilatorio", icon="〰️")
st.info("### 🔊 Transmisión entre medios\nReflexión y transmisión de una onda sonora en varias interfaces: factores R y T, intensidades y decibelios.")
st.page_link("pages/transmision_ondas.py", label="Ir a transmisión entre medios", icon="🔊")

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