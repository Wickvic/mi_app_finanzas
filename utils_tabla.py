import uuid
from supabase_client import supabase

# 👇 Mapeo de tipo a texto para mostrar en la cabecera
tipo_texto = {
    "gastos": "gastos",
    "ingresos": "ingresos",
    "transferencias": "transferencias",
    "histórico": "histórico"
}

def editar_tabla_movimientos(df, tipo, lista_subcat=None, lista_cat=None, cuentas=None, key=None):
    st.markdown(f"### ✏️ Editar {tipo_texto.get(tipo, tipo)}")

    editable_cols = []
    if tipo != "transferencias":
        editable_cols = ["subcategoria", "categoria", "cuenta", "importe", "fecha", "comentario"]
    else:
        editable_cols = ["desde", "hacia", "importe", "fecha", "comentario"]

    if tipo != "transferencias":
        df = df[["subcategoria", "categoria", "cuenta", "importe", "fecha", "comentario"]]
    else:
        df = df[["desde", "hacia", "importe", "fecha", "comentario"]]

    edited_df = st.data_editor(
        df,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "subcategoria": st.column_config.SelectboxColumn("Subcategoría", options=[s.split(":")[0] for s in lista_subcat] if lista_subcat else []),
            "categoria": st.column_config.SelectboxColumn("Categoría", options=lista_cat if lista_cat else []),
            "cuenta": st.column_config.SelectboxColumn("Cuenta", options=cuentas if cuentas else []),
            "desde": st.column_config.SelectboxColumn("Desde", options=cuentas if cuentas else []),
            "hacia": st.column_config.SelectboxColumn("Hacia", options=cuentas if cuentas else []),
            "importe": st.column_config.NumberColumn("Importe", min_value=0, format="%.2f"),
            "comentario": st.column_config.TextColumn("Concepto"),
            "fecha": st.column_config.DateColumn("Fecha")
        },
        key=key,
        on_change=st.experimental_rerun
    )

    if st.button("💾 Guardar cambios", key=f"guardar_{tipo}"):
        movimientos = []
        for _, row in edited_df.iterrows():
            base = {
                "fecha": str(row["fecha"]),
                "importe": float(row["importe"]),
                "comentario": row.get("comentario", ""),
                "id": str(uuid.uuid4()),
                "created_at": pd.Timestamp.now().isoformat()
            }
            if tipo == "gastos":
                base.update({
                    "tipo": "gasto",
                    "subcategoria": row["subcategoria"],
                    "categoria": row["categoria"],
                    "cuenta": row["cuenta"]
                })
            elif tipo == "ingresos":
                base.update({
                    "tipo": "ingreso",
                    "subcategoria": row["subcategoria"],
                    "categoria": row["categoria"],
                    "cuenta": row["cuenta"]
                })
            elif tipo == "transferencias":
                base.update({
                    "tipo": "transferencia",
                    "desde": row["desde"],
                    "hacia": row["hacia"]
                })
            else:
                continue

            movimientos.append(base)

        supabase.table("movimientos").delete().eq("tipo", base["tipo"]).execute()
        if movimientos:
            supabase.table("movimientos").insert(movimientos).execute()
        st.success("✅ Cambios guardados correctamente")
        st.experimental_rerun()
