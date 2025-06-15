
def resumen_mensual(df, tipo):
    import pandas as pd

    df = df.copy()
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    mes_actual = pd.Timestamp.now().month
    df_mes = df[df["fecha"].dt.month == mes_actual]

    resumen = df_mes.groupby("subcategoria")["importe"].sum().reset_index()
    resumen.columns = ["Subcategoría", "Total"]
    resumen = resumen.sort_values("Total", ascending=False)

    total = df_mes["importe"].sum()
    return total, resumen
