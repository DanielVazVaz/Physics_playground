import numpy as np
import scipy.optimize as opt
import streamlit as st


GRAVEDAD = 9.81
VALORES_INICIALES = {"P": 101325.0, "v": 1.0, "z": 0.0, "A": 0.01, "Q": 0.01}
UNIDADES = {"P": "Pa", "v": "m/s", "z": "m", "A": "m²", "Q": "m³/s"}
NOMBRES = {
    "P": "Presión absoluta",
    "v": "Velocidad",
    "z": "Altura",
    "A": "Área de sección",
    "Q": "Caudal volumétrico",
}


def _claves_variables(num_puntos, misma_area=False):
    claves = []
    for indice in range(1, num_puntos + 1):
        claves.extend(f"{variable}{indice}" for variable in ("P", "v", "z"))
        if not misma_area:
            claves.append(f"A{indice}")
    if misma_area:
        claves.append("A")
    claves.append("Q")
    return claves


def _etiquetas_variables(num_puntos, misma_area=False):
    etiquetas = {}
    for indice in range(1, num_puntos + 1):
        for variable in ("P", "v", "z"):
            etiquetas[f"{variable}{indice}"] = (
                f"{NOMBRES[variable]} en el punto {indice} "
                f"[{UNIDADES[variable]}]"
            )
        if not misma_area:
            etiquetas[f"A{indice}"] = (
                f"{NOMBRES['A']} en el punto {indice} [{UNIDADES['A']}]"
            )
    if misma_area:
        etiquetas["A"] = f"{NOMBRES['A']} común [{UNIDADES['A']}]"
    etiquetas["Q"] = f"{NOMBRES['Q']} [m³/s]"
    return etiquetas


