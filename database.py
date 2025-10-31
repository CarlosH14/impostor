from pymongo import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv

load_dotenv()

# Configuración de MongoDB
MONGODB_URL = os.getenv("MONGODB_URL", "")
DATABASE_NAME = os.getenv("DATABASE_NAME", "impostor_game")

# Cliente sincrónico para entornos serverless
_client = None
_connection_attempted = False


def get_mongo_client():
    """Obtener cliente de MongoDB (sincrónico, mejor para serverless)"""
    global _client, _connection_attempted
    
    # Si no hay URL configurada
    if not MONGODB_URL or "<db_username>" in MONGODB_URL:
        return None
    
    # Si ya existe cliente, reutilizarlo
    if _client is not None:
        return _client
    
    # Si ya intentamos conectar y falló
    if _connection_attempted and _client is None:
        return None
    
    _connection_attempted = True
    
    try:
        print(f"🔄 Conectando a MongoDB (sincrónico)...")
        _client = MongoClient(
            MONGODB_URL,
            server_api=ServerApi('1'),
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=5000,
            maxPoolSize=1  # Pool pequeño para serverless
        )
        # Verificar conexión
        _client.admin.command('ping')
        print("✅ Conectado exitosamente a MongoDB!")
        return _client
    except Exception as e:
        print(f"⚠️ No se pudo conectar a MongoDB: {e}")
        _client = None
        return None


async def connect_to_mongo():
    """Conectar a MongoDB (compatibilidad con eventos de FastAPI)"""
    get_mongo_client()


async def close_mongo_connection():
    """Cerrar conexión a MongoDB"""
    global _client
    if _client:
        _client.close()
        print("✅ Conexión a MongoDB cerrada")


async def get_database():
    """Obtener instancia de la base de datos"""
    client = get_mongo_client()
    
    if client is None:
        return None
    
    return client[DATABASE_NAME]
