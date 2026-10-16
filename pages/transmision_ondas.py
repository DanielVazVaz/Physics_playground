import math

import plotly.graph_objects as go
import streamlit as st

I_REF = 1e-12  # umbral de audición [W/m²]

PRESETS = {
    "Aire": (1.2, 343.0),
    "Agua": (1000.0, 1480.0),
    "Grasa": (920.0, 1450.0),
    "Tejido blando": (1060.0, 1540.0),
    "Sangre": (1060.0, 1570.0),
    "Músculo": (1070.0, 1580.0),
    "Hueso": (1900.0, 4080.0),
    "Personalizado": (1000.0, 1500.0),
}


def nivel_db(intensidad):
    """Nivel de intensidad β = 10·log10(I/I₀)."""
    return 10 * math.log10(intensidad / I_REF) if intensidad > 0 else -math.inf


class Medio:
    def __init__(self, nombre, rho, v, espesor=0.0):
        self.nombre, self.rho, self.v = nombre, rho, v
        self.espesor = espesor  # [m]

    @property
    def Z(self):
        return self.rho * self.v


class SolvadorTransmision:
    """Haz que atraviesa medios sucesivos separados por interfaces planas
    (incidencia normal, sin reflexiones múltiples)."""

    def __init__(self, medios):
        self.medios = medios

    @staticmethod
    def factores(Z1, Z2):
        r = Z2 / Z1
        R = ((r - 1) / (r + 1)) ** 2
        T = 4 * r / (r + 1) ** 2
        return r, R, T

    @staticmethod
    def intensidad_esferica(potencia, distancia):
        return potencia / (4 * math.pi * distancia**2)

    def resolver(self, I_primera_interfaz):
        """Una fila por interfaz con incidente, reflejada, transmitida y eco de vuelta."""
        filas = []
        I_inc = I_primera_interfaz
        factor_T_acumulado = 1.0
        for k in range(len(self.medios) - 1):
            m1, m2 = self.medios[k], self.medios[k + 1]
            r, R, T = self.factores(m1.Z, m2.Z)
            I_ref, I_tr = R * I_inc, T * I_inc
            I_eco = I_ref * factor_T_acumulado
            filas.append(
                dict(
                    k=k + 1, m1=m1, m2=m2, r=r, R=R, T=T, I_inc=I_inc,
                    I_ref=I_ref, I_tr=I_tr, I_eco=I_eco,
                    invertida=r < 1,
                )
            )
            factor_T_acumulado *= T
            I_inc = I_tr
            filas[-1]["I_sig"] = I_inc
        return filas


def fmt(x, unidad=""):
    return f"{x:.3e} {unidad}".strip()


def fmt_db(x):
    return "−∞ dB" if x == -math.inf else f"{x:.2f} dB"


def _color(Z):
    # Escala logarítmica de impedancia: del azul claro (aire) al marrón (hueso)
    t = min(max((math.log10(Z) - 2) / 4.5, 0), 1)
    r = int(190 - 80 * t)
    g = int(225 - 105 * t)
    b = int(245 - 175 * t)
    return f"rgb({r},{g},{b})"


