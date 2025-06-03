from supabase import create_client, Client
from dotenv import load_dotenv
import os

from dotenv import load_dotenv
import os

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("❌ Variables de entorno no cargadas correctamente")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def insertar_movimiento(data):
    return supabase.table("movimientos").insert(data).execute()

def obtener_saldos_iniciales():
    return supabase.table("saldos_iniciales").select("*").execute().data
