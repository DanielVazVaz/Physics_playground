import streamlit as st
import numpy as np
import scipy.optimize as opt
import plotly.graph_objects as go

# --- ETAPA 1: Motor Físico del Movimiento Circular Corregido ---
class SolvadorMovimientoCircular:
    def __init__(self):
        # Las 10 variables físicas reales del sistema
        self.vars = {
            'R': None,        # Radio del giro (m)
            'w0': None,       # Velocidad angular inicial (rad/s)
            'w_f': None,      # Velocidad angular final (rad/s)
            'alpha': None,    # Aceleración angular (rad/s²)
            'theta': None,    # Ángulo total girado (radianes)
            't': None,        # Tiempo del movimiento (s)
            'v_t': None,      # Velocidad tangencial final (m/s)
            'a_t': None,      # Aceleración tangencial (m/s²)
            'a_n': None,      # Aceleración centrípeta final (m/s²)
            'rpm': None       # Velocidad angular final en RPM (rev/min)
        }

    def _residuos_circulares(self, valores_activos, claves_activas):
        estado = self.vars.copy()
        for clave, val in zip(claves_activas, valores_activos):
            estado[clave] = val

        # Las 6 ecuaciones fundamentales del sistema (todas igualadas a cero)
        res_wf = estado['w0'] + estado['alpha'] * estado['t'] - estado['w_f']
        res_theta = estado['w0'] * estado['t'] + 0.5 * estado['alpha'] * (estado['t']**2) - estado['theta']
        res_vt = estado['w_f'] * estado['R'] - estado['v_t']
        res_an = (estado['v_t']**2) / estado['R'] - estado['a_n']
        res_rpm = estado['w_f'] * (30 / np.pi) - estado['rpm']
        res_at = estado['alpha'] * estado['R'] - estado['a_t']

        return [res_wf, res_theta, res_vt, res_an, res_rpm, res_at]

    def resolver(self, datos_introducidos):
        for clave in self.vars:
            self.vars[clave] = None
        self.vars.update(datos_introducidos)

        claves_activas = [k for k, v in self.vars.items() if v is None]
        
        # Semillas iniciales seguras para guiar al solucionador numérico fsolve
        valores_iniciales = []
        for k in claves_activas:
            if k in ['R', 't']: valores_iniciales.append(1.0)
            elif k in ['w0', 'w_f', 'rpm']: valores_iniciales.append(10.0)
            else: valores_iniciales.append(1.0)

        solucion_bruta, info, ier, msg = opt.fsolve(
            self._residuos_circulares, 
            valores_iniciales, 
            args=(claves_activas,),
            full_output=True
        )

        if ier != 1:
            return False, "El motor matemático no encontró una solución válida. Revisa si tus datos tienen sentido físico (ej. el radio o el tiempo no pueden ser negativos o cero)."

        for clave, valor_resuelto in zip(claves_activas, solucion_bruta):
            self.vars[clave] = valor_resuelto
            
        return True, self.vars

# --- ETAPA 2: Interfaz de Usuario ---
st.title("🌕 Laboratorio Virtual de Movimiento Circular")
st.markdown("""
¡Bienvenido al laboratorio rotacional! Este sistema combina el **Movimiento Circular Uniforme (MCU)** y el **Variado (MCUV)**.
Tiene **4 grados de libertad**. Selecciona exactamente 4 datos conocidos, introduce sus valores y el motor despejará las 6 incógnitas restantes.
""")

nombres_variables = {
    'R': 'Radio de Giro (R) [m]',
    'w0': 'Velocidad Angular Inicial (w0) [rad/s]',
    'w_f': 'Velocidad Angular Final (w_f) [rad/s]',
    'rpm': 'Revoluciones Finales (RPM) [rev/min]',
    'alpha': 'Aceleración Angular (alpha) [rad/s²]',
    'theta': 'Ángulo Girado (theta) [rad]',
    't': 'Tiempo Transcurrido (t) [s]',
    'v_t': 'Velocidad Tangencial Final (v_t) [m/s]',
    'a_t': 'Aceleración Tangencial (a_t) [m/s²]',
    'a_n': 'Aceleración Centrípeta (a_n) [m/s²]'
}

