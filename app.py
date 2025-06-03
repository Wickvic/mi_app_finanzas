
import streamlit as st
import pandas as pd
from datetime import date
from supabase_client import insertar_movimiento, obtener_saldos_iniciales, supabase

st.set_page_config(page_title="Finanzas Familiares", layout="wide")
st.title("📊 Finanzas Familiares")

def cargar_datos(tipo):
    from supabase_client import supabase
    resp = supabase.table("movimientos").select("*").eq("tipo", tipo).execute()
    if resp.data:
        return pd.DataFrame(resp.data)
    return pd.DataFrame(columns=["fecha", "cuenta", "categoria", "subcategoria", "importe", "comentario", "tipo", "desde", "hacia"])

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

    from datetime import datetime
    import numpy as np

    st.markdown("### 📊 Resumen de gastos del mes")

    # Filtrar gastos del mes actual
    hoy = date.today()
    df_gastos_mes = df_gastos[
        pd.to_datetime(df_gastos["fecha"]).dt.month == hoy.month
    ]

    # Calcular métricas
    importe_total_mes = df_gastos_mes["importe"].sum()
    dias_con_gasto = df_gastos_mes["fecha"].nunique()
    gasto_diario_medio = importe_total_mes / dias_con_gasto if dias_con_gasto else 0
    mayor_gasto = df_gastos_mes["importe"].max() if not df_gastos_mes.empty else 0

    # Mostrar widgets
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Gasto total", f"{importe_total_mes:.2f} €")
    col2.metric("📅 Gasto medio diario", f"{gasto_diario_medio:.2f} €")
    col3.metric("🔥 Mayor gasto", f"{mayor_gasto:.2f} €")

    # Frase motivadora
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

    modo_gasto = st.radio("¿Cómo quieres introducir los gastos?", ["Formulario", "Tabla editable"])

    if modo_gasto == "Formulario":
        with st.form("nuevo_gasto"):
            fecha = st.date_input("Fecha", date.today(), key="fecha_gasto")
            cuenta = st.selectbox("Cuenta", cuentas, key="cuenta_gasto")
            subcat = st.selectbox("Subcategoría", [
                "Hipoteca", "Luz", "Agua", "Cesta", "Letra coche", "Internet y movil",
                "APP y subscripciones", "Impuestos", "Seguros medico", "Seguro coche",
                "Seguro casa", "Colegio: mensualidad", "Colegio: otros gastos", "Limpieza", "Deporte",
                "Medico", "Farmacia", "Cuidados", "Combustible", "Aparcamiento", "Otros transporte",
                "Gastos laborales", "Colegio Medico", "Seguro responsabilidad civil", "Sindicato",
                "Empresa", "Formaciones", "Moda", "Hogar", "Libros", "Restauración", "Viajes",
                "Eventos", "Otros", "Contabilidad"], key="subcat_gasto")
            cat_map = {
                "Hipoteca": "Casa", "Luz": "Casa", "Agua": "Casa", "Cesta": "Casa", "Letra coche": "Casa",
                "Internet y movil": "Casa", "APP y subscripciones": "Casa", "Impuestos": "Casa", "Seguros medico": "Casa",
                "Seguro coche": "Casa", "Seguro casa": "Casa", "Colegio: mensualidad": "Casa",
                "Colegio: otros gastos": "Casa", "Limpieza": "Casa", "Deporte": "Casa",
                "Medico": "Salud", "Farmacia": "Salud", "Cuidados": "Salud",
                "Combustible": "Transporte", "Aparcamiento": "Transporte", "Otros transporte": "Transporte",
                "Gastos laborales": "Trabajo", "Colegio Medico": "Trabajo", "Seguro responsabilidad civil": "Trabajo",
                "Sindicato": "Trabajo", "Empresa": "Trabajo", "Formaciones": "Trabajo",
                "Moda": "Adquisiciones", "Hogar": "Adquisiciones", "Libros": "Adquisiciones",
                "Restauración": "Ocio", "Viajes": "Ocio", "Eventos": "Ocio", "Otros": "Otros",
                "Contabilidad": "Contabilidad"
            }
            categoria = cat_map[subcat]
            importe = st.number_input("Importe", min_value=0.0, format="%.2f", key="importe_gasto")
            comentario = st.text_input("Comentario (opcional)", key="comentario_gasto")
            if st.form_submit_button("Añadir gasto"):
                insertar_movimiento([{
                    "fecha": fecha.isoformat(), "cuenta": cuenta,
                    "categoria": categoria, "subcategoria": subcat,
                    "importe": importe, "comentario": comentario,
                    "tipo": "gasto"
                }])
                st.success("Gasto añadido")

    elif modo_gasto == "Tabla editable":
        st.write("Edita directamente los gastos:")
        edited_gastos = st.data_editor(df_gastos, use_container_width=True, num_rows="dynamic", key="edit_gastos")

    st.markdown("### 📥 Importar gastos desde archivo Excel BBVA")
    archivo_excel = st.file_uploader("Sube el archivo Excel con los movimientos", type=["xlsx"], key="excel_bbva")

    if archivo_excel:
        try:
            import pandas as pd
            from io import BytesIO

            xls = pd.ExcelFile(archivo_excel)
            df = xls.parse('Informe BBVA', skiprows=4)
            df.columns = [
                'Index', 'F_Valor', 'Fecha', 'Concepto', 'Movimiento', 'Importe',
                'Divisa1', 'Disponible', 'Divisa2', 'Observaciones'
            ]

            df = df[df['Fecha'].notna() & df['Importe'].notna()]
            df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce')
            df['Importe'] = pd.to_numeric(df['Importe'], errors='coerce')

            # Filtrar solo gastos reales
            df_gastos_excel = df[
                (df['Importe'] < 0) &
                (~df['Movimiento'].str.lower().str.contains("traspaso|transferencia", na=False))
            ].copy()

            df_gastos_excel['Importe_abs'] = df_gastos_excel['Importe'].abs()
            df_gastos_excel["cuenta"] = "Vivir"
            df_gastos_excel["categoria"] = "Otros"
            df_gastos_excel["subcategoria"] = df_gastos_excel["Concepto"].str.slice(0, 30)
            df_gastos_excel["comentario"] = df_gastos_excel["Observaciones"]
            df_gastos_excel["tipo"] = "gasto"
            df_gastos_excel = df_gastos_excel.rename(columns={"Fecha": "fecha", "Importe_abs": "importe"})

            columnas_app = ["fecha", "cuenta", "categoria", "subcategoria", "importe", "comentario", "tipo"]
            df_gastos_excel = df_gastos_excel[columnas_app]

            st.success(f"✅ Se han detectado {len(df_gastos_excel)} gastos válidos.")
            st.data_editor(df_gastos_excel, use_container_width=True, num_rows="dynamic", key="vista_gastos_excel")

            if st.button("📤 Importar estos gastos"):
                for _, fila in df_gastos_excel.iterrows():
                    insertar_movimiento(fila.to_dict())
                st.success("Movimientos importados correctamente.")

        except Exception as e:
            st.error(f"❌ Error al procesar el archivo: {e}")

    st.markdown("### 🏆 Ranking de categorías de gasto del mes")

    df_gastos_mes = df_gastos[
        pd.to_datetime(df_gastos["fecha"]).dt.month == date.today().month
    ]

    ranking = df_gastos_mes.groupby("subcategoria")["importe"].sum().sort_values(ascending=False)
    for i, (cat, total) in enumerate(ranking.items(), start=1):
        st.write(f"{i}. **{cat}** → {total:.2f} €")

