
import streamlit as st
import pandas as pd
from datetime import date
from supabase_client import insertar_movimiento, obtener_saldos_iniciales, supabase
from gastos import mostrar_gastos
from ingresos import mostrar_ingresos
from utils_movimientos import combinar_movimientos
from historico import mostrar_historico
from movimientos import cargar_datos



st.set_page_config(page_title="Finanzas Familiares", layout="wide")
st.title("📊 Finanzas Familiares")

def resumen_mensual(df, tipo):
    hoy = date.today()
    df["fecha"] = pd.to_datetime(df["fecha"])
    df_mes = df[(df["fecha"].dt.year == hoy.year) & (df["fecha"].dt.month == hoy.month)]
    total = df_mes["importe"].sum()
    resumen = df_mes.groupby("categoria")["importe"].sum().reset_index()
    resumen = resumen[resumen["importe"] > 0].sort_values("importe", ascending=False)
    return total, resumen

tabs = st.tabs(["📆 Presupuesto", "🔴 Gastos", "🟢 Ingresos", "🔁 Transferencias", "📚 Histórico", "📊 Dashboard", "🍀 Vision Financiera",  "🧠 Inteligencia Financiera"])

cuentas = ["Vivir", "Lujo", "Remunerada", "Inversiones", "Efectivo"]

# ---------- PRESUPUESTO ----------
with tabs[0]:

    from supabase_client import supabase  # ⬅️ asegúrate de que esto esté presente

    def cargar_presupuesto():
        resp = supabase.table("presupuestos").select("*").execute()
        if resp.data:
            df = pd.DataFrame(resp.data)
            df["mes"] = df["mes"].astype(int)
            return df
        else:
            return pd.DataFrame(columns=["categoria", "mes", "importe"])

    def guardar_presupuesto(df):
        supabase.table("presupuestos").delete().neq("categoria", "").execute()
        data = df.to_dict(orient="records")
        supabase.table("presupuestos").insert(data).execute()

    meses = [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ]
    categorias = [
        "Casa", "Salud", "Transporte", "Trabajo", "Adquisiciones", "Ocio", "Otros", "Contabilidad"
    ]

    df_presupuesto = cargar_presupuesto()

    # ---------- Tabla Anual ----------
    st.markdown("### 🗓️ Presupuesto Anual")
    df_pivot = df_presupuesto.pivot(index="categoria", columns="mes", values="importe").reindex(categorias).fillna(0)
    df_pivot.columns = [meses[m - 1] for m in df_pivot.columns]
    df_pivot["Total Anual"] = df_pivot.sum(axis=1)
    df_pivot = df_pivot.reset_index()

    df_editado_anual = st.data_editor(df_pivot, use_container_width=True, num_rows="fixed", key="editor_anual")

    if st.button("💾 Guardar presupuesto anual"):
        df_guardar = df_editado_anual.drop(columns=["Total Anual"]).melt(id_vars="categoria", var_name="mes", value_name="importe")
        df_guardar["mes"] = df_guardar["mes"].apply(lambda x: meses.index(x) + 1)
        guardar_presupuesto(df_guardar)
        st.success("✅ Presupuesto anual guardado correctamente")

    # ---------- Tabla Mensual ----------
    st.markdown("### 🔍 Editar un mes específico")
    mes_seleccionado = st.selectbox("Selecciona un mes para editar:", meses)
    mes_idx = meses.index(mes_seleccionado) + 1

    df_mes = df_presupuesto[df_presupuesto["mes"] == mes_idx].set_index("categoria").reindex(categorias).fillna(0).reset_index()
    df_mes = df_mes[["categoria", "importe"]]
    df_mes_editado = st.data_editor(df_mes, use_container_width=True, num_rows="fixed", key="editor_mensual")

    if st.button(f"💾 Guardar presupuesto de {mes_seleccionado}"):
        df_mes_editado["mes"] = mes_idx
        guardar_presupuesto(df_presupuesto[df_presupuesto["mes"] != mes_idx].append(df_mes_editado))
        st.success(f"✅ Presupuesto de {mes_seleccionado} guardado correctamente")

# ---------- GASTOS ----------
df_gastos = cargar_datos("gasto")
with tabs[1]:
    mostrar_gastos(df_gastos, cuentas)


# ---------- INGRESOS ----------
df_ingresos = cargar_datos("ingreso")
with tabs[2]:
    mostrar_ingresos(df_ingresos, cuentas)

