import streamlit as st


R = 8.314  # J/(mol·K)
CLAVES = ("P1", "P2", "C1", "C2", "T")
NOMBRES = {
    "P1": "Presión hidrostática en el lado 1 [Pa]",
    "P2": "Presión hidrostática en el lado 2 [Pa]",
    "C1": "Concentración de soluto en el lado 1 [mol/m³]",
    "C2": "Concentración de soluto en el lado 2 [mol/m³]",
    "T": "Temperatura [K]",
}
VALORES_INICIALES = {"P1": 0.0, "P2": 0.0, "C1": 300.0, "C2": 100.0, "T": 310.0}


def _resolver_equilibrio(datos, incognita):
    """Resuelve ΔP = R·T·ΔC para la incógnita. Presiones en Pa, C en mol/m³, T en K."""
    p1, p2, c1, c2, temp = (datos.get(clave) for clave in CLAVES)
    if incognita == "P1":
        valor = p2 + R * temp * (c1 - c2)
    elif incognita == "P2":
        valor = p1 - R * temp * (c1 - c2)
    elif incognita == "C1":
        valor = c2 + (p1 - p2) / (R * temp)
    elif incognita == "C2":
        valor = c1 - (p1 - p2) / (R * temp)
    else:
        if c1 == c2:
            return None, (
                "Con ΔC = 0 la temperatura no influye: el equilibrio solo se "
                "da si ΔP = 0."
            )
        valor = (p1 - p2) / (R * (c1 - c2))
    if valor < 0 or (incognita == "T" and valor == 0):
        return None, (
            "No existe una solución físicamente válida: el valor necesario "
            f"de {incognita} resulta negativo con los datos introducidos."
        )
    return valor, None


def _texto_presion(valor_pa):
    return f"{valor_pa:.4g} Pa"


def _representar_membrana(p1, p2, c1, c2, temp):
    pi1, pi2 = R * temp * c1, R * temp * c2
    neto1, neto2 = p1 - pi1, p2 - pi2
    diferencia = neto1 - neto2
    tolerancia = 1e-6 * max(abs(neto1), abs(neto2), 1.0)
    if abs(diferencia) <= tolerancia:
        flecha, color = "", "#6c757d"
    else:
        color = "#168aad"
        if diferencia > 0:
            flecha = (
                '<line x1="395" y1="150" x2="505" y2="150" stroke="#e76f51" '
                'stroke-width="6" marker-end="url(#flecha)"/>'
            )
        else:
            flecha = (
                '<line x1="505" y1="150" x2="395" y2="150" stroke="#e76f51" '
                'stroke-width="6" marker-end="url(#flecha)"/>'
            )

    cmax = max(c1, c2, 1e-12)
    opacidad1 = 0.15 + 0.6 * c1 / cmax
    opacidad2 = 0.15 + 0.6 * c2 / cmax

    def particulas(x0, cantidad):
        return "".join(
            f'<circle cx="{x0 + 30 + (i * 37) % 340}" '
            f'cy="{70 + (i * 53) % 190}" r="5" fill="#9b2226"/>'
            for i in range(cantidad)
        )

    n1 = round(25 * c1 / cmax)
    n2 = round(25 * c2 / cmax)

    def bloque(x0, lado, p, c, pi, neto, opacidad):
        return (
            f'<rect x="{x0}" y="50" width="400" height="230" fill="#168aad" '
            f'fill-opacity="{opacidad:.2f}" stroke="#19324d" stroke-width="2"/>'
            f'<text x="{x0 + 200}" y="32" text-anchor="middle" font-size="18" '
            f'font-weight="bold" fill="#19324d">Lado {lado}</text>'
        ), (
            f'<text x="{x0 + 200}" y="310" text-anchor="middle" font-size="14" '
            f'fill="#19324d">P = {_texto_presion(p)}</text>'
            f'<text x="{x0 + 200}" y="330" text-anchor="middle" font-size="14" '
            f'fill="#19324d">C = {c:.4g} mol/m³</text>'
            f'<text x="{x0 + 200}" y="350" text-anchor="middle" font-size="14" '
            f'fill="#9b2226">Π = {_texto_presion(pi)}</text>'
            f'<text x="{x0 + 200}" y="372" text-anchor="middle" font-size="14" '
            f'font-weight="bold" fill="#19324d">P − Π = '
            f'{_texto_presion(neto)}</text>'
        )

    caja1, texto1 = bloque(10, 1, p1, c1, pi1, neto1, opacidad1)
    caja2, texto2 = bloque(490, 2, p2, c2, pi2, neto2, opacidad2)
    return (
        '<svg viewBox="0 0 900 390" role="img" '
        'aria-label="Esquema de una membrana semipermeable">'
        '<defs><marker id="flecha" markerWidth="6" markerHeight="6" refX="4" '
        'refY="3" orient="auto"><path d="M0,0 L0,6 L6,3 z" fill="#e76f51"/>'
        '</marker></defs>'
        f"{caja1}{caja2}{particulas(10, n1)}{particulas(490, n2)}"
        f'<line x1="450" y1="40" x2="450" y2="290" stroke="#19324d" '
        'stroke-width="5" stroke-dasharray="10 6"/>'
        '<text x="450" y="20" text-anchor="middle" font-size="12" '
        'fill="#19324d">Membrana semipermeable</text>'
        f"{flecha}{texto1}{texto2}</svg>"
    )


