
import pandas as pd

def combinar_movimientos(df_ingresos, df_gastos, df_transf):
    df_todos = pd.concat([df_ingresos, df_gastos, df_transf], ignore_index=True)
    df_todos["fecha"] = pd.to_datetime(df_todos["fecha"], errors="coerce")
    return df_todos
