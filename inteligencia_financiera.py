import streamlit as st
import pandas as pd

def mostrar_inteligencia_financiera(df_mov, df_presupuesto, df_ingresos, df_gastos, df_transf, cuentas, obtener_saldos_iniciales):
    st.title("🧠 Inteligencia Financiera")

    # — Preparar fechas y datos base —
    df_mov["fecha"] = pd.to_datetime(df_mov["fecha"], errors="coerce")
    df_mov["mes"]   = df_mov["fecha"].dt.month
    df_mov["año"]   = df_mov["fecha"].dt.year

    # 1) Porcentaje de ahorro mensual
    with st.expander("📊 Porcentaje de ahorro mensual"):
        if st.toggle("ℹ️", key="help_ahorro_mensual"):
            st.caption("Compara el porcentaje que logras ahorrar cada mes respecto a tus ingresos.")
        ingresos_mes  = df_ingresos.groupby(df_ingresos["fecha"].dt.month)["importe"].sum()
        gastos_mes    = df_gastos.groupby(df_gastos["fecha"].dt.month)["importe"].sum()
        porcentaje_ahorro = ((ingresos_mes - gastos_mes) / ingresos_mes).fillna(0) * 100
        st.line_chart(porcentaje_ahorro.rename("% Ahorro mensual"))

    # 2) Evolución interanual de ingresos y gastos
    with st.expander("📈 Evolución interanual de ingresos y gastos"):
        if st.toggle("ℹ️", key="help_evol_interanual"):
            st.caption("Visualiza cómo han variado tus ingresos y gastos a lo largo de los años.")
        ingresos_anuales = df_ingresos.groupby(df_ingresos["fecha"].dt.year)["importe"].sum()
        gastos_anuales   = df_gastos.groupby(df_gastos["fecha"].dt.year)["importe"].sum()
        df_evol = pd.DataFrame({"Ingresos": ingresos_anuales, "Gastos": gastos_anuales})
        st.bar_chart(df_evol)

    # 3) Ratio ingresos/gastos
    with st.expander("🧮 Ratio ingresos/gastos"):
        if st.toggle("ℹ️", key="help_ratio"):
            st.caption("Mide cuánto ingresas por cada euro que gastas. Ideal > 1.")
        ratio = ingresos_anuales / gastos_anuales
        st.dataframe(ratio.rename("Ratio ingresos/gastos"))

    # 4) Distribución por subcategoría
    with st.expander("📊 Distribución por subcategoría"):
        if st.toggle("ℹ️", key="help_top_gastos"):
            st.caption("Ranking de tus subcategorías de gasto con mayor impacto mensual.")
        top_gastos = (
            df_gastos
            .groupby("subcategoria")["importe"]
            .sum()
            .sort_values(ascending=False)
            .head(10)
        )
        st.bar_chart(top_gastos.rename("Top 10 gastos"))

        # 6) Porcentaje alcanzado por categoría respecto al presupuesto
    with st.expander("🎯 Porcentaje alcanzado por categoría respecto al presupuesto"):
        if st.toggle("ℹ️", key="help_ejecucion"):
            st.caption("Muestra cuánto has ejecutado del presupuesto por categoría.")
        presupuesto_total = df_presupuesto.groupby("categoria")["importe"].sum()
        gastos_total      = df_gastos.groupby("categoria")["importe"].sum()
        comparativa = (gastos_total / presupuesto_total).fillna(0) * 100
        st.dataframe(comparativa.rename("% ejecutado"))

    # 7) Promedio mensual por categoría
    with st.expander("💸 Promedio mensual por categoría"):
        if st.toggle("ℹ️", key="help_media_cat"):
            st.caption("Promedio mensual gastado por categoría durante el año actual.")
        df_gastos["mes"] = pd.to_datetime(df_gastos["fecha"], errors="coerce").dt.month
        media_cat = df_gastos.groupby("categoria")["importe"].mean()
        st.bar_chart(media_cat.rename("Media mensual por categoría"))

    # 8) Gasto inesperado (desviaciones)
    with st.expander("📊 Gasto inesperado (desviaciones)"):
        if st.toggle("ℹ️", key="help_desviacion"):
            st.caption("Muestra las categorías donde has gastado más de lo presupuestado.")
        df_presupuesto_total = df_presupuesto.groupby("categoria")["importe"].sum()
        df_gastos_total      = df_gastos.groupby("categoria")["importe"].sum()
        desviaciones = (df_gastos_total - df_presupuesto_total).fillna(0)
        desviaciones = desviaciones[desviaciones > 0].sort_values(ascending=False)
        st.bar_chart(desviaciones.rename("Desviación sobre presupuesto"))

    # 9) Porcentaje ahorro sobre ingreso por categoría
    with st.expander("📌 Porcentaje ahorro sobre ingreso por categoría"):
        if st.toggle("ℹ️", key="help_ahorro_categoria"):
            st.caption("Cuánto te queda de cada euro ingresado en función del gasto por categoría.")
        ingreso_total       = df_ingresos["importe"].sum()
        ahorro_por_categoria = ingreso_total - df_gastos.groupby("categoria")["importe"].sum()
        porcentaje = (ahorro_por_categoria / ingreso_total).fillna(0) * 100
        st.dataframe(porcentaje.rename("% ahorro por categoría"))

    # 10) Proyección de ahorro futuro con interés compuesto
    with st.expander("📈 Proyección de ahorro futuro con interés compuesto"):
        if st.toggle("ℹ️", key="help_proyeccion"):
            st.caption("Simula el crecimiento de tus ahorros en el tiempo con intereses.")
        capital_inicial = st.number_input("💰 Ahorro actual (€)", min_value=0.0, value=0.0)
        ahorro_mensual  = st.number_input("📥 Ahorro mensual (€)", min_value=0.0, value=0.0)
        interes_anual   = st.number_input("📊 Interés anual (%)", min_value=0.0, value=2.0)
        años            = st.slider("📆 Años de proyección", min_value=1, max_value=50, value=10)

        meses = años * 12
        interes_mensual = interes_anual / 100 / 12
        saldo = []
        total = capital_inicial
        for _ in range(meses):
            total = total * (1 + interes_mensual) + ahorro_mensual
            saldo.append(total)

        df_proy = pd.Series(saldo, name="Saldo proyectado")
        st.line_chart(df_proy)
        st.write(f"📌 Saldo final estimado: {total:,.2f} €")

    # 11) Simulador de presupuestos
    with st.expander("🧮 Simulador de presupuestos"):
        if st.toggle("ℹ️", key="help_simulador"):
            st.caption("Ajusta presupuestos por categoría y compara con gastos reales.")
        categorias = df_presupuesto["categoria"].unique().tolist()
        cambios = {}
        for cat in categorias:
            cambios[cat] = st.slider(f"Ajuste presupuesto {cat} (%)", -50, 100, 0)
        st.write("% Ajustes propuestos:", cambios)

        df_pres_ajustado = df_presupuesto.copy()
        df_pres_ajustado["ajuste_pct"] = df_pres_ajustado["categoria"].map(cambios)
        df_pres_ajustado["importe_ajustado"] = df_pres_ajustado["importe"] * (1 + df_pres_ajustado["ajuste_pct"] / 100)

        comparacion_final = pd.DataFrame({
            "Categoria": df_pres_ajustado["categoria"],
            "Presupuesto Original": df_pres_ajustado["importe"],
            "Presupuesto Ajustado": df_pres_ajustado["importe_ajustado"],
            "Gasto Real": df_gastos.groupby("categoria")["importe"].sum().reindex(df_pres_ajustado["categoria"]).values
        })
        comparacion_final["Diferencia Ajustado-Real"] = (
            comparacion_final["Presupuesto Ajustado"] - comparacion_final["Gasto Real"]
        )
        st.dataframe(comparacion_final)

    # 12) Objetivos financieros (en desarrollo)
    with st.expander("🎯 Objetivos financieros"):
        st.info("Define y sigue tus metas de ahorro o inversión")
        st.write("(En desarrollo)")

    # 13) Calendario de pagos (en desarrollo)
    with st.expander("📅 Calendario de pagos"):
        st.info("Recordatorio de pagos recurrentes")
        st.write("(En desarrollo)")

    # 14) Checklist financiero mensual (en desarrollo)
    with st.expander("🧾 Checklist financiero mensual"):
        st.info("Tareas recomendadas para fin de mes")
        st.write("(En desarrollo)")

    # 15) Alertas inteligentes (en desarrollo)
    with st.expander("📲 Alertas inteligentes"):
        st.info("Notificaciones automáticas basadas en reglas")
        st.write("(En desarrollo)")

    # 16) Ratios financieros personales
    with st.expander("📉 Ratios financieros personales"):
        with st.popover("ℹ️"):
            st.markdown("Tasa de ahorro total acumulada sobre tus ingresos del año")
        total_ingresos = df_ingresos["importe"].sum()
        total_gastos   = df_gastos["importe"].sum()
        tasa_ahorro    = (total_ingresos - total_gastos) / total_ingresos * 100 if total_ingresos else 0
        st.metric("Tasa de ahorro global (%)", f"{tasa_ahorro:.2f}%")

    # 17) Seguimiento independencia financiera
    with st.expander("🏁 Seguimiento independencia financiera"):
        with st.popover("ℹ️"):
            st.markdown("Calcula cuántos meses podrías vivir sin ingresos laborales")

        ingresos_pasivos = st.number_input("Ingresos pasivos mensuales (€)", min_value=0.0, value=0.0)
        gastos_medio     = df_gastos.groupby(df_gastos["fecha"].dt.month)["importe"].sum().mean()

        df_saldos_raw = pd.DataFrame(obtener_saldos_iniciales()).rename(columns={"saldo_inicial": "saldo"})

        if "cuenta" in df_saldos_raw.columns:
            df_saldos = df_saldos_raw.set_index("cuenta")
            df_saldos["saldo"] = df_saldos["saldo"].astype(float)

            df_saldos["saldo_final"] = (
                df_saldos["saldo"]
                + df_mov[df_mov["tipo"] == "ingreso"].groupby("cuenta")["importe"].sum().fillna(0)
                - df_mov[df_mov["tipo"] == "gasto"].groupby("cuenta")["importe"].sum().fillna(0)
                + df_mov[df_mov["tipo"] == "transferencia"].groupby("hacia")["importe"].sum().fillna(0)
                - df_mov[df_mov["tipo"] == "transferencia"].groupby("desde")["importe"].sum().fillna(0)
            )
            saldo_actual = df_saldos["saldo_final"].sum()
        else:
            saldo_actual = 0

        if gastos_medio > 0:
            meses_restantes = (saldo_actual + ingresos_pasivos * 12) / (gastos_medio * 12)
            st.metric("Meses hasta independencia financiera", f"{meses_restantes:.1f} meses")
        else:
            st.info("No hay datos suficientes para calcular independencia financiera")


    # 5) Evolución del saldo por cuenta
    with st.expander("💳 Evolución del saldo por cuenta"):
        with st.popover("ℹ️"):
            st.markdown("Muestra cómo evolucionan los saldos por cada cuenta bancaria")
        df_saldos_raw = pd.DataFrame(obtener_saldos_iniciales()).rename(columns={"saldo_inicial": "saldo"})
        if "cuenta" not in df_saldos_raw.columns:
            st.error("No se encontraron saldos iniciales")
            return

        df_saldos = df_saldos_raw.set_index("cuenta")
        df_saldos["saldo"]  = df_saldos["saldo"].astype(float)
        df_saldos["ingresos"] = (
            df_mov[df_mov["tipo"] == "ingreso"]
            .groupby("cuenta")["importe"]
            .sum()
        )
        df_saldos["gastos"] = (
            df_mov[df_mov["tipo"] == "gasto"]
            .groupby("cuenta")["importe"]
            .sum()
        )
        df_saldos["transferencias_recibidas"] = (
            df_mov[df_mov["tipo"] == "transferencia"]
            .groupby("hacia")["importe"]
            .sum()
        )
        df_saldos["transferencias_enviadas"] = (
            df_mov[df_mov["tipo"] == "transferencia"]
            .groupby("desde")["importe"]
            .sum()
        )

        df_saldos = df_saldos.fillna(0)
        df_saldos["saldo_final"] = (
            df_saldos["saldo"]
            + df_saldos["ingresos"]
            - df_saldos["gastos"]
            + df_saldos["transferencias_recibidas"]
            - df_saldos["transferencias_enviadas"]
        )
        st.bar_chart(df_saldos["saldo_final"].sort_values(ascending=False))


