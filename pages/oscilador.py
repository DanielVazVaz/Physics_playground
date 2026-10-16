import math

import numpy as np
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots


class OsciladorAmortiguado:
    """Solución analítica de m·x'' + γ·x' + k·x = 0 con x(0)=x0 y x'(0)=v0."""

    def __init__(self, masa, k, gamma, x0, v0):
        self.masa, self.k, self.gamma = masa, k, gamma
        self.x0, self.v0 = x0, v0
        self.omega0 = math.sqrt(k / masa)
        self.alfa = gamma / (2 * masa)
        self.zeta = gamma / (2 * math.sqrt(k * masa))
        if math.isclose(self.zeta, 1.0, rel_tol=1e-9):
            self.regimen = "crítico"
        elif self.zeta < 1:
            self.regimen = "subamortiguado" if gamma > 0 else "sin amortiguamiento"
        else:
            self.regimen = "sobreamortiguado"

    @property
    def omega_amortiguada(self):
        return math.sqrt(max(self.omega0**2 - self.alfa**2, 0.0))

    @property
    def tau(self):
        return math.inf if self.gamma == 0 else 2 * self.masa / self.gamma

    @property
    def amplitud(self):
        """Amplitud A de x(t) = A·e^(−t/τ)·sin(ω_a·t + φ₀) (régimen subamortiguado)."""
        return math.hypot(self.x0, (self.v0 + self.alfa * self.x0) / self.omega_amortiguada)

    @property
    def fase(self):
        return math.atan2(self.x0, (self.v0 + self.alfa * self.x0) / self.omega_amortiguada)

    def periodo(self):
        omega = self.omega_amortiguada
        return 2 * math.pi / omega if self.regimen in (
            "subamortiguado", "sin amortiguamiento"
        ) else None

    def evolucion(self, t):
        """Devuelve posición, velocidad y aceleración para el array t."""
        alfa, x0, v0 = self.alfa, self.x0, self.v0
        if self.regimen in ("subamortiguado", "sin amortiguamiento"):
            wd = self.omega_amortiguada
            a_coef, b_coef = x0, (v0 + alfa * x0) / wd
            decaimiento = np.exp(-alfa * t)
            coseno, seno = np.cos(wd * t), np.sin(wd * t)
            x = decaimiento * (a_coef * coseno + b_coef * seno)
            v = decaimiento * (
                (-alfa * a_coef + wd * b_coef) * coseno
                + (-alfa * b_coef - wd * a_coef) * seno
            )
        elif self.regimen == "crítico":
            c2 = v0 + alfa * x0
            decaimiento = np.exp(-alfa * t)
            x = (x0 + c2 * t) * decaimiento
            v = (c2 - alfa * (x0 + c2 * t)) * decaimiento
        else:
            beta = math.sqrt(alfa**2 - self.omega0**2)
            r1, r2 = -alfa + beta, -alfa - beta
            c1 = (v0 - r2 * x0) / (r1 - r2)
            c2 = x0 - c1
            x = c1 * np.exp(r1 * t) + c2 * np.exp(r2 * t)
            v = c1 * r1 * np.exp(r1 * t) + c2 * r2 * np.exp(r2 * t)
        a = -(self.k * x + self.gamma * v) / self.masa
        return x, v, a


st.title("〰️ Movimiento oscilatorio")
tipo = st.radio(
    "Tipo de oscilador",
    ("Simple (sin rozamiento)", "Amortiguado (rozamiento viscoso)"),
    horizontal=True,
)
es_simple = tipo.startswith("Simple")
if es_simple:
    st.markdown(
        "Oscilador armónico sin rozamiento: la única fuerza es la recuperadora "
        "$-kx$. Cambia los parámetros y observa $x(t)$, $v(t)$ y $a(t)$."
    )
    st.latex(r"-k\,x = m\,\frac{d^2x}{dt^2}")
    st.caption("Todo en el SI: kg, N/m, m, m/s y s.")