def _representar(medios, filas):
    n = len(medios)
    ancho_total, alto = 900, 330
    margen = 20
    ancho = (ancho_total - 2 * margen) / n
    partes = [
        f'<svg viewBox="0 0 {ancho_total} {alto}" xmlns="http://www.w3.org/2000/svg" '
        'style="width:100%;max-width:900px;font-family:sans-serif">'
    ]
    for i, m in enumerate(medios):
        x = margen + i * ancho
        partes.append(
            f'<rect x="{x}" y="70" width="{ancho}" height="170" fill="{_color(m.Z)}" '
            'stroke="#555" stroke-width="1"/>'
        )
        cx = x + ancho / 2
        partes.append(
            f'<text x="{cx}" y="95" text-anchor="middle" font-size="14" font-weight="bold">{m.nombre}</text>'
            f'<text x="{cx}" y="115" text-anchor="middle" font-size="11">Z = {m.Z:.3e}</text>'
            f'<text x="{cx}" y="130" text-anchor="middle" font-size="10">kg/(m²·s)</text>'
        )
        if 0 < i < n - 1:
            partes.append(
                f'<text x="{cx}" y="225" text-anchor="middle" font-size="11">e = {m.espesor:.3g} m</text>'
            )
        # flecha incidente/transmitida (directa) en cada medio
        partes.append(
            f'<line x1="{x + 10}" y1="175" x2="{x + ancho - 10}" y2="175" stroke="#c0392b" '
            'stroke-width="3" marker-end="url(#fl)"/>'
        )
    partes.insert(
        1,
        '<defs><marker id="fl" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">'
        '<path d="M0,0 L8,4 L0,8 z" fill="#c0392b"/></marker>'
        '<marker id="fr" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">'
        '<path d="M0,0 L8,4 L0,8 z" fill="#2c7fb8"/></marker></defs>',
    )
    for fila in filas:
        xi = margen + fila["k"] * ancho
        partes.append(
            f'<line x1="{xi}" y1="55" x2="{xi}" y2="255" stroke="#222" stroke-width="3"/>'
            f'<line x1="{xi - 5}" y1="150" x2="{xi - ancho + 25}" y2="150" stroke="#2c7fb8" '
            'stroke-width="2.5" marker-end="url(#fr)"/>'
            f'<text x="{xi}" y="45" text-anchor="middle" font-size="12" font-weight="bold">'
            f'R = {fila["R"] * 100:.3g} %  ·  T = {fila["T"] * 100:.3g} %</text>'
            f'<text x="{xi - 8}" y="268" text-anchor="end" font-size="11" fill="#c0392b">'
            f'inc: {fmt_db(nivel_db(fila["I_inc"]))}</text>'
            f'<text x="{xi - 8}" y="284" text-anchor="end" font-size="11" fill="#2c7fb8">'
            f'ref: {fmt_db(nivel_db(fila["I_ref"]))}</text>'
            f'<text x="{xi + 8}" y="268" text-anchor="start" font-size="11" fill="#c0392b">'
            f'trans: {fmt_db(nivel_db(fila["I_tr"]))}</text>'
        )
    partes.append(
        '<text x="20" y="315" font-size="11" fill="#555">Rojo: onda incidente/transmitida · '
        'Azul: onda reflejada · Esquema sin escala</text></svg>'
    )
    return "".join(partes)


st.title("🔊 Transmisión de ondas entre medios")
st.markdown(
    "Una onda sonora de intensidad $I$ atraviesa varios medios (incidencia normal). "
    "En cada **interfaz** una parte se refleja y otra se transmite. Solo en el primer "
    "tramo (fuente puntual → primera interfaz) la intensidad disminuye con la distancia; "
    "dentro de los medios se supone que no se atenúa. Todo en unidades del SI."
)

st.markdown("### Fórmulas")
col_f1, col_f2 = st.columns(2)
with col_f1:
    st.latex(r"Z = \rho\, v \qquad r = \frac{Z_2}{Z_1}")
    st.latex(r"R = \frac{I_{ref}}{I_{inc}} = \left(\frac{r-1}{r+1}\right)^2")
    st.latex(r"T = \frac{I_{tr}}{I_{inc}} = \frac{4r}{(r+1)^2} \qquad R + T = 1")
with col_f2:
    st.latex(r"\beta = 10\,\log_{10}\frac{I}{I_0} \qquad I_0 = 10^{-12}\ \mathrm{W/m^2}")
    st.latex(r"I = \frac{P}{S} = \frac{P}{4\pi d^2} \quad (\text{fuente puntual})")
st.caption(
    "Si $r < 1$ ($Z_2 < Z_1$) la onda de presión se refleja invertida. "
    "Se ignoran las reflexiones múltiples dentro de las capas."
)

# ---------- Entradas ----------
st.markdown("### Datos")
n = st.number_input("Número de medios", min_value=2, max_value=5, value=3, step=1)

medios = []
columnas = st.columns(n)
for i, col in enumerate(columnas):
    with col:
        st.markdown(f"**Medio {i + 1}**")
        preset = st.selectbox(
            "Material", list(PRESETS), index=min(i, 3) if i < 4 else 1,
            key=f"preset_{i}",
        )
        rho0, v0 = PRESETS[preset]
        rho = st.number_input(
            "Densidad ρ [kg/m³]", min_value=1e-3, value=rho0, format="%.4e",
            key=f"rho_{i}_{preset}",
        )
        v = st.number_input(
            "Velocidad v [m/s]", min_value=1e-3, value=v0, format="%.4e",
            key=f"v_{i}_{preset}",
        )
        espesor = 0.0
        if 0 < i < n - 1:
            espesor = st.number_input(
                "Espesor e [m] (solo gráfica)", min_value=0.0, value=0.1, format="%.4e",
                key=f"esp_{i}",
            )
        nombre = preset if preset != "Personalizado" else f"Medio {i + 1}"
        medios.append(Medio(nombre, rho, v, espesor))

