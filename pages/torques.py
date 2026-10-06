import streamlit as st
import numpy as np
import scipy.optimize as opt
import plotly.graph_objects as go


class SolvadorTorques2D:
    def __init__(self, fuerzas, x_ref, y_ref):
        self.fuerzas = [dict(f) for f in fuerzas]
        self.x_ref = float(x_ref)
        self.y_ref = float(y_ref)
        self.unknowns = self._build_unknowns()

    # Ecuaciones de equilibrio usadas por el solver:
    # 1) sum(Fx) + Rx = 0
    # 2) sum(Fy) + Ry = 0
    # 3) sum(T_i) = 0, con T_i = r_x*F_y - r_y*F_x
    # Nota: en este modelo el soporte coincide con el punto de referencia,
    # por eso Rx y Ry no aportan momento.

    def _build_unknowns(self):
        unknowns = []
        for f in self.fuerzas:
            if f["mode"] == "Magnitud desconocida":
                unknowns.append((f"F{f['id']}", "force_mag", f["id"] - 1))
            elif f["mode"] == "Angulo desconocido":
                unknowns.append((f"theta{f['id']}", "force_ang", f["id"] - 1))
        unknowns.append(("Rx", "rx", None))
        unknowns.append(("Ry", "ry", None))
        return unknowns

    def _build_initial_guess_and_bounds(self):
        x0_vec = []
        lb = []
        ub = []

        for _, typ, idx in self.unknowns:
            if typ == "force_mag":
                x0_vec.append(10.0)
                # Permitimos magnitud algebraica (negativa) para indicar
                # direccion opuesta al angulo introducido.
                lb.append(-np.inf)
                ub.append(np.inf)
            elif typ == "force_ang":
                x0_vec.append(float(self.fuerzas[idx]["theta_rad"]))
                lb.append(-20.0 * np.pi)
                ub.append(20.0 * np.pi)
            elif typ in ["rx", "ry"]:
                x0_vec.append(0.0)
                lb.append(-np.inf)
                ub.append(np.inf)

        return np.array(x0_vec, dtype=float), np.array(lb, dtype=float), np.array(ub, dtype=float)

    def _force_components_and_torque(self, mag_i, theta_i, x_i, y_i):
        fx_i = mag_i * np.cos(theta_i)
        fy_i = mag_i * np.sin(theta_i)
        rxi = x_i - self.x_ref
        ryi = y_i - self.y_ref
        tau_i = rxi * fy_i - ryi * fx_i
        return fx_i, fy_i, tau_i

    def _build_state_from_unknown_vector(self, xvec):
        rx_val_local = 0.0
        ry_val_local = 0.0

        mags = [float(f["mag"]) if f["mag"] is not None else 0.0 for f in self.fuerzas]
        thetas = [float(f["theta_rad"]) for f in self.fuerzas]

        for value, (_, typ, idx) in zip(xvec, self.unknowns):
            if typ == "force_mag":
                mags[idx] = float(value)
            elif typ == "force_ang":
                thetas[idx] = float(value)
            elif typ == "rx":
                rx_val_local = float(value)
            elif typ == "ry":
                ry_val_local = float(value)

        return mags, thetas, rx_val_local, ry_val_local

    def _equation_sum_fx(self, mags, thetas, rx_val):
        sum_fx = 0.0
        for i_f, f in enumerate(self.fuerzas):
            fx_i, _, _ = self._force_components_and_torque(mags[i_f], thetas[i_f], f["x"], f["y"])
            sum_fx += fx_i
        return sum_fx + rx_val

    def _equation_sum_fy(self, mags, thetas, ry_val):
        sum_fy = 0.0
        for i_f, f in enumerate(self.fuerzas):
            _, fy_i, _ = self._force_components_and_torque(mags[i_f], thetas[i_f], f["x"], f["y"])
            sum_fy += fy_i
        return sum_fy + ry_val

    def _equation_sum_tau(self, mags, thetas):
        sum_tau = 0.0
        for i_f, f in enumerate(self.fuerzas):
            _, _, tau_i = self._force_components_and_torque(mags[i_f], thetas[i_f], f["x"], f["y"])
            sum_tau += tau_i
        return sum_tau

    def _residuals_equilibrium(self, xvec):
        mags, thetas, rx_val_local, ry_val_local = self._build_state_from_unknown_vector(xvec)

        eq_fx = self._equation_sum_fx(mags, thetas, rx_val_local)
        eq_fy = self._equation_sum_fy(mags, thetas, ry_val_local)
        eq_tau = self._equation_sum_tau(mags, thetas)

        return np.array([eq_fx, eq_fy, eq_tau], dtype=float)

    def resolver(self):
        unknown_count = len(self.unknowns)
        if unknown_count == 0:
            return {"status": "no_unknowns", "unknown_count": 0}
        if unknown_count > 3:
            return {"status": "too_many_unknowns", "unknown_count": unknown_count}

        x0_vec, lb, ub = self._build_initial_guess_and_bounds()
        sol = opt.least_squares(self._residuals_equilibrium, x0_vec, bounds=(lb, ub))
        resid = self._residuals_equilibrium(sol.x)
        norm_resid = float(np.linalg.norm(resid))
        tol_res = 1e-7

        if not sol.success or norm_resid > tol_res:
            return {
                "status": "incompatible",
                "unknown_count": unknown_count,
                "norm_resid": norm_resid,
            }

        rx_val = 0.0
        ry_val = 0.0

        for value, (_, typ, idx) in zip(sol.x, self.unknowns):
            if typ == "force_mag":
                self.fuerzas[idx]["mag"] = float(value)
            elif typ == "force_ang":
                self.fuerzas[idx]["theta_rad"] = float(value)
                self.fuerzas[idx]["theta_deg"] = float(np.degrees(value))
            elif typ == "rx":
                rx_val = float(value)
            elif typ == "ry":
                ry_val = float(value)

        fx_total = 0.0
        fy_total = 0.0
        tau_total = 0.0

        for f in self.fuerzas:
            mag = float(f["mag"])
            fx, fy, tau = self._force_components_and_torque(mag, f["theta_rad"], f["x"], f["y"])

            f["fx"] = fx
            f["fy"] = fy
            f["tau"] = tau

            fx_total += fx
            fy_total += fy
            tau_total += tau

        tau_reac = 0.0
        sum_fx_final = fx_total + rx_val
        sum_fy_final = fy_total + ry_val
        sum_tau_final = tau_total + tau_reac

        return {
            "status": "ok",
            "unknown_count": unknown_count,
            "fuerzas": self.fuerzas,
            "rx_val": rx_val,
            "ry_val": ry_val,
            "fx_total": fx_total,
            "fy_total": fy_total,
            "tau_total": tau_total,
            "tau_reac": tau_reac,
            "sum_fx_final": sum_fx_final,
            "sum_fy_final": sum_fy_final,
            "sum_tau_final": sum_tau_final,
        }


