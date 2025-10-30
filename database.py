from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv

load_dotenv()

# Configuración de MongoDB
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb+srv://<db_username>:<db_password>@impostordb.gl1cvjc.mongodb.net/?appName=impostordb")
DATABASE_NAME = os.getenv("DATABASE_NAME", "impostor_game")

# Cliente de MongoDB
client = None
database = None


async def connect_to_mongo():
    """Conectar a MongoDB"""
    global client, database
    try:
        client = AsyncIOMotorClient(MONGODB_URL, server_api=ServerApi('1'))
        database = client[DATABASE_NAME]
        # Verificar conexión
        await client.admin.command('ping')
        print("✅ Conectado exitosamente a MongoDB!")
    except Exception as e:
        print(f"❌ Error conectando a MongoDB: {e}")
        raise


async def close_mongo_connection():
    """Cerrar conexión a MongoDB"""
    global client
    if client:
        client.close()
        print("✅ Conexión a MongoDB cerrada")


def get_database():
    """Obtener instancia de la base de datos"""
    return database