st.markdown("### Fuente")
modo = st.radio(
    "Dato de partida",
    ["Intensidad incidente en la primera interfaz", "Potencia de una fuente puntual"],
    horizontal=True,
)
if modo.startswith("Intensidad"):
    I0 = st.number_input(
        "Intensidad incidente $I_{inc}$ [W/m²]", min_value=1e-20, value=1e-3, format="%.4e"
    )
    I_primera = I0
else:
    P = st.number_input("Potencia emitida P [W]", min_value=1e-20, value=1.0, format="%.4e")
    d1 = st.number_input(
        "Distancia fuente–primera interfaz d [m]", min_value=1e-6, value=1.0, format="%.4e"
    )
    medios[0].espesor = d1
    I_primera = SolvadorTransmision.intensidad_esferica(P, d1)
    st.caption(
        f"Intensidad al llegar a la primera interfaz: {fmt(I_primera, 'W/m²')} "
        "(I = P/4πd²)."
    )

# ---------- Cálculo ----------
solver = SolvadorTransmision(medios)
filas = solver.resolver(I_primera)

st.markdown("### Esquema")
st.markdown(_representar(medios, filas), unsafe_allow_html=True)

st.markdown("### Resultados por interfaz")
for fila in filas:
    m1, m2 = fila["m1"], fila["m2"]
    with st.container(border=True):
        st.markdown(f"**Interfaz {fila['k']}: {m1.nombre} → {m2.nombre}**")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("r = Z₂/Z₁", f"{fila['r']:.4g}")
        c2.metric("Reflexión R", f"{fila['R'] * 100:.4g} %")
        c3.metric("Transmisión T", f"{fila['T'] * 100:.4g} %")
        c4.metric(
            "Pérdida por transmisión",
            fmt_db(-10 * math.log10(fila["T"])),
        )
        filas_tabla = [
            ("Incidente", fila["I_inc"]),
            ("Reflejada", fila["I_ref"]),
            ("Transmitida", fila["I_tr"]),
            ("Eco de vuelta a la 1ª interfaz", fila["I_eco"]),
        ]
        st.table(
            {
                "Onda": [n_ for n_, _ in filas_tabla],
                "Intensidad [W/m²]": [fmt(i) for _, i in filas_tabla],
                "Nivel [dB]": [fmt_db(nivel_db(i)) for _, i in filas_tabla],
            }
        )
        if fila["invertida"]:
            st.caption("Z₂ < Z₁: la onda reflejada sale invertida (cambio de fase de π).")

I_final = filas[-1]["I_tr"]
st.markdown("### Balance global")
st.table(
    {
        "Haz directo": ["Inicial (1ª interfaz)", "Final (último medio)"],
        "Intensidad [W/m²]": [fmt(I_primera), fmt(I_final)],
        "Nivel [dB]": [fmt_db(nivel_db(I_primera)), fmt_db(nivel_db(I_final))],
    }
)
st.metric("Pérdida total del haz directo", fmt_db(nivel_db(I_primera) - nivel_db(I_final)))
st.caption(
    "El eco de vuelta es la parte reflejada en la interfaz que regresa a la 1ª interfaz "
    "atravesando de nuevo las interfaces anteriores ($I_{eco}$)."
)

# ---------- Gráfica ----------
etiquetas = [f"{f['m1'].nombre} → {f['m2'].nombre}" for f in filas]
fig = go.Figure()
for clave, nombre, color in (
    ("T", "Transmitida", "#27ae60"),
    ("R", "Reflejada", "#2c7fb8"),
):
    fig.add_bar(
        x=etiquetas,
        y=[-10 * math.log10(f[clave]) if f[clave] > 0 else 0 for f in filas],
        name=nombre,
        marker_color=color,
        customdata=[[100 * f[clave]] for f in filas],
        hovertemplate="%{y:.3g} dB por debajo del incidente<br>"
        "(%{customdata[0]:.4g} % de la intensidad)<extra>" + nombre + "</extra>",
    )
fig.update_layout(
    barmode="group",
    yaxis_title="Atenuación respecto al incidente [dB]",
    yaxis_autorange="reversed",
    height=380,
    title="Cuánto baja cada onda respecto a la incidente (más abajo = más débil)",
)
st.plotly_chart(fig, width="stretch")
st.caption(
    "Atenuación = $-10\\log_{10} T$ (transmitida) y $-10\\log_{10} R$ (reflejada). "
    "En intensidad (W/m²) sí se cumple $I_{ref} + I_{tr} = I_{inc}$; en dB no se suman."
)
