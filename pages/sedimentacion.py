import math

import streamlit as st


def _flecha(x_inicio, x_fin, y, color, base, subindice, valor):
    if abs(x_fin - x_inicio) < 1:
        return ""
    x_texto = (x_inicio + x_fin) / 2
    return (
        f'<line x1="{x_inicio:.1f}" y1="{y}" x2="{x_fin:.1f}" y2="{y}" '
        f'stroke="{color}" stroke-width="5" marker-end="url(#punta-{color[1:]})"/>'
        f'<text x="{x_texto:.1f}" y="{y - 14}" text-anchor="middle" '
        f'font-size="14" fill="#19324d">{base}'
        f'<tspan font-size="10" dy="4">{subindice}</tspan>'
        f'<tspan dy="-4"> = {valor:.3e} N</tspan></text>'
        f'<defs><marker id="punta-{color[1:]}" markerWidth="6" markerHeight="6" '
        f'refX="4" refY="3" orient="auto"><path d="M0,0 L0,6 L6,3 z" '
        f'fill="{color}"/></marker></defs>'
    )


def _representar_fuerzas(f_centrifuga, f_arquimedes, f_arrastre):
    """Fuerzas sobre la partícula; el eje x positivo apunta hacia fuera del eje de giro."""
    maximo = max(abs(f_centrifuga), abs(f_arquimedes), abs(f_arrastre), 1e-300)
    escala = 300 / maximo
    centro = 450
    flechas = (
        _flecha(centro, centro + f_centrifuga * escala, 160,
                "#2a6fdb", "m·a", "c", f_centrifuga)
        + _flecha(centro, centro - f_arquimedes * escala, 90,
                  "#e76f51", "F", "A", f_arquimedes)
        + _flecha(centro, centro - f_arrastre * escala, 125,
                  "#2a9d8f", "F", "r", f_arrastre)
    )
    return (
        '<svg viewBox="0 0 900 230" role="img" '
        'aria-label="Fuerzas sobre una partícula en una centrífuga">'
        f'<circle cx="{centro}" cy="125" r="34" fill="#9b5b5b" stroke="#5c2e2e" '
        'stroke-width="3"/>'
        f'<line x1="10" y1="210" x2="890" y2="210" stroke="#6c757d" '
        'stroke-dasharray="6 4"/>'
        '<text x="12" y="200" font-size="12" fill="#6c757d">Eje de giro</text>'
        '<text x="888" y="200" text-anchor="end" font-size="12" '
        'fill="#6c757d">Hacia fuera (R<tspan font-size="9" dy="3">rot</tspan>'
        '<tspan dy="-3"> creciente)</tspan></text>'
        f"{flechas}</svg>"
    )


st.title("🌀 Sedimentación en centrífuga")
st.markdown(
    "Velocidad de sedimentación de una partícula en un medio que gira. En "
    "régimen estacionario la fuerza centrífuga se equilibra con el empuje y "
    "el arrastre viscoso."
)
st.latex(r"m\,a_c = F_A + F_r \quad\Rightarrow\quad v_s = \frac{V\,(\rho_{p}-\rho_{f})\,\omega^2\,R_{rot}}{\phi\,\mu\,R_{p}}")
st.latex(r"m\,a_c = \rho_p V \omega^2 R_{rot} \qquad F_A = \rho_f V \omega^2 R_{rot} \qquad F_r = \phi\,\mu\,R_p\,v_s")
st.caption(
    "Todo en el SI. Por defecto la partícula es una esfera: "
    "$V = \\frac{4}{3}\\pi R_p^3$ y $\\phi = 6\\pi$ (ley de Stokes)."
)

VARIABLES = {
    "v_s": ("Velocidad de sedimentación", "m/s", 7e-8),
    "rho_p": ("Densidad de la partícula", "kg/m³", 1350.0),
    "rho_f": ("Densidad del fluido", "kg/m³", 1000.0),
    "mu": ("Viscosidad del fluido", "Pa·s", 1e-3),
    "radio_p": ("Radio de la partícula", "m", 3e-9),
    "omega": ("Velocidad angular", "rad/s", 1000.0),
    "radio_rot": ("Radio de giro", "m", 0.1),
}
POSITIVAS = ("rho_p", "rho_f", "mu", "radio_p", "omega", "radio_rot")


