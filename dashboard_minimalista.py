
import streamlit as st
import pandas as pd
from datetime import date
from supabase_client import supabase
import io
from xhtml2pdf import pisa

def mostrar_dashboard(df_ingresos, df_gastos, df_transf, cuentas, meses, obtener_saldos_iniciales):

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

    # Aquí seguiría el resto del dashboard (gráficos, métricas, etc.)
