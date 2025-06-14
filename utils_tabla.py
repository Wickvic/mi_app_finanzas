import streamlit as st
import pandas as pd

def mapear_categoria(df, opciones_subcat):
    subcat_to_cat = {}
    for s in opciones_subcat:
        if ":" in s:
            sub, cat = s.split(":", 1)
            subcat_to_cat[sub.strip()] = cat.strip()

    if "subcategoria" in df.columns and "categoria" in df.columns:
        df["categoria"] = df["subcategoria"].map(subcat_to_cat).fillna(df["categoria"])

    return df

def editar_tabla_movimientos(df_original, tipo, opciones_subcat=None, opciones_cat=None, cuentas=None, key=None):
    df = df_original.copy()
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")

    if opciones_subcat:
        df = mapear_categoria(df, opciones_subcat)

    columnas_deseadas = ["comentario", "subcategoria", "categoria", "cuenta", "importe", "fecha"]
    columnas_deseadas = [col for col in columnas_deseadas if col in df.columns]
    df = df[columnas_deseadas]

    df = df.rename(columns={
        "comentario": "Concepto",
        "subcategoria": "Subcategoría",
        "categoria": "Categoría",
        "cuenta": "Cuenta",
        "importe": "Importe",
        "fecha": "Fecha"
    })

    column_config = {
        "Cuenta": st.column_config.SelectboxColumn("Cuenta", options=cuentas) if cuentas else None,
        "Importe": st.column_config.NumberColumn("Importe", format="%.2f €"),
        "Fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY")
    }

    if opciones_subcat:
        sub_opciones = [s.split(":")[0].strip() for s in opciones_subcat]
        column_config["Subcategoría"] = st.column_config.SelectboxColumn("Subcategoría", options=sub_opciones)
    if opciones_cat:
        column_config["Categoría"] = st.column_config.SelectboxColumn("Categoría", options=opciones_cat)

    st.markdown(f"### ✏️ Editar {tipo}")
    edited = st.data_editor(
        df,
        column_config=column_config,
        use_container_width=True,
        num_rows="dynamic",
        key=key
    )

    if st.button(f"💾 Guardar cambios en {tipo}"):
        for _, row in edited.iterrows():
            movimiento_id = row.get("movimiento_id")
            if movimiento_id:
                supabase.table("movimientos").update({
                    "comentario": row["Concepto"],
                    "subcategoria": row["Subcategoría"],
                    "categoria": row["Categoría"],
                    "cuenta": row["Cuenta"],
                    "importe": row["Importe"],
                    "fecha": str(row["Fecha"])
                }).eq("movimiento_id", movimiento_id).execute()
        st.success(f"Cambios guardados en {tipo}")