class SolvadorSedimentacion:
    """v_s = V·(ρp − ρf)·ω²·R_rot / (φ·μ·R_p), con V y φ de esfera por defecto."""

    def __init__(self, phi=6 * math.pi, volumen_manual=None):
        self.phi = phi
        self.volumen_manual = volumen_manual

    def volumen(self, radio_p):
        if self.volumen_manual is not None:
            return self.volumen_manual
        return 4 / 3 * math.pi * radio_p**3

    @staticmethod
    def aceleracion(datos):
        return datos["omega"] ** 2 * datos["radio_rot"]

    def resolver(self, incognita, datos):
        """Devuelve (datos completos, error) con la incógnita despejada."""
        try:
            valor = self._despejar(incognita, datos)
        except ZeroDivisionError:
            return None, "No se puede calcular con estos datos (división por cero)."
        except ValueError as excepcion:
            return None, str(excepcion)
        if incognita in POSITIVAS and valor <= 0:
            return None, "No existe una solución físicamente válida (resultado ≤ 0)."
        return {**datos, incognita: valor}, None

    def _despejar(self, incognita, d):
        phi, a = self.phi, self.aceleracion(d)
        error_signo = ValueError(
            "No hay solución: el signo de v_s no es coherente con ρp − ρf."
        )
        delta_rho = d["rho_p"] - d["rho_f"]
        if incognita == "radio_p":
            if self.volumen_manual is not None:
                return (
                    self.volumen_manual * delta_rho * a
                    / (phi * d["mu"] * d["v_s"])
                )
            razon = 3 * d["v_s"] * phi * d["mu"] / (4 * math.pi * delta_rho * a)
            if razon <= 0:
                raise error_signo
            return math.sqrt(razon)

        rp = d["radio_p"]
        v = self.volumen(rp)
        if incognita == "v_s":
            return v * delta_rho * a / (phi * d["mu"] * rp)
        if incognita == "mu":
            return v * delta_rho * a / (phi * d["v_s"] * rp)
        arrastre = d["v_s"] * phi * d["mu"] * rp
        if incognita == "rho_p":
            return d["rho_f"] + arrastre / (v * a)
        if incognita == "rho_f":
            return d["rho_p"] - arrastre / (v * a)
        if incognita == "omega":
            razon = arrastre / (v * delta_rho * d["radio_rot"])
            if razon < 0:
                raise error_signo
            return math.sqrt(razon)
        return arrastre / (v * delta_rho * d["omega"] ** 2)

    def fuerzas(self, d):
        """Fuerzas [N] con el eje positivo hacia fuera del eje de giro."""
        volumen = self.volumen(d["radio_p"])
        a = self.aceleracion(d)
        centrifuga = d["rho_p"] * volumen * a
        arquimedes = d["rho_f"] * volumen * a
        return {
            "aceleracion": a,
            "masa": d["rho_p"] * volumen,
            "centrifuga": centrifuga,
            "arquimedes": arquimedes,
            "arrastre": centrifuga - arquimedes,
        }


incognita = st.selectbox(
    "Magnitud a calcular (el resto son datos)",
    list(VARIABLES),
    format_func=lambda clave: f"{VARIABLES[clave][0]} [{VARIABLES[clave][1]}]",
)

st.subheader("Datos")
columnas = st.columns(3)
datos = {}
indice = 0
for clave, (nombre, unidad, inicial) in VARIABLES.items():
    if clave == incognita:
        continue
    with columnas[indice % 3]:
        datos[clave] = st.number_input(
            f"{nombre} [{unidad}]",
            min_value=None if clave == "v_s" else 1e-30,
            value=inicial,
            format="%.4e",
            key=f"sed_{clave}",
        )
    indice += 1

with st.expander("Opciones avanzadas (partícula no esférica)"):
    usar_phi = st.checkbox("Usar un coeficiente φ distinto de 6π")
    phi = st.number_input(
        "Coeficiente de fricción φ [adimensional]",
        min_value=1e-9,
        value=6 * math.pi,
        disabled=not usar_phi,
    )
    usar_volumen = st.checkbox("Introducir el volumen manualmente")
    volumen_usuario = st.number_input(
        "Volumen de la partícula [m³]",
        min_value=1e-60,
        value=4 / 3 * math.pi * VARIABLES["radio_p"][2] ** 3,
        format="%.4e",
        disabled=not usar_volumen,
    )
solvador = SolvadorSedimentacion(
    phi=phi if usar_phi else 6 * math.pi,
    volumen_manual=volumen_usuario if usar_volumen else None,
)
datos, error = solvador.resolver(incognita, datos)
if error:
    st.error(error)
    st.stop()
fuerzas = solvador.fuerzas(datos)

st.subheader("Resultados")
nombre, unidad, _ = VARIABLES[incognita]
c1, c2, c3 = st.columns(3)
c1.metric(nombre, f"{datos[incognita]:.4e} {unidad}")
c2.metric("Aceleración centrífuga", f"{fuerzas['aceleracion']:.4e} m/s²")
c3.metric("Masa de la partícula", f"{fuerzas['masa']:.4e} kg")

v_s = datos["v_s"]
if v_s > 0:
    st.info("La partícula **sedimenta** (se aleja del eje de giro): $\\rho_p > \\rho_f$.")
elif v_s < 0:
    st.info("La partícula **flota** (se acerca al eje de giro): $\\rho_p < \\rho_f$.")
else:
    st.success("$\\rho_p = \\rho_f$: no hay movimiento neto de la partícula.")

st.subheader("Esquema de fuerzas")
st.markdown(
    _representar_fuerzas(
        fuerzas["centrifuga"], fuerzas["arquimedes"], fuerzas["arrastre"]
    ),
    unsafe_allow_html=True,
)
st.caption(
    "Longitudes de flecha proporcionales a cada fuerza. El arrastre "
    "$F_r = \\phi\\,\\mu\\,R_p\\,v_s$ "
    "se opone al movimiento; si la partícula flota, su flecha apunta hacia fuera."
)
