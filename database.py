from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv

load_dotenv()

# Configuración de MongoDB
MONGODB_URL = os.getenv("MONGODB_URL", "")
DATABASE_NAME = os.getenv("DATABASE_NAME", "impostor_game")

# Cliente de MongoDB
client = None
database = None


async def connect_to_mongo():
    """Conectar a MongoDB"""
    global client, database
    
    # Si no hay URL configurada, usar modo sin base de datos
    if not MONGODB_URL or MONGODB_URL == "mongodb://localhost:27017" or "<db_username>" in MONGODB_URL:
        print("⚠️ MongoDB no configurado. La app funcionará en modo local (sin persistencia).")
        return
    
    try:
        client = AsyncIOMotorClient(MONGODB_URL, server_api=ServerApi('1'))
        database = client[DATABASE_NAME]
        # Verificar conexión
        await client.admin.command('ping')
        print("✅ Conectado exitosamente a MongoDB!")
    except Exception as e:
        print(f"⚠️ No se pudo conectar a MongoDB: {e}")
        print("⚠️ La app funcionará en modo local (sin persistencia).")
        client = None
        database = None


async def close_mongo_connection():
    """Cerrar conexión a MongoDB"""
    global client
    if client:
        client.close()
        print("✅ Conexión a MongoDB cerrada")


def get_database():
    """Obtener instancia de la base de datos"""
    return database
