
from utils_tabla import editar_tabla_movimientos
import streamlit as st
from datetime import date
import pandas as pd
from app_utils import resumen_mensual

def mostrar_gastos(df_gastos, cuentas):
    lista_subcat = [
        "Hipoteca:Casa", "Luz:Casa", "Agua:Casa", "Cesta:Casa", "Letra coche:Casa", "Internet y movil:Casa",
        "APP y subscripciones:Casa", "Impuestos:Casa", "Seguros medico:Casa", "Seguro coche:Casa",
        "Seguro casa:Casa", "Colegio:Casa", "Colegio: otros gastos:Casa", "Limpieza:Casa", "Deporte:Casa",
        "Medico:Salud", "Farmacia:Salud", "Cuidados:Salud", "Combustible:Transporte", "Aparcamiento:Transporte", "Otros transporte:Transporte",
        "Gastos laborales:Trabajo", "Colegio Medico:Trabajo", "Seguro responsabilidad civil:Trabajo", "Sindicato:Trabajo",
        "Empresa:Trabajo", "Formaciones:Trabajo", "Moda:Adquisiciones", "Hogar:Adquisiciones", "Libros:Adquisiciones",
        "Restauración:Ocio", "Viajes:Ocio", "Eventos:Ocio", "Otros:Otros", "Contabilidad:Contabilidad"
    ]
    lista_cat = ["Casa", "Salud", "Transporte", "Trabajo", "Adquisiciones", "Ocio", "Otros", "Contabilidad"]

    hoy = date.today()
    df_gastos_mes = df_gastos[pd.to_datetime(df_gastos["fecha"]).dt.month == hoy.month]

    importe_total_mes = df_gastos_mes["importe"].sum()
    dias_con_gasto = df_gastos_mes["fecha"].nunique()
    gasto_diario_medio = importe_total_mes / dias_con_gasto if dias_con_gasto else 0
    mayor_gasto = df_gastos_mes["importe"].max() if not df_gastos_mes.empty else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Gasto total", f"{importe_total_mes:.2f} €")
    col2.metric("📅 Gasto medio diario", f"{gasto_diario_medio:.2f} €")
    col3.metric("🔥 Mayor gasto", f"{mayor_gasto:.2f} €")

    st.markdown("### 🧠 Consejo del mes")
    if gasto_diario_medio <= 30:
        st.success("¡Muy bien! Estás manteniendo tus gastos bajo control este mes. 💪")
    elif gasto_diario_medio <= 50:
        st.info("Buen ritmo, pero revisa tus gastos en ocio o caprichos para optimizar. 🧐")
    else:
        st.warning("Este mes estás gastando más de lo habitual. ¿Podrías ajustar alguna categoría? 🔍")

    st.subheader("Registro de gastos")
    total_gastos, resumen_gastos = resumen_mensual(df_gastos, "gasto")
    st.warning(f"💸 Gastos este mes: {total_gastos:.2f}€")
    st.dataframe(resumen_gastos, use_container_width=True)

    editar_tabla_movimientos(df_gastos, "gastos", lista_subcat, lista_cat, cuentas, key="edit_gastos")