st.title("🧫 Laboratorio Virtual de Fluidos: Ósmosis")
st.markdown(
    "Dos compartimentos están separados por una membrana semipermeable: deja "
    "pasar el disolvente (agua) pero no el soluto. El agua se desplaza hacia "
    "el lado con menor valor de **P − Π**."
)
st.latex(r"\Delta \Pi = R\,T\,\Delta C \qquad \Delta P = P_1 - P_2 \qquad \Delta C = C_1 - C_2")
st.latex(r"\text{Flujo de agua: } 1 \to 2 \text{ si } \Delta P > \Delta \Pi \qquad 2 \to 1 \text{ si } \Delta P < \Delta \Pi")
st.caption(
    "Se usa la concentración total de partículas osmóticamente activas "
    "para calcular la presión osmótica. Todas las magnitudes en el SI: Pa, mol/m³ y K. "
    "R = 8,314 J/(mol·K)."
)

modo = st.radio(
    "¿Qué quieres hacer?",
    (
        "a) Calcular el sentido del flujo",
        "b) Calcular el valor necesario para flujo nulo",
    ),
)
es_modo_b = modo.startswith("b")

incognita = None
if es_modo_b:
    incognita = st.selectbox(
        "Magnitud a calcular (el resto son datos)",
        CLAVES,
        format_func=lambda clave: NOMBRES[clave].split(" [")[0],
    )

st.subheader("Datos")
columnas = st.columns(3)
valores = {}
for indice, clave in enumerate(CLAVES):
    if clave == incognita:
        continue
    with columnas[indice % 3]:
        valores[clave] = st.number_input(
            NOMBRES[clave],
            min_value=None if clave[0] == "P" else 0.0,
            value=VALORES_INICIALES[clave],
            step=1000.0 if clave[0] == "P" else 1.0,
            format="%.4e",
            key=f"osmosis_{clave}",
        )

if valores.get("T", 1) <= 0:
    st.error("La temperatura debe ser superior al cero absoluto.")
    st.stop()

if es_modo_b:
    resultado, error = _resolver_equilibrio(valores, incognita)
    if error:
        st.error(error)
        st.stop()
    st.subheader("Resultado")
    unidad_resultado = {"P": "Pa", "C": "mol/m³", "T": "K"}[incognita[0]]
    st.metric(
        f"{NOMBRES[incognita].split(' [')[0]} para flujo nulo",
        f"{resultado:.4g} {unidad_resultado}",
    )
    valores[incognita] = resultado
    if incognita[0] == "T" and valores["C1"] == valores["C2"]:
        st.stop()

p1, p2, c1, c2, temp = (valores[clave] for clave in CLAVES)
delta_p = p1 - p2
delta_pi = R * temp * (c1 - c2)

st.subheader("Resultado" if not es_modo_b else "Comprobación")
col1, col2, col3 = st.columns(3)
col1.metric("ΔP = P₁ − P₂", _texto_presion(delta_p))
col2.metric("ΔΠ = R·T·(C₁ − C₂)", _texto_presion(delta_pi))
col3.metric("ΔP − ΔΠ", _texto_presion(delta_p - delta_pi))

tolerancia = 1e-6 * max(abs(delta_p), abs(delta_pi), 1.0)
if abs(delta_p - delta_pi) <= tolerancia:
    st.success("⚖️ Equilibrio: no hay flujo neto de agua a través de la membrana.")
elif delta_p > delta_pi:
    st.info("➡️ El agua fluye del **lado 1 al lado 2** (ΔP > ΔΠ).")
else:
    st.info("⬅️ El agua fluye del **lado 2 al lado 1** (ΔP < ΔΠ).")

st.subheader("Esquema del sistema")
st.markdown(_representar_membrana(p1, p2, c1, c2, temp), unsafe_allow_html=True)
st.caption(
    "Los puntos rojos representan la concentración de soluto. La flecha naranja "
    "indica el sentido del flujo de agua. Π = R·T·C es la presión osmótica de "
    "cada lado."
)
