import streamlit as st
import numpy as np
import scipy.optimize as opt
import plotly.graph_objects as go

# --- ETAPA 1: Motor del Simulador Físico ---
class SolvadorTiroParabolico:
    def __init__(self):
        # Registro completo de las 9 variables físicas del sistema
        self.vars = {
            'g': 9.81,       # Aceleración de la gravedad (m/s²)
            'y0': None,      # Altura inicial de lanzamiento (m)
            'v0': None,      # Velocidad inicial total (m/s)
            'theta': None,   # Ángulo de lanzamiento (grados)
            'v0x': None,     # Velocidad inicial en el eje X (m/s)
            'v0y': None,     # Velocidad inicial en el eje Y (m/s)
            'x_f': None,     # Posición final / Alcance en X (m)
            'y_f': None,     # Altura final / Impacto en Y (m)
            'y_max': None,   # Altura máxima alcanzada (m)
            't': None        # Tiempo total de vuelo (s)
        }

    def _residuos_fisicos(self, valores_activos, claves_activas):
        estado = self.vars.copy()
        for clave, val in zip(claves_activas, valores_activos):
            estado[clave] = val

        # Convertimos el ángulo a radianes para las funciones trigonométricas
        rad = np.radians(estado['theta'])
        
        # Definición de las 5 ecuaciones cinemáticas fundamentales (todas igualadas a cero)
        res_v0x = estado['v0'] * np.cos(rad) - estado['v0x']
        res_v0y = estado['v0'] * np.sin(rad) - estado['v0y']
        res_x = estado['v0x'] * estado['t'] - estado['x_f']
        res_y = estado['y0'] + (estado['v0y'] * estado['t']) - (0.5 * estado['g'] * (estado['t']**2)) - estado['y_f']
        res_ymax = estado['y0'] + (estado['v0y']**2) / (2 * estado['g']) - estado['y_max']

        return [res_v0x, res_v0y, res_x, res_y, res_ymax]

    def resolver(self, datos_introducidos):
        # Reiniciar variables para el cálculo actual
        for clave in self.vars:
            if clave != 'g': self.vars[clave] = None
        self.vars.update(datos_introducidos)

        claves_activas = [k for k, v in self.vars.items() if v is None]
        
        # Inicialización inteligente de búsqueda para guiar al solucionador numérico
        valores_iniciales = []
        for k in claves_activas:
            if k == 't': valores_iniciales.append(5.0)  
            elif k in ['v0', 'v0x', 'v0y']: valores_iniciales.append(15.0)
            elif k == 'theta': valores_iniciales.append(45.0)
            elif k in ['y_max', 'x_f']: valores_iniciales.append(20.0)
            else: valores_iniciales.append(10.0)

        solucion_bruta, info, ier, msg = opt.fsolve(
            self._residuos_fisicos, 
            valores_iniciales, 
            args=(claves_activas,),
            full_output=True
        )

        if ier != 1:
            return False, "No se encontró una trayectoria válida. Revisa si tus datos tienen sentido físico (ej. la altura máxima no puede ser menor que la altura inicial)."

        for clave, valor_resuelto in zip(claves_activas, solucion_bruta):
            self.vars[clave] = valor_resuelto
            
        return True, self.vars

# --- ETAPA 2: Interfaz Gráfica con Streamlit ---
st.title("🎯 Laboratorio Virtual de Tiro Parabólico")
st.markdown("""
¡Bienvenido al tiro parabólico! Este sistema tiene **4 grados de libertad** por definir.
Selecciona **exactamente 4 datos conocidos**, introduce sus valores y observa cómo el motor calcula las incógnitas restantes de forma instantánea.
""")

nombres_variables = {
    'y0': 'Altura Inicial (y0) [m]',
    'v0': 'Velocidad Inicial Total (v0) [m/s]',
    'theta': 'Ángulo de Lanzamiento (theta) [grados]',
    'v0x': 'Velocidad Horizontal (v0x) [m/s]',
    'v0y': 'Velocidad Vertical (v0y) [m/s]',
    'x_f': 'Distancia Final / Alcance (x_f) [m]',
    'y_f': 'Altura Final (y_f) [m]',
    'y_max': 'Altura Máxima Alcanzada (y_max) [m]',
    't': 'Tiempo de Vuelo (t) [s]'
}

st.subheader("1. Selecciona tus 4 Datos Conocidos")
datos_seleccionados = st.multiselect(
    "Elige los 4 datos que vas a introducir de partida:",
    options=list(nombres_variables.keys()),
    default=['y0', 'v0', 'theta', 'y_f'],
    format_func=lambda x: nombres_variables[x]
)

num_seleccionados = len(datos_seleccionados)
if num_seleccionados != 4:
    st.info(f"💡 **Estado del sistema:** Has seleccionado **{num_seleccionados}/4** variables. Necesitas marcar exactamente 4 para bloquear el sistema matemático.")