class SolvadorBernoulli:
    def __init__(self, num_puntos, densidad, misma_area=False):
        self.num_puntos = num_puntos
        self.densidad = densidad
        self.misma_area = misma_area
        self.vars = {}
        self.claves_desconocidas = []
        self.escalas = {}
        self.escala_energia = 1.0
        self.escala_caudal = 1.0

    def _residuos_bernoulli(self, valores_escalados):
        valores = self.vars.copy()
        for clave, valor in zip(self.claves_desconocidas, valores_escalados):
            variable = "Q" if clave == "Q" else clave.rstrip("0123456789")
            valores[clave] = valor * self.escalas[variable]

        energias = [
            valores[f"P{indice}"]
            + 0.5 * self.densidad * valores[f"v{indice}"] ** 2
            + self.densidad * GRAVEDAD * valores[f"z{indice}"]
            for indice in range(1, self.num_puntos + 1)
        ]
        balances_bernoulli = [
            (energia - energias[0]) / self.escala_energia
            for energia in energias[1:]
        ]
        balances_continuidad = [
            (
                valores["Q"]
                - (valores["A"] if self.misma_area else valores[f"A{indice}"])
                * valores[f"v{indice}"]
            )
            / self.escala_caudal
            for indice in range(1, self.num_puntos + 1)
        ]
        return balances_bernoulli + balances_continuidad

    def _resolver_presiones_area_comun(self, datos_conocidos):
        alturas_conocidas = all(
            f"z{indice}" in datos_conocidos
            for indice in range(1, self.num_puntos + 1)
        )
        presiones_conocidas = [
            indice
            for indice in range(1, self.num_puntos + 1)
            if f"P{indice}" in datos_conocidos
        ]
        if not alturas_conocidas or not presiones_conocidas:
            return False

        referencia = presiones_conocidas[0]
        presion_total = (
            datos_conocidos[f"P{referencia}"]
            + self.densidad * GRAVEDAD * datos_conocidos[f"z{referencia}"]
        )
        presiones_calculadas = {
            f"P{indice}": presion_total
            - self.densidad * GRAVEDAD * datos_conocidos[f"z{indice}"]
            for indice in range(1, self.num_puntos + 1)
        }
        for indice in presiones_conocidas:
            if not np.isclose(
                presiones_calculadas[f"P{indice}"],
                datos_conocidos[f"P{indice}"],
                rtol=1e-9,
                atol=1e-6,
            ):
                return False

        for clave in self.claves_desconocidas:
            self.vars[clave] = None
        self.vars.update(presiones_calculadas)
        self.vars.update(
            {
                f"A{indice}": self.vars["A"]
                for indice in range(1, self.num_puntos + 1)
            }
        )
        return True

    def resolver(self, datos_conocidos):
        claves = _claves_variables(self.num_puntos, self.misma_area)
        self.claves_desconocidas = [
            clave for clave in claves if clave not in datos_conocidos
        ]
        valores_base = VALORES_INICIALES.copy()
        self.vars = {
            f"{variable}{indice}": valores_base[variable]
            for indice in range(1, self.num_puntos + 1)
            for variable in ("P", "v", "z", "A")
        }
        self.vars["Q"] = valores_base["Q"]
        if self.misma_area:
            self.vars["A"] = valores_base["A"]
        self.vars.update(datos_conocidos)
        if self.misma_area:
            self.vars.update(
                {
                    f"A{indice}": self.vars["A"]
                    for indice in range(1, self.num_puntos + 1)
                }
            )

        presiones = [
            abs(self.vars[f"P{indice}"])
            for indice in range(1, self.num_puntos + 1)
        ]
        velocidades = [
            abs(self.vars[f"v{indice}"])
            for indice in range(1, self.num_puntos + 1)
        ]
        alturas = [
            abs(self.vars[f"z{indice}"])
            for indice in range(1, self.num_puntos + 1)
        ]
        areas = (
            [abs(self.vars["A"])]
            if self.misma_area
            else [
                abs(self.vars[f"A{indice}"])
                for indice in range(1, self.num_puntos + 1)
            ]
        )
        escala_presion = max(
            1e4,
            *presiones,
            self.densidad * GRAVEDAD * max(1.0, *alturas),
            0.5
            * self.densidad
            * max(1.0, *(velocidad**2 for velocidad in velocidades)),
        )
        escala_velocidad = max(
            1.0,
            *velocidades,
            np.sqrt(2.0 * escala_presion / self.densidad),
        )
        escala_altura = max(1.0, *alturas)
        escala_area = max(1e-4, *areas)
        self.escala_caudal = max(
            1e-4,
            abs(self.vars["Q"]),
            escala_area * escala_velocidad,
        )
        self.escalas = {
            "P": escala_presion,
            "v": escala_velocidad,
            "z": escala_altura,
            "A": escala_area,
            "Q": self.escala_caudal,
        }
        self.escala_energia = max(
            escala_presion,
            self.densidad
            * (escala_velocidad**2 + GRAVEDAD * escala_altura),
        )

        valores_iniciales = {}
        for indice in range(1, self.num_puntos + 1):
            area_clave = "A" if self.misma_area else f"A{indice}"
            velocidad_clave = f"v{indice}"
            if (
                velocidad_clave in self.claves_desconocidas
                and "Q" in datos_conocidos
                and area_clave in datos_conocidos
                and datos_conocidos[area_clave] > 0
            ):
                valores_iniciales[velocidad_clave] = (
                    datos_conocidos["Q"] / datos_conocidos[area_clave]
                )
            if (
                area_clave in self.claves_desconocidas
                and "Q" in datos_conocidos
                and velocidad_clave in datos_conocidos
                and datos_conocidos[velocidad_clave] > 0
            ):
                valores_iniciales[area_clave] = (
                    datos_conocidos["Q"] / datos_conocidos[velocidad_clave]
                )

        caudales_conocidos = []
        if self.misma_area and "A" in datos_conocidos:
            caudales_conocidos.extend(
                datos_conocidos["A"] * datos_conocidos[f"v{indice}"]
                for indice in range(1, self.num_puntos + 1)
                if f"v{indice}" in datos_conocidos
            )
        elif not self.misma_area:
            caudales_conocidos.extend(
                datos_conocidos[f"A{indice}"] * datos_conocidos[f"v{indice}"]
                for indice in range(1, self.num_puntos + 1)
                if f"A{indice}" in datos_conocidos
                and f"v{indice}" in datos_conocidos
            )
        if "Q" in self.claves_desconocidas and caudales_conocidos:
            valores_iniciales["Q"] = float(np.mean(caudales_conocidos))

        valores_escalados_iniciales = []
        limites_inferiores = []
        limites_superiores = []
        for clave in self.claves_desconocidas:
            variable = "Q" if clave == "Q" else clave.rstrip("0123456789")
            valor_inicial = valores_iniciales.get(clave, valores_base[variable])
            if variable in ("P", "v", "A", "Q"):
                valor_inicial = max(valor_inicial, self.escalas[variable] * 1e-6)
                limites_inferiores.append(0.0)
                limites_superiores.append(np.inf)
            else:
                limites_inferiores.append(-np.inf)
                limites_superiores.append(np.inf)
            valores_escalados_iniciales.append(
                valor_inicial / self.escalas[variable]
            )

        if not self.claves_desconocidas:
            if np.max(np.abs(self._residuos_bernoulli([]))) > 1e-7:
                return None, (
                    "Los datos introducidos son incompatibles con Bernoulli "
                    "y la continuidad."
                )
            return self.vars, None

        solucion = opt.least_squares(
            self._residuos_bernoulli,
            valores_escalados_iniciales,
            bounds=(limites_inferiores, limites_superiores),
            max_nfev=5000,
            ftol=1e-12,
            xtol=1e-12,
            gtol=1e-12,
        )
        if (
            not solucion.success
            or np.max(np.abs(self._residuos_bernoulli(solucion.x))) > 1e-7
        ):
            return None, (
                "No se encontró una solución compatible con los datos introducidos. "
                "Comprueba las condiciones iniciales y las unidades."
            )
        if np.linalg.matrix_rank(solucion.jac) < len(self.claves_desconocidas):
            if self.misma_area and self._resolver_presiones_area_comun(
                datos_conocidos
            ):
                return self.vars, None
            return None, (
                "Esta selección no determina una solución única. "
                "Prueba a cambiar cuáles variables conoces."
            )

        for clave, valor in zip(self.claves_desconocidas, solucion.x):
            variable = "Q" if clave == "Q" else clave.rstrip("0123456789")
            self.vars[clave] = float(valor * self.escalas[variable])
        if self.misma_area:
            self.vars.update(
                {
                    f"A{indice}": self.vars["A"]
                    for indice in range(1, self.num_puntos + 1)
                }
            )
        return self.vars, None