# ---------- TRANSFERENCIAS ----------
df_transf = cargar_datos("transferencia")
with tabs[3]:
    st.subheader("Registro de transferencias")

    modo_transf = st.radio("¿Cómo quieres introducir las transferencias?", ["Formulario", "Tabla editable"])

    if modo_transf == "Formulario":
        with st.form("nueva_transf"):
            fecha = st.date_input("Fecha", date.today(), key="fecha_transf")
            desde = st.selectbox("Desde", cuentas, key="desde_transf")
            hacia = st.selectbox("Hacia", [x for x in cuentas if x != desde], key="hacia_transf")
            importe = st.number_input("Importe", min_value=0.0, format="%.2f", key="importe_transf")
            comentario = st.text_input("Comentario (opcional)", key="comentario_transf")
            if st.form_submit_button("Añadir transferencia"):
                insertar_movimiento([{
                    "fecha": fecha.isoformat(),
                    "desde": desde, "hacia": hacia,
                    "importe": importe, "comentario": comentario,
                    "tipo": "transferencia"
                }])
                st.success("Transferencia registrada")
    else:
        st.write("Edita directamente las transferencias:")
        edited_transf = st.data_editor(df_transf, use_container_width=True, num_rows="dynamic", key="edit_transf")

# ---------- HISTÓRICO ---------- 
# Combinar los tres tipos de movimientos
df_todos = combinar_movimientos(df_ingresos, df_gastos, df_transf)

# Mostrar histórico en la pestaña correspondiente
with tabs[4]:
    mostrar_historico(df_todos, cuentas)

# ---------- DASHBOARD ---------- 
from dashboard_section import mostrar_dashboard

with tabs[5]:
    from datetime import date
    import numpy as np

    st.markdown("### 📊 Dashboard")

    # Filtrar datos del mes actual
    hoy = date.today()
    df_ingresos_mes = df_ingresos[
        pd.to_datetime(df_ingresos["fecha"]).dt.month == hoy.month
    ]
    df_gastos_mes = df_gastos[
        pd.to_datetime(df_gastos["fecha"]).dt.month == hoy.month
    ]

    total_ingresos = df_ingresos_mes["importe"].sum()
    total_gastos = df_gastos_mes["importe"].sum()
    ahorro = total_ingresos - total_gastos
    porcentaje_ahorro = (ahorro / total_ingresos * 100) if total_ingresos > 0 else 0

    # KPIs
    col1, col2, col3 = st.columns(3)
    col1.metric("💵 Ingresos", f"{total_ingresos:.2f} €")
    col2.metric("💸 Gastos", f"{total_gastos:.2f} €")
    col3.metric("📊 Ahorro neto", f"{ahorro:.2f} €", f"{porcentaje_ahorro:.1f}%")

    # Consejo motivador
    st.markdown("### 💬 Balance y consejo")
    if porcentaje_ahorro >= 20:
        st.success("¡Excelente! Estás ahorrando más del 20% de tus ingresos. 🌱 Invierte en tu futuro.")
    elif porcentaje_ahorro > 0:
        st.info("Buen trabajo, estás en positivo. Puedes buscar margen para ahorrar aún más. 🚀")
    else:
        st.warning("Has gastado más de lo que ingresaste este mes. Revisa tus hábitos o gastos fijos. 🧾")

    mostrar_dashboard(
        df_ingresos=df_ingresos,
        df_gastos=df_gastos,
        df_transf=df_transf,
        cuentas=cuentas,
        meses=meses,
        obtener_saldos_iniciales=obtener_saldos_iniciales
    )


# ---------- VISION FINANCIERA ---------- 
from vision_financiera import mostrar_vision_financiera
from supabase_client import supabase

with tabs[6]:
    mostrar_vision_financiera(
    df_mov=df_todos,
    df_presupuesto=df_presupuesto,
    obtener_saldos_iniciales=obtener_saldos_iniciales,
    cuentas=cuentas,
    meses=meses,
    supabase=supabase
)

# ---------- INTELIGENCIA FINANCIERA ---------- 
from inteligencia_financiera import mostrar_inteligencia_financiera
with tabs[7]:
    mostrar_inteligencia_financiera(
    df_mov=df_todos,
    df_presupuesto=df_presupuesto,
    df_ingresos=df_ingresos,
    df_gastos=df_gastos,
    df_transf=df_transf,
    cuentas=cuentas,
    obtener_saldos_iniciales=obtener_saldos_iniciales  # ✅ Nombre correcto del parámetro
)
    

