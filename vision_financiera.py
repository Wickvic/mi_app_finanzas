import streamlit as st
import pandas as pd
import uuid

def mostrar_vision_financiera(df_mov, df_presupuesto, obtener_saldos_iniciales, cuentas, meses, supabase):
    st.markdown("### 🔍 Visión Financiera")

    df_mov["fecha"] = pd.to_datetime(df_mov["fecha"], errors="coerce")
    df_mov["mes"] = df_mov["fecha"].dt.month
    df_mov["año"] = df_mov["fecha"].dt.year

    año_actual = pd.Timestamp.today().year
    df_mov_año = df_mov[df_mov["año"] == año_actual]

    with st.expander("📊 Comparativa anual gasto vs presupuesto"):
        with st.popover("ℹ️"):
            st.markdown("Compara el gasto real frente al presupuesto asignado por categoría para el año en curso. Te ayuda a detectar si estás gastando por encima o por debajo de tus previsiones.")
        gastos_por_categoria = (
            df_mov_año[df_mov_año["tipo"] == "gasto"]
            .groupby("categoria")["importe"].sum().reset_index()
        )
        presupuesto_anual = (
            df_presupuesto.groupby("categoria")["importe"].sum().reset_index()
        )
        comparativa = pd.merge(
            presupuesto_anual, gastos_por_categoria,
            on="categoria", how="outer"
        ).fillna(0)
        comparativa.columns = ["Categoria", "Presupuesto Anual", "Gasto Real"]
        comparativa["Diferencia"] = comparativa["Presupuesto Anual"] - comparativa["Gasto Real"]
        st.dataframe(comparativa)
        st.bar_chart(comparativa.set_index("Categoria")[["Presupuesto Anual", "Gasto Real"]])

    with st.expander("🏆 Ranking subcategorías más costosas"):
        with st.popover("ℹ️"):
            st.markdown("Muestra las 10 subcategorías donde más has gastado este año. Ideal para identificar patrones de gasto o excesos específicos.")
        ranking_gastos = (
            df_mov_año[df_mov_año["tipo"] == "gasto"]
            .groupby("subcategoria")["importe"].sum()
            .sort_values(ascending=False).head(10)
        )
        st.bar_chart(ranking_gastos)

    with st.expander("💼 Ingresos más significativos"):
        with st.popover("ℹ️"):
            st.markdown("Lista las principales fuentes de ingreso por subcategoría en el año actual. Útil para entender qué actividades generan más dinero")
        ranking_ingresos = (
            df_mov_año[df_mov_año["tipo"] == "ingreso"]
            .groupby("subcategoria")["importe"].sum()
            .sort_values(ascending=False).head(10)
        )
        st.bar_chart(ranking_ingresos)

    with st.expander("📈 Evolución ahorro neto acumulado"):
        with st.popover("ℹ️"):
            st.markdown("Representa la evolución del ahorro mensual neto a lo largo del año, sumando mes a mes.")
        ingresos = df_mov_año[df_mov_año["tipo"] == "ingreso"].groupby("mes")["importe"].sum()
        gastos = df_mov_año[df_mov_año["tipo"] == "gasto"].groupby("mes")["importe"].sum()
        ahorro_mensual = ingresos.subtract(gastos, fill_value=0).reindex(range(1, 13), fill_value=0)
        ahorro_acumulado = ahorro_mensual.cumsum()
        ahorro_acumulado.index = [meses[m - 1] for m in ahorro_acumulado.index]
        st.line_chart(ahorro_acumulado.rename("Ahorro neto acumulado"))

    with st.expander("📊 Comparativa ahorro neto entre años"):
        with st.popover("ℹ️"):
            st.markdown("Compara el ahorro neto (ingresos - gastos) entre distintos años")
        ahorro_ingresos = df_mov[df_mov["tipo"] == "ingreso"].groupby("año")["importe"].sum()
        ahorro_gastos = df_mov[df_mov["tipo"] == "gasto"].groupby("año")["importe"].sum()
        ahorro_anual = ahorro_ingresos.subtract(ahorro_gastos, fill_value=0).fillna(0).sort_index()
        st.bar_chart(ahorro_anual.rename("Ahorro neto por año"))

    with st.expander("🏦 Distribución por cuentas"):
        with st.popover("ℹ️"):
            st.markdown("Calcula el saldo final por cuenta, considerando ingresos, gastos y transferencias")

        df_saldos_raw = pd.DataFrame(obtener_saldos_iniciales())

        if df_saldos_raw.empty or "cuenta" not in df_saldos_raw.columns:
            st.warning("⚠️ No se han encontrado saldos iniciales válidos.")
        else:
            df_saldos = (
                df_saldos_raw[["cuenta", "saldo_inicial"]]
                .set_index("cuenta")
                .rename(columns={"saldo_inicial": "saldo"})
                .astype(float)
            )

            df_saldos["ingresos"] = df_mov[df_mov["tipo"] == "ingreso"].groupby("cuenta")["importe"].sum()
            df_saldos["gastos"] = df_mov[df_mov["tipo"] == "gasto"].groupby("cuenta")["importe"].sum()
            df_saldos["transferencias_recibidas"] = df_mov[df_mov["tipo"] == "transferencia"].groupby("hacia")["importe"].sum()
            df_saldos["transferencias_enviadas"] = df_mov[df_mov["tipo"] == "transferencia"].groupby("desde")["importe"].sum()

            df_saldos = df_saldos.fillna(0)

            df_saldos["saldo_final"] = (
                df_saldos["saldo"]
                + df_saldos["ingresos"]
                - df_saldos["gastos"]
                + df_saldos["transferencias_recibidas"]
                - df_saldos["transferencias_enviadas"]
            )

            st.dataframe(df_saldos[["saldo_final"]].sort_values("saldo_final", ascending=False))
    with st.expander("💪 Objetivos financieros (por cuenta)"):
        with st.popover("ℹ️"):
            st.markdown("Tasa de ahorro total acumulada sobre tus ingresos del año")
        df_obj = pd.DataFrame(supabase.table("objetivos").select("*").execute().data)
        if not df_obj.empty:
            df_saldos_df = pd.DataFrame(df_saldos_iniciales).set_index("cuenta")
            df_obj["monto"] = df_obj["monto"].astype(float)

            for _, row in df_obj.iterrows():
                cuenta = row["cuenta"]
                saldo_actual = df_saldos_df.loc[cuenta]["saldo"] if cuenta in df_saldos_df.index else 0
                progreso = min(saldo_actual / row["monto"], 1.0)
                st.write(f"**{row['descripcion']}** ({row['tipo']} - {cuenta}) — hasta el {row['fecha_limite']}")
                st.progress(progreso)
                st.caption(f"Progreso: {progreso*100:.1f}% — {saldo_actual:,.2f}€ / {row['monto']:,.2f}€")
                if st.button(f"❌ Eliminar {row['descripcion']}", key=f"del_{row['id']}"):
                    supabase.table("objetivos").delete().eq("id", row["id"]).execute()
                    st.experimental_rerun()

        with st.form("nuevo_objetivo"):
            col1, col2, col3 = st.columns(3)
            tipo = col1.selectbox("Tipo", ["Ahorro", "Inversión", "Deuda"])
            descripcion = col2.text_input("Descripción")
            cuenta = col3.selectbox("Cuenta asociada", cuentas)
            monto = st.number_input("Monto objetivo", min_value=0.0, format="%.2f")
            fecha_limite = st.date_input("Fecha límite")
            if st.form_submit_button("➕ Añadir objetivo"):
                supabase.table("objetivos").insert({
                    "tipo": tipo,
                    "descripcion": descripcion,
                    "cuenta": cuenta,
                    "monto": monto,
                    "fecha_limite": fecha_limite.isoformat()
                }).execute()
                st.success("🌟 Objetivo añadido correctamente")
                st.experimental_rerun()

    with st.expander("💪 Seguimiento manual de objetivos personales"):
        objetivos_financieros = supabase.table("objetivos_financieros").select("*").execute().data
        for obj in objetivos_financieros:
            progreso = obj["ahorrado"] / obj["meta"] if obj["meta"] else 0
            nuevo_ahorro = st.number_input(
                f'💰 {obj["nombre"]} → {obj["ahorrado"]:.0f} € / {obj["meta"]:.0f} €',
                min_value=0.0,
                max_value=obj["meta"],
                value=obj["ahorrado"],
                step=100.0,
                key=f"edit_ahorro_{obj['id']}"
            )
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("📂 Guardar", key=f"guardar_{obj['id']}"):
                    supabase.table("objetivos_financieros").update({
                        "ahorrado": nuevo_ahorro
                    }).eq("id", obj["id"]).execute()
                    st.success(f"Ahorro actualizado para '{obj['nombre']}'")
                    st.rerun()
            with col2:
                st.progress(progreso)
                st.caption(f"{progreso*100:.1f}% completado")

    with st.expander("➕ Añadir nuevo objetivo personal"):
        with st.form("nuevo_objetivo_financiero"):
            nombre = st.text_input("Nombre del objetivo", key="obj_nombre")
            meta = st.number_input("Meta (€)", min_value=0.0, format="%.2f", key="obj_meta")
            ahorrado = st.number_input("Ahorro inicial (€)", min_value=0.0, format="%.2f", key="obj_ahorrado")
            if st.form_submit_button("Guardar"):
                supabase.table("objetivos_financieros").insert({
                    "id": str(uuid.uuid4()),
                    "nombre": nombre,
                    "meta": meta,
                    "ahorrado": ahorrado
                }).execute()
                st.success("Objetivo personal añadido correctamente")
                st.rerun()
