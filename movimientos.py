from supabase_client import supabase
import pandas as pd

def cargar_datos(tipo):
    response = supabase.table("movimientos").select("*").eq("tipo", tipo).execute()
    columnas_base = [
        "fecha", "cuenta", "categoria", "subcategoria",
        "importe", "comentario", "tipo", "movimiento_id"
    ]
    if tipo == "transferencia":
        columnas_base += ["desde", "hacia"]

    if response.data:
        df = pd.DataFrame(response.data)
        if "fecha" in df.columns:
            df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")

        for col in columnas_base:
            if col not in df.columns:
                df[col] = None

        return df[columnas_base if tipo != "transferencia" else columnas_base]
    else:
        return pd.DataFrame(columns=columnas_base)