# Diccionario de traducción a LaTeX
traducciones_latex = {
    "R": "$R$", "w0": "$w_0$", "w_f": "$w_f$", "rpm": "$RPM$",
    "alpha": "$\\alpha$", "theta": "$\\theta$", "t": "$t$", "v_t": "$v_t$", 
    "a_t": "$a_t$", "a_n": "$a_n$"
}

st.subheader("1. Selecciona tus 4 Datos Conocidos")
datos_seleccionados = st.multiselect(
    "Elige los 4 parámetros iniciales del ejercicio:",
    options=list(nombres_variables.keys()),
    default=['R', 'w0', 'alpha', 't'], 
    format_func=lambda x: nombres_variables[x]
)

num_seleccionados = len(datos_seleccionados)
if num_seleccionados != 4:
    st.info(f"💡 **Estado de la matriz:** Has seleccionado **{num_seleccionados}/4** variables. Necesitas marcar exactamente 4.")
else:
    st.success("✅ Grados de libertad fijados. Modifica los valores numéricos:")
    
    st.subheader("2. Valores de los Datos Conocidos")
    columnas = st.columns(4)
    valores_usuario = {}
    
    for idx, clave in enumerate(datos_seleccionados):
        with columnas[idx % 4]:
            if clave == 'R': valores_usuario['R'] = st.number_input("Radio (R) [m]", min_value=0.01, value=3.5, step=0.5)
            elif clave == 'w0': valores_usuario['w0'] = st.number_input("Vel. angular inicial ($w_0$) [rad/s]", value=3.0, step=1.0)
            elif clave == 'w_f': valores_usuario['w_f'] = st.number_input("Vel. angular final ($w_f$) [rad/s]", value=10.0, step=1.0)
            elif clave == 'rpm': valores_usuario['rpm'] = st.number_input("Revoluciones (RPM) [rev/min]", value=100.0, step=10.0)
            elif clave == 'alpha': valores_usuario['alpha'] = st.number_input("Aceleración ang. ($\\alpha$) [rad/s²]", value=0.0, step=0.5)
            elif clave == 'theta': valores_usuario['theta'] = st.number_input("Ángulo total ($\\theta$) [rad]", value=6.28, step=1.0)
            elif clave == 't': valores_usuario['t'] = st.number_input("Tiempo (t) [s]", min_value=0.01, value=6.0, step=0.5)
            elif clave == 'v_t': valores_usuario['v_t'] = st.number_input("Vel. tangencial ($v_t$) [m/s]", value=10.0, step=1.0)
            elif clave == 'a_t': valores_usuario['a_t'] = st.number_input("Acel. tangencial ($a_t$) [m/s²]", value=0.0, step=0.5)
            elif clave == 'a_n': valores_usuario['a_n'] = st.number_input("Acel. centrípeta ($a_n$) [m/s²]", value=9.8, step=1.0)

    # Disparar motor de cálculo
    motor = SolvadorMovimientoCircular()
    exito, resultado = motor.resolver(valores_usuario)

    if not exito:
        st.error(f"❌ {resultado}")
    else:
        # --- ETAPA 2 CORREGIDA ---
        with st.expander("📊 Ver Resultados de las Incógnitas Despejadas", expanded=True):
            columnas_res = st.columns(4)
            contador_c = 0
            for clave, texto in nombres_variables.items():
                es_calculado = clave not in datos_seleccionados
                unidad = "m" if clave=='R' else "rad/s" if 'w' in clave else "rad/s²" if clave=='alpha' else "rad" if clave=='theta' else "s" if clave=='t' else "rev/min" if clave=='rpm' else "m/s" if clave=='v_t' else "m/s²"
                etiqueta = ":red[(Calculado)]" if es_calculado else ":blue[(Dado)]"
                
                # CORREGIDO: Añadido  para extraer el texto limpio antes de limpiar espacios
                nombre_sin_unidades = texto.split(' [')[0].strip()
                
                variable_latex = traducciones_latex.get(clave, clave)
                nombre_con_latex = nombre_sin_unidades.replace(clave, variable_latex)
                
                with columnas_res[contador_c % 4]:
                    st.metric(
                        label=f"{nombre_con_latex} {etiqueta}",
                        value=f"{resultado[clave]:.2f} {unidad}",
                        delta="Resuelto" if es_calculado else None
                    )
                contador_c += 1



        # --- ETAPA 3 DEFINITIVA: ANIMACIÓN EXCLUSIVA CON TEXTO DINÁMICO EN VIVO ---
        st.subheader("3. Simulación Animada de la Trayectoria")
        st.markdown("Usa los controles del gráfico para reproducir, o mueve el deslizador de abajo para analizar el movimiento **fotograma a fotograma**.")
        
        # 1. Generamos los pasos de tiempo reales (100 fotogramas)
        pasos_tiempo = np.linspace(0, resultado['t'], 100)
        
        # 2. Slider interactivo de Streamlit
        t_seleccionado = st.slider(
            "⏱️ Control manual del tiempo (Avanza fotograma a fotograma con las flechas del teclado):", 
            min_value=float(pasos_tiempo[0]), 
            max_value=float(pasos_tiempo[-1]), 
            value=float(pasos_tiempo[-1]),
            step=float(pasos_tiempo[1] - pasos_tiempo[0]),
            format="%.2f s"
        )
        
        # Encontramos el índice del fotograma que más se aproxima al tiempo del slider
        idx_frame = np.abs(pasos_tiempo - t_seleccionado).argmin()
        
        # 3. Matrices físicas de la trayectoria
        angulos_tiempo = resultado['w0'] * pasos_tiempo + 0.5 * resultado['alpha'] * (pasos_tiempo ** 2)
        vueltas_tiempo = angulos_tiempo / (2 * np.pi)
        
        x_anim = resultado['R'] * np.cos(angulos_tiempo)
        y_anim = resultado['R'] * np.sin(angulos_tiempo)
        
        # Parámetros instantáneos variables para cada fotograma
        w_instantanea = resultado['w0'] + resultado['alpha'] * pasos_tiempo
        vt_instantenea = w_instantanea * resultado['R']
        an_instantenea = (vt_instantenea**2) / resultado['R']
        at_instantenea = np.full_like(pasos_tiempo, resultado['a_t'])

        # Longitud visual de la flecha fija al 75% del radio
        longitud_fija_flecha = 0.75 * resultado['R']

        an_x_punta, an_y_punta = [], []
        at_x_punta, at_y_punta = [], []

        for i in range(100):
            an_x_punta.append(x_anim[i] - longitud_fija_flecha * np.cos(angulos_tiempo[i]) if an_instantenea[i] > 1e-5 else x_anim[i])
            an_y_punta.append(y_anim[i] - longitud_fija_flecha * np.sin(angulos_tiempo[i]) if an_instantenea[i] > 1e-5 else y_anim[i])
            
            if abs(at_instantenea[i]) > 1e-5:
                sentido = 1.0 if at_instantenea[i] >= 0 else -1.0
                at_x_punta.append(x_anim[i] - sentido * longitud_fija_flecha * np.sin(angulos_tiempo[i]))
                at_y_punta.append(y_anim[i] + sentido * longitud_fija_flecha * np.cos(angulos_tiempo[i]))
            else:
                at_x_punta.append(x_anim[i])
                at_y_punta.append(y_anim[i])

        # Cabezas de las flechas en V manuales
        l_aleta = resultado['R'] * 0.08
        angulo_aleta = np.radians(30)

        an_flecha_x, an_flecha_y = [], []
        at_flecha_x, at_flecha_y = [], []

        for i in range(100):
            phi_an = angulos_tiempo[i] + np.pi
            an_flecha_x.append([an_x_punta[i] + l_aleta * np.cos(phi_an + np.pi - angulo_aleta), an_x_punta[i], an_x_punta[i] + l_aleta * np.cos(phi_an + np.pi + angulo_aleta)])
            an_flecha_y.append([an_y_punta[i] + l_aleta * np.sin(phi_an + np.pi - angulo_aleta), an_y_punta[i], an_y_punta[i] + l_aleta * np.sin(phi_an + np.pi + angulo_aleta)])

            desfase = np.pi/2 if at_instantenea[i] >= 0 else -np.pi/2
            phi_at = angulos_tiempo[i] + desfase
            at_flecha_x.append([at_x_punta[i] + l_aleta * np.cos(phi_at + np.pi - angulo_aleta), at_x_punta[i], at_x_punta[i] + l_aleta * np.cos(phi_at + np.pi + angulo_aleta)])
            at_flecha_y.append([at_y_punta[i] + l_aleta * np.sin(phi_at + np.pi - angulo_aleta), at_y_punta[i], at_y_punta[i] + l_aleta * np.sin(phi_at + np.pi + angulo_aleta)])

        # Fondo de la pista circular
        angulos_pista = np.linspace(0, 2 * np.pi, 300)
        x_pista = resultado['R'] * np.cos(angulos_pista)
        y_pista = resultado['R'] * np.sin(angulos_pista)
        limite_eje = resultado['R'] * 1.6

        # 4. Estado inicial del gráfico sincronizado con el fotograma seleccionado
        i = idx_frame
        texto_cartel_inicial = f"Tiempo: {pasos_tiempo[i]:.2f} s | Vueltas: {vueltas_tiempo[i]:.2f} | Ac. Normal: {an_instantenea[i]:.2f} m/s² | Ac. Tangencial: {at_instantenea[i]:.2f} m/s² | Vel. Angular: {w_instantanea[i]:.2f} rad/s | Vel. Tangencial: {vt_instantenea[i]:.2f} m/s"
        
        fig = go.Figure(
            data=[
                go.Scatter(x=x_pista, y=y_pista, mode='lines', name='Órbita de Giro', line=dict(color='#00CC96', width=2)),
                go.Scatter(x=[x_anim[i]], y=[y_anim[i]], mode='markers+text', name='Partícula', text=["🚗"], textposition="top center", marker=dict(color='red', size=14)),
                go.Scatter(x=[0, x_anim[i]], y=[0, y_anim[i]], mode='lines', name='Radio Vector', line=dict(color='blue', dash='dash')),
                
                go.Scatter(x=[x_anim[i], an_x_punta[i]], y=[y_anim[i], an_y_punta[i]], mode='lines', line=dict(color='red', width=3), showlegend=False),
                go.Scatter(x=an_flecha_x[i], y=an_flecha_y[i], mode='lines', name='Dirección a_n (Roja)', line=dict(color='red', width=3)),
                
                go.Scatter(x=[x_anim[i], at_x_punta[i]], y=[y_anim[i], at_y_punta[i]], mode='lines', line=dict(color='orange', width=3), showlegend=False),
                go.Scatter(x=at_flecha_x[i], y=at_flecha_y[i], mode='lines', name='Dirección a_t (Naranja)', line=dict(color='orange', width=3))
            ],
            layout=go.Layout(
                title=dict(text=texto_cartel_inicial, x=0.05),
                xaxis=dict(title="Eje X (m)", scaleanchor="y", scaleratio=1, range=[-limite_eje, limite_eje], autorange=False),
                yaxis=dict(title="Eje Y (m)", range=[-limite_eje, limite_eje], autorange=False),
                height=550,
                hovermode=False,
                updatemenus=[dict(
                    type="buttons",
                    showactive=False,
                    buttons=[dict(
                        label="▶️ Reproducir Automático", 
                        method="animate", 
                        args=[None, dict(frame=dict(duration=40, redraw=True), fromcurrent=True, mode="immediate")]
                    )]
                )]
            ),
            # 5. ACTUALIZACIÓN EN VIVO: Metemos los valores que crecen en cada fotograma del bucle
            frames=[go.Frame(
                data=[
                    go.Scatter(x=x_pista, y=y_pista),             
                    go.Scatter(x=[x_anim[k]], y=[y_anim[k]]),     
                    go.Scatter(x=[0, x_anim[k]], y=[0, y_anim[k]]), 
                    go.Scatter(x=[x_anim[k], an_x_punta[k]], y=[y_anim[k], an_y_punta[k]]),
                    go.Scatter(x=an_flecha_x[k], y=an_flecha_y[k]),
                    go.Scatter(x=[x_anim[k], at_x_punta[k]], y=[y_anim[k], at_y_punta[k]]),
                    go.Scatter(x=at_flecha_x[k], y=at_flecha_y[k])
                ],
                layout=go.Layout(title=dict(text=f"Tiempo: {pasos_tiempo[k]:.2f} s | Vueltas: {vueltas_tiempo[k]:.2f} | Ac. Normal: {an_instantenea[k]:.2f} m/s² | Ac. Tangencial: {at_instantenea[k]:.2f} m/s² | Vel. Angular: {w_instantanea[k]:.2f} rad/s | Vel. Tangencial: {vt_instantenea[k]:.2f} m/s")),
                name=str(k)
            ) for k in range(len(pasos_tiempo))]
        )
        
        st.plotly_chart(fig, width='stretch')








