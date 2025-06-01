
from supabase import create_client, Client
import os

# Sustituye estos valores con los tuyos de Supabase
SUPABASE_URL = "https://nfjevxpqpkaqqqnhdfuf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5mamV2eHBxcGthcXFxbmhkZnVmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDg3NzI3MjMsImV4cCI6MjA2NDM0ODcyM30.4RQhTyCCk37TAGZvYIr6L6bx-xpoGF95Q7DlViQhGFM"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def insertar_movimiento(data):
    response = supabase.table("movimientos").insert(data).execute()
    return response