else:
    st.markdown(
        "Oscilador armónico con rozamiento viscoso: la fuerza recuperadora "
        "$-kx$ y la fuerza de amortiguamiento $-\\gamma\\,dx/dt$ determinan la "
        "aceleración. Cambia los parámetros y observa $x(t)$, $v(t)$ y $a(t)$."
    )
    st.latex(r"-k\,x-\gamma\,\frac{dx}{dt}=m\,\frac{d^2x}{dt^2}")
    st.caption("Todo en el SI: kg, N/m, kg/s, m, m/s y s.")

columnas = st.columns(3)
with columnas[0]:
    masa = st.number_input("Masa m [kg]", min_value=1e-6, value=1.0, format="%.4e")
    k = st.number_input("Constante recuperadora k [N/m]", min_value=1e-6, value=10.0, format="%.4e")
with columnas[1]:
    if es_simple:
        gamma = 0.0
    else:
        gamma = st.number_input("Coeficiente de amortiguamiento γ [kg/s]", min_value=0.0, value=0.5, format="%.4e")
    t_final = st.number_input("Tiempo final [s]", min_value=1e-3, value=10.0, format="%.4e")
with columnas[2]:
    x0 = st.number_input("Posición inicial x₀ [m]", value=1.0, format="%.4e")
    v0 = st.number_input("Velocidad inicial v₀ [m/s]", value=0.0, format="%.4e")

oscilador = OsciladorAmortiguado(masa, k, gamma, x0, v0)
t = np.linspace(0, t_final, 2000)
x, v, a = oscilador.evolucion(t)
oscila = oscilador.regimen in ("subamortiguado", "sin amortiguamiento")

st.subheader("Solución analítica")
if es_simple:
    st.latex(r"x(t) = A\,\sin(\omega\,t + \phi_o) \qquad v(t) = A\,\omega\,\cos(\omega\,t + \phi_o) \qquad a(t) = -A\,\omega^2\,\sin(\omega\,t + \phi_o)")
    st.latex(r"\omega = \sqrt{\frac{k}{m}} \qquad T = \frac{2\pi}{\omega} \qquad A = \sqrt{x_0^2 + \left(\frac{v_0}{\omega}\right)^2}")
    with st.expander("¿Qué significa cada parámetro?", expanded=True):
        st.markdown(
            "- $A$: amplitud, el desplazamiento máximo respecto al equilibrio.\n"
            "- $\\omega$: frecuencia angular; depende solo de $k$ y $m$, no de la amplitud.\n"
            "- $T$: periodo, tiempo de una oscilación completa. $f = 1/T$.\n"
            "- $\\phi_o$: fase inicial, fijada por $x_0$ y $v_0$.\n"
            "- $k$: constante recuperadora; $m$: masa."
        )
    st.markdown("Con tus datos:")
    st.latex(
        rf"x(t) = {oscilador.amplitud:.4g}\,\sin({oscilador.omega0:.4g}\,t + {oscilador.fase:.4g})"
    )
else:
    st.latex(r"x(t) = x_o\,e^{-t/\tau}\,\sin(\omega_a\,t + \phi_o)")
    st.latex(r"\omega_a = \sqrt{\frac{k}{m} - \frac{1}{\tau^2}} \qquad \tau = 2\,\frac{m}{\gamma}")
    with st.expander("¿Qué significa cada parámetro?", expanded=True):
        st.markdown(
            "- $x_o$: amplitud inicial de la oscilación.\n"
            "- $\\tau$: tiempo de relajación; la amplitud cae un factor $e$ cada $\\tau$ segundos. "
            "Cuanto mayor es $\\gamma$, menor es $\\tau$ y antes se amortigua.\n"
            "- $\\omega_a$: frecuencia angular amortiguada, siempre menor que la natural "
            "$\\omega_0=\\sqrt{k/m}$. El periodo es $T = 2\\pi/\\omega_a$.\n"
            "- $\\phi_o$: fase inicial, fijada por $x(0)$ y $v(0)$.\n"
            "- $\\gamma$: coeficiente de rozamiento viscoso; $k$: constante recuperadora; "
            "$m$: masa."
        )
    if oscila:
        tau_txt = r"\infty" if oscilador.tau == math.inf else f"{oscilador.tau:.4g}"
        st.markdown("Con tus datos:")
        st.latex(
            rf"x(t) = {oscilador.amplitud:.4g}\,e^{{-t/{tau_txt}}}\,"
            rf"\sin({oscilador.omega_amortiguada:.4g}\,t + {oscilador.fase:.4g})"
        )
    elif oscilador.regimen == "crítico":
        st.markdown(
            "En amortiguamiento **crítico** ($\\omega_a=0$) no hay oscilación: "
            "$x(t) = (x_0 + c\\,t)\\,e^{-t/\\tau}$ con $c = v_0 + x_0/\\tau$."
        )
    else:
        st.markdown(
            "En régimen **sobreamortiguado** ($k/m < 1/\\tau^2$) no hay oscilación: "
            "$x(t) = c_1 e^{r_1 t} + c_2 e^{r_2 t}$ con "
            "$r_{1,2} = -1/\\tau \\pm \\sqrt{1/\\tau^2 - k/m}$."
        )