# ---------- INGRESOS ----------
df_ingresos = cargar_datos("ingreso")
with tabs[2]:

    st.markdown("### 📈 Resumen de ingresos del mes")

    # Filtrar ingresos del mes actual
    hoy = date.today()
    df_ingresos_mes = df_ingresos[
        pd.to_datetime(df_ingresos["fecha"]).dt.month == hoy.month
    ]

    # KPIs
    total_ingresos = df_ingresos_mes["importe"].sum()
    dias_con_ingresos = df_ingresos_mes["fecha"].nunique()
    ingreso_diario_medio = total_ingresos / dias_con_ingresos if dias_con_ingresos else 0
    mayor_ingreso = df_ingresos_mes["importe"].max() if not df_ingresos_mes.empty else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("💵 Total ingresos", f"{total_ingresos:.2f} €")
    col2.metric("📅 Ingreso medio diario", f"{ingreso_diario_medio:.2f} €")
    col3.metric("💥 Mayor ingreso", f"{mayor_ingreso:.2f} €")

    # Consejo motivador
    st.markdown("### 🚀 Consejo")
    if total_ingresos > 5000:
        st.success("Gran mes de ingresos. ¿Has pensado en qué parte puedes invertir o ahorrar? 💡")
    elif total_ingresos > 2000:
        st.info("Buen ritmo. Revisa qué ingresos puedes escalar o hacer recurrentes. 📈")
    else:
        st.warning("Tus ingresos son bajos este mes. ¿Puedes impulsar alguna fuente extra? 🔍")


    st.subheader("Registro de ingresos")
    total_ingresos, resumen_ingresos = resumen_mensual(df_ingresos, "ingreso")
    st.info(f"💰 Ingresos este mes: {total_ingresos:.2f}€")
    st.dataframe(resumen_ingresos, use_container_width=True)

    modo_ingreso = st.radio("¿Cómo quieres introducir los ingresos?", ["Formulario", "Tabla editable"])

    if modo_ingreso == "Formulario":
        with st.form("nuevo_ingreso"):
            fecha = st.date_input("Fecha", date.today())
            cuenta = st.selectbox("Cuenta", cuentas)
            subcat = st.selectbox("Subcategoría", [
                "Nomina Sof", "Nomina Vic", "Vanguard", "Inversiones", "Venta de productos",
                "Youtube", "Digital", "Afiliaciones", "Donaciones", "Devoluciones", "Otros"])
            categoria = {
                "Nomina Sof": "Nomina", "Nomina Vic": "Nomina",
                "Vanguard": "Empresa", "Inversiones": "Empresa", "Venta de productos": "Empresa",
                "Youtube": "Empresa", "Digital": "Empresa", "Afiliaciones": "Empresa",
                "Donaciones": "Regalos", "Devoluciones": "Otros", "Otros": "Otros"
            }[subcat]
            importe = st.number_input("Importe", min_value=0.0, format="%.2f")
            comentario = st.text_input("Comentario (opcional)")
            if st.form_submit_button("Añadir ingreso"):
                insertar_movimiento([{
                    "fecha": fecha.isoformat(), "cuenta": cuenta,
                    "categoria": categoria, "subcategoria": subcat,
                    "importe": importe, "comentario": comentario,
                    "tipo": "ingreso"
                }])
                st.success("Ingreso añadido")
    else:
        st.write("Edita directamente los ingresos:")
        edited_ingresos = st.data_editor(df_ingresos, use_container_width=True, num_rows="dynamic", key="edit_ingresos")




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
with tabs[4]:
    st.subheader("Histórico de movimientos")
    df_todos = pd.concat([df_ingresos, df_gastos, df_transf], ignore_index=True)
    df_todos["fecha"] = pd.to_datetime(df_todos["fecha"])
    tipo = st.selectbox("Tipo", ["Todos", "ingreso", "gasto", "transferencia"])
    año = st.selectbox("Año", sorted(df_todos["fecha"].dt.year.unique(), reverse=True))
    mes = st.selectbox("Mes", list(range(1, 13)))

    df_filtrado = df_todos[df_todos["fecha"].dt.year == año]
    df_filtrado = df_filtrado[df_filtrado["fecha"].dt.month == mes]
    if tipo != "Todos":
        df_filtrado = df_filtrado[df_filtrado["tipo"] == tipo]

    texto = st.text_input("Buscar texto")
    if texto:
        df_filtrado = df_filtrado[df_filtrado.apply(lambda row: texto.lower() in str(row).lower(), axis=1)]

    st.dataframe(df_filtrado.sort_values("fecha", ascending=False), use_container_width=True)

# ---------- DASHBOARD ---------- 
from dashboard_section import mostrar_dashboard

with tabs[5]:
    from datetime import date
    import numpy as np

    st.markdown("### 📊 Visión general del mes")

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
    