st.title("🧰 Laboratorio Virtual de Torques en estática")
st.markdown(
    r"""
Este modulo resuelve sistemas estaticos planos usando:
- $\sum F_x = 0$
- $\sum F_y = 0$
- $\sum T = 0$

El ángulo se mide siempre desde la horizontal positiva (eje x positivo) y el torque positivo es antihorario.
"""
)


st.subheader("1. Configuracion del Problema")
col_cfg1, col_cfg2, col_cfg3 = st.columns(3)
with col_cfg1:
    n_fuerzas = int(
        st.number_input("Numero de fuerzas externas", min_value=1, max_value=20, value=2, step=1)
    )
with col_cfg2:
    x_ref = st.number_input("$x_0$ del punto de referencia [m]", value=0.0, step=0.5)
with col_cfg3:
    y_ref = st.number_input("$y_0$ del punto de referencia [m]", value=0.0, step=0.5)

st.subheader("2. Definir Fuerzas Externas")
st.caption(
    "Para cada fuerza define su punto y selecciona si la magnitud o el angulo son datos o incognitas."
)

subindices = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")

fuerzas = []
for i in range(n_fuerzas):
    st.markdown(f"**Fuerza F{i + 1}**")
    c1, c2, c3 = st.columns(3)

    with c1:
        modo = st.selectbox(
            f"Modo F{str(i + 1).translate(subindices)}",
            options=["Definida", "Magnitud desconocida", "Angulo desconocido"],
            index=0,
            key=f"mode_{i}",
        )
    with c2:
        x_p = st.number_input(f"x{str(i + 1).translate(subindices)} [m]", value=float(i + 1), step=0.5, key=f"x_{i}")
    with c3:
        y_p = st.number_input(f"y{str(i + 1).translate(subindices)} [m]", value=0.0, step=0.5, key=f"y_{i}")

    c4, c5 = st.columns(2)
    if modo == "Definida":
        with c4:
            mag = st.number_input(
                f"|F{str(i + 1).translate(subindices)}| [N]",
                min_value=0.0,
                value=10.0,
                step=1.0,
                key=f"mag_{i}",
            )
        with c5:
            ang_deg = st.number_input(f"θ{str(i + 1).translate(subindices)} [grados]", value=90.0, step=5.0, key=f"theta_{i}")
    elif modo == "Magnitud desconocida":
        with c4:
            st.markdown("**|F| sera calculada**")
            mag = None
        with c5:
            ang_deg = st.number_input(f"θ{str(i + 1).translate(subindices)} [grados]", value=90.0, step=5.0, key=f"theta_{i}")
    else:
        with c4:
            mag = st.number_input(
                f"|F{str(i + 1).translate(subindices)}| [N]",
                min_value=0.0,
                value=10.0,
                step=1.0,
                key=f"mag_{i}",
            )
        with c5:
            st.markdown("**θ sera calculado**")
            ang_deg = 90.0

    fuerzas.append(
        {
            "id": i + 1,
            "mode": modo,
            "mag": mag,
            "x": x_p,
            "y": y_p,
            "theta_deg": ang_deg,
            "theta_rad": np.radians(ang_deg),
        }
    )