st.subheader("Resultados")
periodo = oscilador.periodo()
if es_simple:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Amplitud", f"{oscilador.amplitud:.4e} m")
    c2.metric("Frecuencia angular", f"{oscilador.omega0:.4e} rad/s")
    c3.metric("Periodo", f"{periodo:.4e} s")
    c4.metric("Frecuencia", f"{1 / periodo:.4e} Hz")
    c5, c6, c7 = st.columns(3)
    c5.metric("Fase inicial", f"{oscilador.fase:.4e} rad")
    c6.metric("Velocidad máxima", f"{oscilador.amplitud * oscilador.omega0:.4e} m/s")
    c7.metric("Energía mecánica", f"{0.5 * k * oscilador.amplitud**2:.4e} J")
else:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Régimen", oscilador.regimen.capitalize())
    c2.metric("Frecuencia natural", f"{oscilador.omega0:.4e} rad/s")
    c3.metric("Factor de amortiguamiento", f"{oscilador.zeta:.4e}")
    c4.metric("Periodo", "—" if periodo is None else f"{periodo:.4e} s")
    c5, c6, c7 = st.columns(3)
    c5.metric("Tiempo de relajación", "∞" if oscilador.tau == math.inf else f"{oscilador.tau:.4e} s")
    c6.metric("Frecuencia amortiguada", f"{oscilador.omega_amortiguada:.4e} rad/s")
    c7.metric("Fase inicial", f"{oscilador.fase:.4e} rad" if oscila else "—")

figura = make_subplots(
    rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.06,
    subplot_titles=("Posición x(t) [m]", "Velocidad v(t) [m/s]", "Aceleración a(t) [m/s²]"),
)
for fila, (serie, color) in enumerate(
    ((x, "#168aad"), (v, "#e76f51"), (a, "#2a9d8f")), start=1
):
    figura.add_trace(
        go.Scatter(x=t, y=serie, mode="lines", line=dict(color=color, width=2),
                   showlegend=False),
        row=fila, col=1,
    )
if oscila and gamma > 0:
    envolvente = oscilador.amplitud * np.exp(-t / oscilador.tau)
    for signo in (1, -1):
        figura.add_trace(
            go.Scatter(x=t, y=signo * envolvente, mode="lines",
                       line=dict(color="gray", dash="dash", width=1),
                       showlegend=False, hoverinfo="skip"),
            row=1, col=1,
        )
figura.update_xaxes(title_text="Tiempo [s]", row=3, col=1)
figura.update_layout(height=750, margin=dict(t=40, b=40))
st.plotly_chart(figura, width="stretch")
st.caption(
    "Las líneas discontinuas de la posición son la envolvente $\\pm x_o\\,e^{-t/\\tau}$."
    if not es_simple
    else "La velocidad está adelantada $\\pi/2$ respecto a la posición, y la aceleración "
    "es proporcional y de signo contrario a $x$: $a = -\\omega^2 x$."
)
