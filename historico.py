
from utils_tabla import editar_tabla_movimientos
import streamlit as st
import pandas as pd

def mostrar_historico(df_todos, cuentas):
    st.subheader("Histórico de movimientos")

    tipo = st.selectbox("Tipo", ["Todos", "ingreso", "gasto", "transferencia"])

    años_disponibles = sorted(df_todos["fecha"].dt.year.dropna().unique(), reverse=True)
    año = st.selectbox("Año", años_disponibles)

    opcion_filtro = st.radio("¿Cómo quieres filtrar?", ["Todo el año", "Trimestre", "Mes"])
    df_filtrado = df_todos[df_todos["fecha"].dt.year == año]

    if opcion_filtro == "Trimestre":
        trimestre = st.selectbox("Trimestre", [1, 2, 3, 4])
        meses_trimestre = {1: [1,2,3], 2: [4,5,6], 3: [7,8,9], 4: [10,11,12]}
        df_filtrado = df_filtrado[df_filtrado["fecha"].dt.month.isin(meses_trimestre[trimestre])]
    elif opcion_filtro == "Mes":
        mes = st.selectbox("Mes", list(range(1,13)))
        df_filtrado = df_filtrado[df_filtrado["fecha"].dt.month == mes]

    if tipo != "Todos":
        df_filtrado = df_filtrado[df_filtrado["tipo"] == tipo]

    texto = st.text_input("Buscar texto")
    if texto:
        df_filtrado = df_filtrado[df_filtrado.apply(lambda row: texto.lower() in str(row).lower(), axis=1)]

    editar_tabla_movimientos(df_filtrado, "histórico", cuentas=cuentas, key="edit_historico")