def _representar_sistema(estado, num_puntos):
    alturas = [estado[f"z{indice}"] for indice in range(1, num_puntos + 1)]
    areas = [estado[f"A{indice}"] for indice in range(1, num_puntos + 1)]
    altura_min = min(alturas)
    rango_alturas = max(alturas) - altura_min
    areas_conocidas = [area for area in areas if area is not None]
    area_min = min(areas_conocidas) if areas_conocidas else None
    area_max = max(areas_conocidas) if areas_conocidas else None
    ancho = 900
    posiciones = [
        65 + indice * 770 / max(num_puntos - 1, 1)
        for indice in range(num_puntos)
    ]
    niveles = [
        130 - 55 * (altura - altura_min) / rango_alturas
        if rango_alturas
        else 105
        for altura in alturas
    ]

    trazado = [f"M 25 {niveles[0]:.1f}", f"H {posiciones[0]:.1f}"]
    for indice in range(num_puntos - 1):
        punto_medio = (posiciones[indice] + posiciones[indice + 1]) / 2
        trazado.extend(
            (
                f"H {punto_medio:.1f}",
                f"V {niveles[indice + 1]:.1f}",
                f"H {posiciones[indice + 1]:.1f}",
            )
        )
    tuberia = (
        f'<path d="{" ".join(trazado)}" fill="none" stroke="#168aad" '
        'stroke-width="5" stroke-linejoin="round"/>'
    )
    flechas = "".join(
        f'<line x1="{posiciones[indice + 1] - 24:.1f}" '
        f'y1="{niveles[indice + 1]:.1f}" '
        f'x2="{posiciones[indice + 1] - 7:.1f}" '
        f'y2="{niveles[indice + 1]:.1f}" stroke="#168aad" stroke-width="3" '
        'marker-end="url(#flecha)"/>'
        for indice in range(num_puntos - 1)
    )
    puntos_svg = []
    for indice, (altura, area) in enumerate(zip(alturas, areas)):
        x, y = posiciones[indice], niveles[indice]
        radio = (
            7 + 4 * (area - area_min) / (area_max - area_min)
            if area is not None and area_max > area_min
            else 8
        )
        presion = estado[f"P{indice + 1}"]
        velocidad = estado[f"v{indice + 1}"]
        puntos_svg.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radio:.1f}" '
            'fill="white" stroke="#168aad" stroke-width="3"/>'
            f'<text x="{x:.1f}" y="{y - 22:.1f}" text-anchor="middle" '
            f'font-size="12" fill="#19324d">Punto {indice + 1}</text>'
            f'<text x="{x:.1f}" y="{y + 25:.1f}" text-anchor="middle" '
            f'font-size="10" fill="#526579">'
            f'{"Faltan datos" if presion is None else f"P={presion:.2e} Pa"}</text>'
            f'<text x="{x:.1f}" y="{y + 39:.1f}" text-anchor="middle" '
            f'font-size="10" fill="#526579">'
            f'{"v=Faltan datos" if velocidad is None else f"v={velocidad:.3g} m/s"}</text>'
            f'<text x="{x:.1f}" y="{y + 53:.1f}" text-anchor="middle" '
            f'font-size="10" fill="#526579">h={altura:.2f} m</text>'
        )
    return (
        f'<svg viewBox="0 0 {ancho} 230" role="img" '
        'aria-label="Esquema de una tubería con puntos de análisis">'
        '<defs><marker id="flecha" markerWidth="8" markerHeight="8" '
        'refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L7,3 z" '
        'fill="#168aad"/></marker></defs>'
        f"{tuberia}{flechas}{''.join(puntos_svg)}</svg>"
    )


