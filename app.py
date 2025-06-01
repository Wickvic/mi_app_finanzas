
import streamlit as st
import pandas as pd
from datetime import date
from supabase_client import insertar_movimiento

st.set_page_config(page_title="Finanzas Familiares", layout="centered")
st.title("📊 Finanzas Familiares")

modo = st.radio("Modo de registro:", ["Formulario", "Tabla editable"], horizontal=True)

cuentas = ["Vivir", "Lujo", "Remunerada", "Inversiones", "Efectivo"]
tipos = ["Gasto", "Ingreso", "Transferencia"]
subcategorias = [
    "Cesta", "Luz", "Agua", "Letra coche", "Internet y movil",
    "Restauración", "Viajes", "Eventos",
    "Combustible", "Aparcamiento", "Otros transporte",
    "Farmacia", "Médico", "Cuidados",
    "Moda", "Hogar", "Libros",
    "Nómina Sof", "Nómina Vic",
    "Vanguard", "Inversiones", "Venta de productos", "YouTube", "Digital", "Afiliaciones",
    "Donaciones", "Devoluciones", "Otros", "Contabilidad"
]

mapa_subcat = {
    "Cesta": "Casa", "Luz": "Casa", "Agua": "Casa", "Letra coche": "Casa", "Internet y movil": "Casa",
    "Restauración": "Ocio", "Viajes": "Ocio", "Eventos": "Ocio",
    "Combustible": "Transporte", "Aparcamiento": "Transporte", "Otros transporte": "Transporte",
    "Farmacia": "Salud", "Médico": "Salud", "Cuidados": "Salud",
    "Moda": "Adquisiciones", "Hogar": "Adquisiciones", "Libros": "Adquisiciones",
    "Nómina Sof": "Nómina", "Nómina Vic": "Nómina",
    "Vanguard": "Empresa", "Inversiones": "Empresa", "Venta de productos": "Empresa",
    "YouTube": "Empresa", "Digital": "Empresa", "Afiliaciones": "Empresa",
    "Donaciones": "Regalos", "Devoluciones": "Otros", "Otros": "Otros",
    "Contabilidad": "Contabilidad"
}

if modo == "Formulario":
    tipo = st.selectbox("Tipo de movimiento", tipos)
    fecha = st.date_input("Fecha", value=date.today())
    cuenta = st.selectbox("Cuenta", cuentas)
    importe = st.number_input("Importe (€)", min_value=0.0, step=0.01)
    subcat = st.selectbox("Subcategoría", subcategorias)
    concepto = st.text_input("Concepto")
    categoria = mapa_subcat.get(subcat, "")

    if tipo == "Transferencia":
        cuenta_destino = st.selectbox("Cuenta destino", [c for c in cuentas if c != cuenta])
    else:
        cuenta_destino = None

    if st.button("💾 Guardar movimiento"):
        datos = {
            "fecha": fecha.isoformat(),
            "cuenta": cuenta,
            "tipo": tipo,
            "importe": importe,
            "subcategoria": subcat,
            "categoria": categoria,
            "concepto": concepto
        }
        respuesta = insertar_movimiento(datos)
        if respuesta.status_code == 201:
            st.success(f"Movimiento registrado correctamente.")
        else:
            st.error(f"Error al guardar: {respuesta.data}")

else:
    hoy = pd.to_datetime("2025-06-01")
    df_template = pd.DataFrame([{"Fecha": hoy, "Cuenta": cuentas[0], "Tipo": tipos[0], "Importe": 0.0, "Subcategoría": subcategorias[0], "Concepto": ""}])
    df_edit = st.data_editor(
        df_template,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Cuenta": st.column_config.SelectboxColumn("Cuenta", options=cuentas),
            "Tipo": st.column_config.SelectboxColumn("Tipo", options=tipos),
            "Subcategoría": st.column_config.SelectboxColumn("Subcategoría", options=subcategorias),
            "Fecha": st.column_config.DateColumn("Fecha"),
            "Importe": st.column_config.NumberColumn("Importe (€)", step=0.01),
            "Concepto": st.column_config.TextColumn("Concepto")
        }
    )

    if st.button("💾 Guardar registros de la tabla"):
        errores = 0
        for _, row in df_edit.iterrows():
            categoria = mapa_subcat.get(row["Subcategoría"], "")
            datos = {
                "fecha": row["Fecha"].date().isoformat(),
                "cuenta": row["Cuenta"],
                "tipo": row["Tipo"],
                "importe": row["Importe"],
                "subcategoria": row["Subcategoría"],
                "categoria": categoria,
                "concepto": row["Concepto"]
            }
            respuesta = insertar_movimiento(datos)
            if respuesta.status_code != 201:
                errores += 1
        if errores == 0:
            st.success("Todos los registros se guardaron correctamente.")
        else:
            st.warning(f"Se guardaron con {errores} errores.")