st.markdown("En este modulo, Rx y Ry son siempre incognitas y se calculan automaticamente.")
st.markdown("El soporte/referencia esta fijado en (x0, y0), por lo que Rx y Ry no aportan momento alrededor del punto de referencia.")

solver = SolvadorTorques2D(fuerzas=fuerzas, x_ref=x_ref, y_ref=y_ref)
resultado = solver.resolver()


if resultado["status"] == "no_unknowns":
    st.info("Selecciona al menos una incognita para resolver.")
elif resultado["status"] == "too_many_unknowns":
    st.info("Hay mas de 3 incognitas; no hay solucion unica sin ecuaciones adicionales.")
elif resultado["status"] == "incompatible":
    st.error(
        "No se encontro una solucion fisica compatible con las incognitas seleccionadas. "
        "Prueba otra combinacion de variables dadas/incognitas."
    )
else:
    fuerzas_resueltas = resultado["fuerzas"]
    rx_val = resultado["rx_val"]
    ry_val = resultado["ry_val"]
    fx_total = resultado["fx_total"]
    fy_total = resultado["fy_total"]
    tau_total = resultado["tau_total"]
    tau_reac = resultado["tau_reac"]
    sum_fx_final = resultado["sum_fx_final"]
    sum_fy_final = resultado["sum_fy_final"]
    sum_tau_final = resultado["sum_tau_final"]

    st.subheader("3. Resultados")
    r1, r2, r3 = st.columns(3)
    with r1:
        st.metric(r"$\sum F_x$ fuerzas [N]", f"{fx_total:.3f}")
        st.metric(r"$\sum F_y$ fuerzas [N]", f"{fy_total:.3f}")
    with r2:
        st.metric("Rx [N]", f"{rx_val:.3f}")
        st.metric("Ry [N]", f"{ry_val:.3f}")
    with r3:
        st.metric(r"$\sum T$ fuerzas [N m]", f"{tau_total:.3f}")

    st.markdown("### :green[Tabla de Variables]")
    tabla = []
    for f in fuerzas_resueltas:
        if f["mode"] == "Definida":
            estado = "Dada"
        elif f["mode"] == "Magnitud desconocida":
            estado = "Magnitud calculada"
        else:
            estado = "Angulo calculado"

        ang_norm = ((float(f["theta_deg"]) + 180.0) % 360.0) - 180.0
        tabla.append(
            {
                "Variable": f"F{str(f['id']).translate(subindices)}",
                "Estado": estado,
                "Magnitud [N]": round(float(f["mag"]), 6),
                "x [m]": round(f["x"], 3),
                "y [m]": round(f["y"], 3),
                "\u03b8 [grados]": round(ang_norm, 6),
                "Fx [N]": round(f["fx"], 6),
                "Fy [N]": round(f["fy"], 6),
                "Torque [N m]": round(f["tau"], 6),
            }
        )

    tabla.append(
        {
            "Variable": "Reacciones",
            "Estado": "Calculada",
            "Magnitud [N]": round(np.hypot(rx_val, ry_val), 6),
            "x [m]": round(x_ref, 3),
            "y [m]": round(y_ref, 3),
                "\u03b8 [grados]": round(np.degrees(np.arctan2(ry_val, rx_val)), 3)
            if abs(rx_val) + abs(ry_val) > 1e-12
            else 0.0,
            "Fx [N]": round(rx_val, 6),
            "Fy [N]": round(ry_val, 6),
            "Torque [N m]": round(tau_reac, 6),
        }
    )

    st.dataframe(tabla, width="stretch")

    st.subheader("4. Visualizacion")
    xs = [f["x"] for f in fuerzas_resueltas] + [x_ref]
    ys = [f["y"] for f in fuerzas_resueltas] + [y_ref]
    span = max(np.ptp(xs) if len(xs) > 1 else 1.0, np.ptp(ys) if len(ys) > 1 else 1.0, 1.0)

    max_comp_f = max(
        max(abs(f["fx"]) for f in fuerzas_resueltas),
        max(abs(f["fy"]) for f in fuerzas_resueltas),
        1e-9,
    )
    scale_f = (0.25 * span) / max_comp_f
    min_arrow_len = 0.08 * span

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=[x_ref],
            y=[y_ref],
            mode="markers+text",
            text=["Referencia"],
            textposition="top center",
            marker=dict(size=13, color="black", symbol="x"),
            name="Punto de momentos",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[x_ref],
            y=[y_ref],
            mode="markers+text",
            text=["Soporte"],
            textposition="bottom center",
            marker=dict(size=11, color="#2ca02c", symbol="diamond"),
            name="Punto de reaccion",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[f["x"] for f in fuerzas_resueltas],
            y=[f["y"] for f in fuerzas_resueltas],
            mode="markers+text",
            text=[f"F{f['id']}" for f in fuerzas_resueltas],
            textposition="top center",
            marker=dict(size=9, color="#1f77b4"),
            name="Puntos de aplicacion",
        )
    )

    for f in fuerzas_resueltas:
        x0p = f["x"]
        y0p = f["y"]
        dx = f["fx"] * scale_f
        dy = f["fy"] * scale_f
        arrow_len = float(np.hypot(dx, dy))
        if arrow_len < min_arrow_len and arrow_len > 1e-12:
            factor = min_arrow_len / arrow_len
            dx *= factor
            dy *= factor
        elif arrow_len <= 1e-12:
            dx = min_arrow_len
            dy = 0.0
        fig.add_annotation(
            x=x0p + dx,
            y=y0p + dy,
            ax=x0p,
            ay=y0p,
            xref="x",
            yref="y",
            axref="x",
            ayref="y",
            showarrow=True,
            arrowhead=3,
            arrowsize=1.0,
            arrowwidth=2,
            arrowcolor="#d62728",
        )
        fig.add_annotation(
            x=x0p + dx,
            y=y0p + dy,
            text=f"{abs(f['mag']):.2f} N",
            showarrow=False,
            yshift=10,
            font=dict(size=11, color="#d62728"),
        )

    if abs(rx_val) + abs(ry_val) > 1e-12:
        max_comp_r = max(abs(rx_val), abs(ry_val), 1e-9)
        scale_r = (0.35 * span) / max_comp_r
        fig.add_annotation(
            x=x_ref + rx_val * scale_r,
            y=y_ref + ry_val * scale_r,
            ax=x_ref,
            ay=y_ref,
            xref="x",
            yref="y",
            axref="x",
            ayref="y",
            showarrow=True,
            arrowhead=4,
            arrowsize=1.2,
            arrowwidth=3,
            arrowcolor="#2ca02c",
        )
        fig.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="markers",
                marker=dict(size=9, color="#2ca02c"),
                name="Reaccion",
            )
        )

    pad = 0.7 * span
    xmin, xmax = min(xs) - pad, max(xs) + pad
    ymin, ymax = min(ys) - pad, max(ys) + pad

    fig.update_layout(
        xaxis=dict(title="Eje X [m]", range=[xmin, xmax], scaleanchor="y", scaleratio=1),
        yaxis=dict(title="Eje Y [m]", range=[ymin, ymax]),
        height=620,
        showlegend=True,
    )

    st.plotly_chart(fig, width="stretch")