st.title("💧 Laboratorio Virtual de Fluidos: Ecuación de Bernoulli")
st.markdown(
    "Resuelve el balance mecánico de un fluido ideal en régimen estacionario, "
    "sin pérdidas de carga ni ramificaciones. Se aplica conservación de caudal "
    "entre todos los puntos."
)
st.latex(r"P_i + \frac{1}{2}\rho v_i^2 + \rho g z_i = \mathrm{cte}")
st.latex(r"Q = A_i v_i")
st.caption(
    "Se usa presión absoluta, una densidad común y velocidad no negativa "
    "(sentido del flujo indicado en el esquema)."
)

num_puntos = st.number_input(
    "Número de puntos de análisis",
    min_value=2,
    max_value=8,
    value=2,
    step=1,
)
densidad = st.number_input(
    "Densidad del fluido (ρ) [kg/m³]",
    min_value=0.01,
    value=1000.0,
    step=10.0,
)
misma_area = st.checkbox("Usar la misma área de sección en todos los puntos")
claves = _claves_variables(num_puntos, misma_area)
etiquetas = _etiquetas_variables(num_puntos, misma_area)
clave_widget_seleccion = "bernoulli_datos_seleccionados"
seleccion_anterior = st.session_state.get(clave_widget_seleccion, [])
st.session_state[clave_widget_seleccion] = [
    clave for clave in seleccion_anterior if clave in claves
]

st.subheader("1. Selecciona tus datos conocidos")
datos_seleccionados = st.multiselect(
    "Elige las variables que conoces:",
    options=claves,
    key=clave_widget_seleccion,
    placeholder="Selecciona las magnitudes conocidas",
    format_func=lambda clave: etiquetas[clave],
)
if not datos_seleccionados:
    st.info("Selecciona las magnitudes que conoces para introducir sus valores.")
else:
    st.subheader("2. Introduce los valores conocidos")
    valores_usuario = {}
    columnas = st.columns(3)
    for indice, clave in enumerate(datos_seleccionados):
        variable = "Q" if clave == "Q" else clave.rstrip("0123456789")
        with columnas[indice % len(columnas)]:
            valores_usuario[clave] = st.number_input(
                etiquetas[clave],
                min_value=0.0 if variable in ("P", "v", "A", "Q") else None,
                value=VALORES_INICIALES[variable],
                step=0.1 if variable in ("v", "z") else 0.001,
                format="%.4e",
                key=f"bernoulli_{clave}",
            )

    motor = SolvadorBernoulli(num_puntos, densidad, misma_area)
    resultado, error = motor.resolver(valores_usuario)
    if error:
        st.error(error)
    else:
        st.subheader("3. Resultados")
        claves_calculadas = [clave for clave in claves if clave not in valores_usuario]
        columnas_resultados = st.columns(3)
        for indice, clave in enumerate(claves_calculadas):
            variable = "Q" if clave == "Q" else clave.rstrip("0123456789")
            with columnas_resultados[indice % len(columnas_resultados)]:
                st.metric(
                    etiquetas[clave],
                    "Faltan datos"
                    if resultado[clave] is None
                    else f"{resultado[clave]:.4e} {UNIDADES[variable]}",
                )

        st.subheader("Esquema del sistema")
        st.markdown(_representar_sistema(resultado, num_puntos), unsafe_allow_html=True)

        filas = []
        for indice in range(1, num_puntos + 1):
            presion = resultado[f"P{indice}"]
            velocidad = resultado[f"v{indice}"]
            altura = resultado[f"z{indice}"]
            area = resultado[f"A{indice}"]
            caudal = None if velocidad is None or area is None else area * velocidad
            energia = (
                None
                if velocidad is None or presion is None
                else presion
                + 0.5 * densidad * velocidad**2
                + densidad * GRAVEDAD * altura
            )
            filas.append(
                {
                    "Punto": indice,
                    "Presión (Pa)": "Faltan datos" if presion is None else f"{presion:.4e}",
                    "Velocidad (m/s)": "Faltan datos" if velocidad is None else f"{velocidad:.4e}",
                    "Altura (m)": f"{altura:.4e}",
                    "Área (m²)": "Faltan datos" if area is None else f"{area:.4e}",
                    "Caudal (m³/s)": "Faltan datos" if caudal is None else f"{caudal:.4e}",
                    "Energía mecánica por unidad de volumen (Pa)": (
                        "Faltan datos" if energia is None else f"{energia:.4e}"
                    ),
                }
            )
        st.dataframe(filas, hide_index=True, width='stretch')