else:
    st.success("✅ Número de grados de libertad fijados correctamente. Introduce los valores abajo.")
    
    st.subheader("2. Valores de los Datos Conocidos")
    columnas = st.columns(4)
    valores_usuario = {}
    
    for idx, clave in enumerate(datos_seleccionados):
        with columnas[idx % 4]:
            if clave == 'y0': valores_usuario['y0'] = st.number_input("$y_0$ (Altura inicial) [m]", value=0.0, step=1.0)
            elif clave == 'v0': valores_usuario['v0'] = st.number_input("$v_0$ (Velocidad inicial) [m/s]", min_value=0.01, value=25.0, step=1.0)
            elif clave == 'theta': valores_usuario['theta'] = st.number_input("$\\theta$ (Ángulo de lanzamiento) [°]", min_value = 0.0, max_value = 360.0, value = 45.0, step = 1.0)
            elif clave == 'v0x': valores_usuario['v0x'] = st.number_input("$v_{0x}$ (Velocidad X) [m/s]", min_value=0.1, value=20.0, step=1.0)
            elif clave == 'v0y': valores_usuario['v0y'] = st.number_input("$v_{0y}$ (Velocidad Y) [m/s]", value=10.0, step=1.0)
            elif clave == 'x_f': valores_usuario['x_f'] = st.number_input("$x_f$ (Alcance) [m]", min_value=0.1, value=50.0, step=1.0)
            elif clave == 'y_f': valores_usuario['y_f'] = st.number_input("$y_f$ (Altura impacto) [m]", value=0.0, step=1.0)
            elif clave == 'y_max': valores_usuario['y_max'] = st.number_input("$y_{max}$ (Altura máxima) [m]", min_value=0.0, value=15.0, step=1.0)
            elif clave == 't': valores_usuario['t'] = st.number_input("$t$ (Tiempo vuelo) [s]", min_value=0.00, value=3.0, step=0.1)

    # Ejecutar el motor matemático
    motor = SolvadorTiroParabolico()
    exito, resultado = motor.resolver(valores_usuario)

    if not exito:
        st.error(f"❌ {resultado}")
    else:
        with st.expander("📊 Ver Resultados de las Incógnitas Despejadas", expanded=True):
            columnas_res = st.columns(4)
            contador_c = 0
            traducciones_latex = {
                                    "y0": "$y_0$",
                                    "v0": "$v_0$",
                                    "theta": "$\\theta$",   # Usamos doble barra \\ para que Python no lo confunda con un comando de texto
                                    "v0x": "$v_{0x}$",
                                    "v0y": "$v_{0y}$",
                                    "x_f": "$x_f$",
                                    "y_f": "$y_f$",
                                    "y_max": "$y_{max}$",
                                    "t": "$t$"
                                }
            for clave, texto in nombres_variables.items():
                es_calculado = clave not in datos_seleccionados
                unidad = "m/s" if 'v0' in clave else "°" if clave=='theta' else "s" if clave=='t' else "m"
                etiqueta = ":red[(Calculado)]" if es_calculado else ":blue[(Dado)]"
                
                # 1. Separamos el texto limpio de la variable matemática
                nombre_sin_unidades = texto.split('[')[0].strip()
        
                variable_original = f"({clave})"
                
                # Buscamos en el diccionario usando la clave limpia
                variable_latex = traducciones_latex.get(clave, variable_original)
                nombre_con_latex = nombre_sin_unidades.replace(clave, variable_latex)
                with columnas_res[contador_c % 4]:
                    st.metric(
                        label=f"{nombre_con_latex} {etiqueta}",
                        value=f"{resultado[clave]:.2f} {unidad}",
                        delta="Resuelto" if es_calculado else None
                    )
                contador_c += 1

        # --- ETAPA 3: Gráfica con Puntos Clave ---
        st.subheader("3. Gráfica e Inspección Visual de la Trayectoria")
        vector_tiempo = np.linspace(0, resultado['t'], 200)
        coordenadas_x = resultado['v0x'] * vector_tiempo
        coordenadas_y = resultado['y0'] + (resultado['v0y'] * vector_tiempo) - (0.5 * resultado['g'] * (vector_tiempo ** 2))

        # Calculamos la posición X exacta donde ocurre la altura máxima para el gráfico
        t_al_vortex = resultado['v0y'] / resultado['g']
        x_al_vortex = resultado['v0x'] * t_al_vortex

        fig = go.Figure()
        
        # Curva de vuelo continua
        fig.add_trace(go.Scatter(x=coordenadas_x, y=coordenadas_y, mode='lines', name='Trayectoria', line=dict(color='#00CC96', width=4)))
        
        # Marcador del punto de salida inicial (origen en X=0)
        fig.add_trace(go.Scatter(x=[0.0], y=[resultado['y0']], mode='markers', name='Salida (y0)', marker=dict(color='blue', size=10)))
        
        # Marcador de la Altura Máxima (Vértice de la parábola)
        fig.add_trace(go.Scatter(x=[x_al_vortex], y=[resultado['y_max']], mode='markers', name='Altura Máx (y_max)', marker=dict(color='magenta', size=12, symbol='star')))
        
        # Marcador del Punto de Impacto Final objetivo
        fig.add_trace(go.Scatter(x=[resultado['x_f']], y=[resultado['y_f']], mode='markers', name='Impacto Final', marker=dict(color='orange', size=14, symbol='x')))

        fig.update_layout(
            xaxis_title="Distancia Horizontal (m)", 
            yaxis_title="Altura Vertical (m)", 
            hovermode="x unified", 
            height=600
        )
        st.plotly_chart(fig, width='stretch')

