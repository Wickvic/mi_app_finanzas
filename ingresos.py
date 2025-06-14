
from utils_tabla import editar_tabla_movimientos
import streamlit as st
from datetime import date
import pandas as pd
from app_utils import resumen_mensual

def mostrar_ingresos(df_ingresos, cuentas):
    lista_subcat = [
        "Nomina Sof:Nomina", "Nomina Vic:Nomina", "Vanguard:Empresa", "Inversiones:Empresa",
        "Venta de productos:Empresa", "Youtube:Empresa", "Digital:Empresa", "Afiliaciones:Empresa",
        "Donaciones:Regalos", "Devoluciones:Otros", "Otros:Otros"
    ]
    lista_cat = ["Nomina", "Empresa", "Regalos", "Otros"]

    hoy = date.today()
    df_mes = df_ingresos[pd.to_datetime(df_ingresos["fecha"]).dt.month == hoy.month]

    total = df_mes["importe"].sum()
    dias = df_mes["fecha"].nunique()
    diario = total / dias if dias else 0
    mayor = df_mes["importe"].max() if not df_mes.empty else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("💵 Total ingresos", f"{total:.2f} €")
    col2.metric("📅 Ingreso medio diario", f"{diario:.2f} €")
    col3.metric("💥 Mayor ingreso", f"{mayor:.2f} €")

    st.markdown("### 🚀 Consejo")
    if total > 5000:
        st.success("Gran mes de ingresos. ¿Has pensado en qué parte puedes invertir o ahorrar? 💡")
    elif total > 2000:
        st.info("Buen ritmo. Revisa qué ingresos puedes escalar o hacer recurrentes. 📈")
    else:
        st.warning("Tus ingresos son bajos este mes. ¿Puedes impulsar alguna fuente extra? 🔍")

    st.subheader("Registro de ingresos")
    total_ingresos, resumen_ingresos = resumen_mensual(df_ingresos, "ingreso")
    st.info(f"💰 Ingresos este mes: {total_ingresos:.2f}€")
    st.dataframe(resumen_ingresos, use_container_width=True)

    editar_tabla_movimientos(df_ingresos, "ingresos", lista_subcat, lista_cat, cuentas, key="edit_ingresos")
