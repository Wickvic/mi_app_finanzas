import streamlit as st
import pandas as pd
from datetime import date
import io
from xhtml2pdf import pisa
from supabase_client import supabase

def mostrar_dashboard(df_ingresos, df_gastos, df_transf, cuentas, meses, obtener_saldos_iniciales):

    df_saldos_raw = pd.DataFrame(obtener_saldos_iniciales()).rename(columns={"saldo_inicial": "saldo"})

    if "cuenta" in df_saldos_raw.columns:
        df_saldos = df_saldos_raw.set_index("cuenta")
        df_saldos["saldo"] = df_saldos["saldo"].astype(float)

        df_saldos["ingresos"] = (
            df_ingresos
            .groupby("cuenta")["importe"]
            .sum()
        )
        df_saldos["gastos"] = (
            df_gastos
            .groupby("cuenta")["importe"]
            .sum()
        )
        df_saldos["transferencias_recibidas"] = (
            df_transf
            .groupby("hacia")["importe"]
            .sum()
        )
        df_saldos["transferencias_enviadas"] = (
            df_transf
            .groupby("desde")["importe"]
            .sum()
        )

        df_saldos = df_saldos.fillna(0)
        df_saldos["saldo_actual"] = (
            df_saldos["saldo"]
            + df_saldos["ingresos"]
            - df_saldos["gastos"]
            + df_saldos["transferencias_recibidas"]
            - df_saldos["transferencias_enviadas"]
        )

        st.subheader("💳 Balance actual por cuenta")
        st.dataframe(df_saldos[["saldo_actual"]].sort_values(by="saldo_actual", ascending=False).style.format("{:.2f} €"))
        st.metric("💼 Total disponible", f"{df_saldos['saldo_actual'].sum():,.2f} €")
    else:
        st.warning("No se han encontrado saldos iniciales.")


    st.markdown("### 📤 Exportar datos")

    df_todos = pd.concat([df_ingresos, df_gastos, df_transf], ignore_index=True)

    if not df_todos.empty and "fecha" in df_todos.columns:
        df_todos["fecha"] = pd.to_datetime(df_todos["fecha"], errors="coerce")
    else:
        st.warning("No hay movimientos registrados o falta la columna 'fecha'")
        return

    col1, col2 = st.columns(2)

    with col1:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_todos.to_excel(writer, index=False, sheet_name="Movimientos")
        st.download_button("⬇️ Exportar TODO a Excel", data=output.getvalue(), file_name="historico_completo.xlsx")

    with col2:
        mes_actual = date.today().month
        año_actual = date.today().year
        df_mes = df_todos[(df_todos["fecha"].dt.month == mes_actual) & (df_todos["fecha"].dt.year == año_actual)]
        output_mes = io.BytesIO()
        with pd.ExcelWriter(output_mes, engine='xlsxwriter') as writer:
            df_mes.to_excel(writer, index=False, sheet_name="Mes actual")
        st.download_button("⬇️ Exportar MES actual a Excel", data=output_mes.getvalue(), file_name="mes_actual.xlsx")

    def df_to_pdf_bytes(df):
        html = df.to_html(index=False, border=0)
        html = f"<h2>Movimientos</h2>{html}"
        output = io.BytesIO()
        pisa.CreatePDF(io.StringIO(html), dest=output)
        return output.getvalue()

    st.markdown("### 📄 Exportar a PDF")

    col3, col4 = st.columns(2)

    with col3:
        pdf_todos = df_to_pdf_bytes(df_todos)
        st.download_button("🧾 Descargar TODO en PDF", data=pdf_todos, file_name="historico_completo.pdf", mime="application/pdf")

    with col4:
        pdf_mes = df_to_pdf_bytes(df_mes)
        st.download_button("🧾 Descargar MES actual en PDF", data=pdf_mes, file_name="mes_actual.pdf", mime="application/pdf")

    # Cargar movimientos desde supabase
    df_mov = pd.DataFrame(supabase.table("movimientos").select("*").execute().data)
    df_mov["fecha"] = pd.to_datetime(df_mov["fecha"], errors="coerce")
    df_mov = df_mov[df_mov["tipo"] == "gasto"]

    mes_actual = date.today().month
    año_actual = date.today().year
    df_mov_mes = df_mov[(df_mov["fecha"].dt.month == mes_actual) & (df_mov["fecha"].dt.year == año_actual)]

    df_gastos_mes = df_mov_mes.groupby("categoria")["importe"].sum().reset_index()
    df_gastos_mes.columns = ["categoria", "real"]

    df_presupuesto = pd.DataFrame(
        supabase.table("presupuestos").select("*").eq("mes", mes_actual).execute().data
    )

    # ✅ Validar que tiene datos y la columna 'categoria'
    if df_presupuesto.empty or "categoria" not in df_presupuesto.columns:
        st.warning("⚠️ No hay presupuesto cargado para este mes o falta la columna 'categoria'.")
        return

    # Proceder solo si todo está correcto
    df_comparativa = pd.merge(df_presupuesto, df_gastos_mes, on="categoria", how="outer").fillna(0)
    df_comparativa["diferencia"] = df_comparativa["importe"] - df_comparativa["real"]
    df_comparativa.rename(columns={"importe": "presupuesto"}, inplace=True)



    st.metric("💸 Gasto total del mes", f"{df_gastos_mes['real'].sum():,.2f} €")
    st.metric("📆 Presupuesto total del mes", f"{df_presupuesto['presupuesto'].sum():,.2f} €")
    st.metric("📉 Diferencia total", f"{df_comparativa['diferencia'].sum():,.2f} €")

    st.info("Comparativa por categoría del mes actual")
    st.dataframe(df_comparativa, use_container_width=True)
    st.bar_chart(df_comparativa.set_index("categoria")[["presupuesto", "real"]])

    st.markdown("### 📆 Evolución mensual de ingresos y gastos")

    df_mov_full = pd.DataFrame(supabase.table("movimientos").select("*").execute().data)
    df_mov_full["fecha"] = pd.to_datetime(df_mov_full["fecha"], errors="coerce")
    df_mov_full = df_mov_full[df_mov_full["fecha"].notnull()]
    df_mov_full["mes"] = df_mov_full["fecha"].dt.month
    df_mov_full["año"] = df_mov_full["fecha"].dt.year

    df_filtrado_año = df_mov_full[df_mov_full["año"] == año_actual]
    evolucion = df_filtrado_año.groupby(["mes", "tipo"])["importe"].sum().unstack(fill_value=0).reset_index()
    evolucion["mes_nombre"] = evolucion["mes"].apply(lambda x: meses[x - 1])
    evolucion = evolucion.sort_values("mes")
    st.line_chart(evolucion.set_index("mes_nombre")[["ingreso", "gasto"]])

    st.markdown("### 💰 Evolución del saldo acumulado")
    df_mov_valid = df_mov_full[df_mov_full["año"] == año_actual]
    df_mov_valid["mes"] = df_mov_valid["fecha"].dt.month
    ingresos = df_mov_valid[df_mov_valid["tipo"] == "ingreso"].groupby("mes")["importe"].sum()
    gastos = df_mov_valid[df_mov_valid["tipo"] == "gasto"].groupby("mes")["importe"].sum()
    saldo_mensual = ingresos.subtract(gastos, fill_value=0).reindex(range(1, 13), fill_value=0)
    saldo_acumulado = saldo_mensual.cumsum()
    saldo_acumulado.index = [meses[m - 1] for m in saldo_acumulado.index]
    st.line_chart(saldo_acumulado.rename("Saldo acumulado"))

    st.markdown("### 🏦 Saldos por cuenta")
    df_saldos_ini = obtener_saldos_iniciales()
    ingresos_cuenta = df_mov_valid[df_mov_valid["tipo"] == "ingreso"].groupby("cuenta")["importe"].sum()
    gastos_cuenta = df_mov_valid[df_mov_valid["tipo"] == "gasto"].groupby("cuenta")["importe"].sum()

    resumen_cuentas = pd.DataFrame({
        "Saldo inicial": df_saldos_ini.set_index("cuenta")["saldo"],
        "Ingresos": ingresos_cuenta,
        "Gastos": gastos_cuenta
    }).fillna(0)

    resumen_cuentas["Saldo final"] = resumen_cuentas["Saldo inicial"] + resumen_cuentas["Ingresos"] - resumen_cuentas["Gastos"]
    resumen_cuentas = resumen_cuentas[["Saldo inicial", "Ingresos", "Gastos", "Saldo final"]].sort_values("Saldo final", ascending=False)
    st.dataframe(resumen_cuentas.style.format("{:,.2f} €"), use_container_width=True)

    st.markdown("### 📈 Saldo acumulado mensual")
    evolucion["saldo_mes"] = evolucion["ingreso"] - evolucion["gasto"]
    evolucion["saldo_acumulado"] = evolucion["saldo_mes"].cumsum()
    st.line_chart(evolucion.set_index("mes_nombre")[["saldo_acumulado"]])
