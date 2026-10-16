import math

import streamlit as st


VARIABLES = {
    "h": ("Altura de capilaridad", "m", 0.03),
    "gamma": ("Tensión superficial", "N/m", 0.0728),
    "theta": ("Ángulo de contacto", "°", 0.0),
    "rho": ("Densidad del líquido", "kg/m³", 1000.0),
    "r": ("Radio del capilar", "m", 4.9e-4),
    "g": ("Gravedad", "m/s²", 9.81),
}


class SolvadorJurin:
    """h = 2·γ·cos(θ) / (ρ·g·r), con θ en grados en la interfaz."""

    def resolver(self, incognita, datos):
        """Devuelve (datos completos, error) con la incógnita despejada."""
        try:
            valor = self._despejar(incognita, datos)
        except ZeroDivisionError:
            return None, "No se puede calcular con estos datos (división por cero)."
        except ValueError as excepcion:
            return None, str(excepcion)
        if incognita in ("gamma", "rho", "r", "g") and valor <= 0:
            return None, "No existe una solución físicamente válida (resultado ≤ 0)."
        return {**datos, incognita: valor}, None

    @staticmethod
    def _despejar(incognita, d):
        coseno = math.cos(math.radians(d["theta"])) if incognita != "theta" else None
        if incognita == "h":
            return 2 * d["gamma"] * coseno / (d["rho"] * d["g"] * d["r"])
        if incognita == "gamma":
            return d["h"] * d["rho"] * d["g"] * d["r"] / (2 * coseno)
        if incognita == "rho":
            return 2 * d["gamma"] * coseno / (d["h"] * d["g"] * d["r"])
        if incognita == "g":
            return 2 * d["gamma"] * coseno / (d["h"] * d["rho"] * d["r"])
        if incognita == "r":
            return 2 * d["gamma"] * coseno / (d["h"] * d["rho"] * d["g"])
        cos_theta = d["h"] * d["rho"] * d["g"] * d["r"] / (2 * d["gamma"])
        if abs(cos_theta) > 1:
            raise ValueError(
                "No hay solución: se necesitaría |cos θ| > 1 con estos datos."
            )
        return math.degrees(math.acos(cos_theta))


def _representar_capilar(h, theta):
    coseno = math.cos(math.radians(theta))
    nivel_exterior = 230
    saturacion = 1 - math.exp(-abs(h) / 0.05)
    desplazamiento = 110 * saturacion if h > 0 else -45 * saturacion
    nivel_interior = nivel_exterior - desplazamiento
    flecha_menisco = 12 * coseno
    x_izq, x_der, centro = 430, 470, 450
    color_liquido = "#7fc8e8"

    if h == 0:
        cota = ""
    else:
        cota = (
            f'<line x1="530" y1="{nivel_exterior}" x2="600" y2="{nivel_exterior}" '
            'stroke="#6c757d" stroke-dasharray="5 4"/>'
            f'<line x1="530" y1="{nivel_interior:.1f}" x2="600" y2="{nivel_interior:.1f}" '
            'stroke="#6c757d" stroke-dasharray="5 4"/>'
            f'<line x1="580" y1="{nivel_exterior}" x2="580" y2="{nivel_interior:.1f}" '
            'stroke="#e76f51" stroke-width="3" marker-start="url(#cota)" '
            'marker-end="url(#cota)"/>'
            f'<text x="592" y="{(nivel_exterior + nivel_interior) / 2 + 5:.1f}" '
            'font-size="15" fill="#19324d">h = '
            f'{h:.3e} m</text>'
        )

    return (
        '<svg viewBox="0 0 900 380" role="img" '
        'aria-label="Ascenso capilar en un tubo estrecho">'
        '<defs><marker id="cota" markerWidth="8" markerHeight="8" refX="4" '
        'refY="4" orient="auto-start-reverse"><path d="M0,8 L4,0 L8,8 z" '
        'fill="#e76f51"/></marker></defs>'
        f'<rect x="150" y="{nivel_exterior}" width="600" height="130" '
        f'fill="{color_liquido}" fill-opacity="0.6"/>'
        '<path d="M150 150 V350 H750 V150" fill="none" stroke="#19324d" '
        'stroke-width="4"/>'
        f'<rect x="{x_izq}" y="{nivel_interior:.1f}" width="{x_der - x_izq}" '
        f'height="{300 - nivel_interior:.1f}" fill="{color_liquido}"/>'
        f'<path d="M{x_izq} {nivel_interior:.1f} Q{centro} '
        f'{nivel_interior + 2 * flecha_menisco:.1f} {x_der} {nivel_interior:.1f}" '
        f'fill="{color_liquido}" stroke="#19324d" stroke-width="2"/>'
        f'<line x1="{x_izq}" y1="40" x2="{x_izq}" y2="300" stroke="#19324d" '
        'stroke-width="4"/>'
        f'<line x1="{x_der}" y1="40" x2="{x_der}" y2="300" stroke="#19324d" '
        'stroke-width="4"/>'
        '<line x1="430" y1="60" x2="470" y2="60" stroke="#6c757d" '
        'stroke-dasharray="3 3"/>'
        '<text x="300" y="70" text-anchor="middle" font-size="14" '
        'fill="#19324d">Diámetro = 2r</text>'
        '<text x="160" y="140" font-size="13" fill="#19324d">Depósito abierto '
        '(nivel exterior)</text>'
        f'<text x="{centro}" y="30" text-anchor="middle" font-size="13" '
        f'fill="#19324d">θ<tspan font-size="10" dy="4">c</tspan>'
        f'<tspan dy="-4"> = {theta:.4g}°</tspan></text>'
        f"{cota}</svg>"
    )


st.title("🧪 Laboratorio Virtual de Fluidos: Ley de Jurin")
st.markdown(
    "Altura que alcanza (o desciende) un líquido en un capilar por el "
    "equilibrio entre la tensión superficial y el peso de la columna."
)
st.latex(r"h = \frac{2\,\gamma\,\cos\theta_c}{\rho_{liq}\,g\,r}")
st.caption(
    "Todo en el SI, salvo el ángulo de contacto en grados. Si θ < 90° el "
    "líquido moja y sube (h > 0); si θ > 90° no moja y desciende (h < 0)."
)

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
    minimo = {"h": None, "theta": 0.0}.get(clave, 1e-30)
    with columnas[indice % 3]:
        datos[clave] = st.number_input(
            f"{nombre} [{unidad}]",
            min_value=minimo,
            max_value=180.0 if clave == "theta" else None,
            value=inicial,
            format="%.4e",
            key=f"jurin_{clave}",
        )
    indice += 1

datos, error = SolvadorJurin().resolver(incognita, datos)
if error:
    st.error(error)
    st.stop()

st.subheader("Resultados")
nombre, unidad, _ = VARIABLES[incognita]
c1, c2 = st.columns(2)
c1.metric(nombre, f"{datos[incognita]:.4e} {unidad}")
c2.metric("Coseno del ángulo", f"{math.cos(math.radians(datos['theta'])):.4f}")

if datos["h"] > 0:
    st.info("El líquido **asciende** por el capilar (moja la pared).")
elif datos["h"] < 0:
    st.info("El líquido **desciende** en el capilar (no moja la pared).")
else:
    st.success("θ = 90°: no hay ascenso ni descenso capilar.")

st.subheader("Esquema del sistema")
st.markdown(_representar_capilar(datos["h"], datos["theta"]), unsafe_allow_html=True)
st.caption(
    "Esquema ilustrativo: la altura dibujada crece con h pero no está a escala."
)
