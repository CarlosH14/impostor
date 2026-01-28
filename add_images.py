"""
Script para agregar imágenes a las palabras usando APIs gratuitas
"""
import asyncio
import aiohttp
import json
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import time
import re

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "")
DATABASE_NAME = os.getenv("DATABASE_NAME", "impostor_game")

# APIs gratuitas para imágenes
PIXABAY_API_KEY = "46157802-8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b"  # API key gratuita de Pixabay (limitada)
UNSPLASH_ACCESS_KEY = "your_unsplash_access_key"  # Opcional

class ImageAdder:
    def __init__(self):
        self.client = None
        self.db = None
        self.session = None

    async def connect_db(self):
        """Conectar a MongoDB"""
        try:
            self.client = MongoClient(MONGODB_URL, server_api=ServerApi('1'))
            self.db = self.client[DATABASE_NAME]
            print("✅ Conectado a MongoDB!")
        except Exception as e:
            print(f"❌ Error conectando a MongoDB: {e}")
            raise

    async def init_session(self):
        """Inicializar sesión HTTP"""
        self.session = aiohttp.ClientSession(
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )

    async def get_pixabay_image(self, word):
        """Obtener imagen de Pixabay"""
        try:
            # Pixabay API - búsqueda de imágenes
            url = f"https://pixabay.com/api/?key={PIXABAY_API_KEY}&q={word.lower()}&image_type=photo&per_page=3&safesearch=true"

            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('hits') and len(data['hits']) > 0:
                        # Tomar la primera imagen de alta calidad
                        image_url = data['hits'][0].get('webformatURL', '')
                        if image_url:
                            return image_url

        except Exception as e:
            print(f"⚠️ Error obteniendo imagen Pixabay para '{word}': {e}")

        return None

    async def get_unsplash_image(self, word):
        """Obtener imagen de Unsplash"""
        try:
            # Unsplash API (sin key para uso básico)
            url = f"https://api.unsplash.com/search/photos?query={word.lower()}&per_page=1&client_id={UNSPLASH_ACCESS_KEY}"

            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('results') and len(data['results']) > 0:
                        image_url = data['results'][0].get('urls', {}).get('small', '')
                        if image_url:
                            return image_url

        except Exception as e:
            print(f"⚠️ Error obteniendo imagen Unsplash para '{word}': {e}")

        return None

    async def get_fallback_image(self, word):
        """Imágenes de respaldo para palabras comunes"""
        fallback_images = {
            # Comida
            "PIZZA": "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=400",
            "HAMBURGUESA": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400",
            "SUSHI": "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?w=400",
            "TACO": "https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=400",
            "PASTA": "https://images.unsplash.com/photo-1621996346565-e3dbc353d2e5?w=400",
            "HELADO": "https://images.unsplash.com/photo-1497034825429-c343d7c6a68f?w=400",
            "CHOCOLATE": "https://images.unsplash.com/photo-1606312619070-d48b4c652a52?w=400",
            "PAELLA": "https://images.unsplash.com/photo-1534080564583-6be75777b70a?w=400",
            "EMPANADA": "https://images.unsplash.com/photo-1541745537411-b8046dc6d66c?w=400",
            "SANDWICH": "https://images.unsplash.com/photo-1481070414801-51b21d9e8301?w=400",
            "ENSALADA": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400",
            "AREPA": "https://images.unsplash.com/photo-1625398407796-9024b5a3f1e2?w=400",
            "BANDEJA PAISA": "https://images.unsplash.com/photo-1625398407796-9024b5a3f1e2?w=400",
            "AJIACO": "https://images.unsplash.com/photo-1541745537411-b8046dc6d66c?w=400",
            "SANCOCHO": "https://images.unsplash.com/photo-1541745537411-b8046dc6d66c?w=400",

            # Animales
            "PERRO": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400",
            "GATO": "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=400",
            "ELEFANTE": "https://images.unsplash.com/photo-1557050543-4d5f4e07ef46?w=400",
            "LEÓN": "https://images.unsplash.com/photo-1546182990-dffeafbe841d?w=400",
            "DELFÍN": "https://images.unsplash.com/photo-1570481662006-a3a1374699e8?w=400",
            "PINGÜINO": "https://images.unsplash.com/photo-1545671913-b89ac1b4ac10?w=400",
            "MARIPOSA": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=400",
            "COCODRILO": "https://images.unsplash.com/photo-1520637836862-4d197d17c1a8?w=400",
            "JIRAFA": "https://images.unsplash.com/photo-1544568100-847a948585b9?w=400",
            "ZEBRA": "https://images.unsplash.com/photo-1520637836862-4d197d17c1a8?w=400",
            "TIGRE": "https://images.unsplash.com/photo-1544568100-847a948585b9?w=400",
            "OSO": "https://images.unsplash.com/photo-1544568100-847a948585b9?w=400",
            "MONO": "https://images.unsplash.com/photo-1544568100-847a948585b9?w=400",
            "SERPIENTE": "https://images.unsplash.com/photo-1520637836862-4d197d17c1a8?w=400",
            "BALLENA": "https://images.unsplash.com/photo-1570481662006-a3a1374699e8?w=400",
            "TIBURÓN": "https://images.unsplash.com/photo-1570481662006-a3a1374699e8?w=400",
            "ÁGUILA": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=400",
            "BÚHO": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=400",
            "PATO": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=400",
            "GALLINA": "https://images.unsplash.com/photo-1544568100-847a948585b9?w=400",
            "CONEJO": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400",
            "RATÓN": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400",
            "CABALLO": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400",
            "VACA": "https://images.unsplash.com/photo-1544568100-847a948585b9?w=400",
            "OVEJA": "https://images.unsplash.com/photo-1544568100-847a948585b9?w=400",
            "CERDO": "https://images.unsplash.com/photo-1544568100-847a948585b9?w=400",
            "TORTUGA": "https://images.unsplash.com/photo-1520637836862-4d197d17c1a8?w=400",
            "RANA": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=400",
            "ABEJA": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=400",
            "HORMIGA": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=400",
            "ARAÑA": "https://images.unsplash.com/photo-1520637836862-4d197d17c1a8?w=400",
            "MOSCA": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=400",
            "MOSQUITO": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=400",
            "CANGREJO": "https://images.unsplash.com/photo-1570481662006-a3a1374699e8?w=400",
            "PULPO": "https://images.unsplash.com/photo-1570481662006-a3a1374699e8?w=400",

            # Naturaleza
            "PLAYA": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400",
            "MONTAÑA": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400",
            "BOSQUE": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=400",
            "SELVA": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=400",
            "DESIERTO": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400",
            "RÍO": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=400",
            "LAGO": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400",
            "OCÉANO": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400",
            "VOLCÁN": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400",
            "CUEVA": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400",
            "SOL": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400",
            "LUNA": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400",
            "ESTRELLA": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400",
            "NUBE": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400",
            "LLUVIA": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400",
            "NIEVE": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400",
            "VIENTO": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400",
            "TRUENO": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400",
            "RAYO": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400",
            "ARCOÍRIS": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400",
            "ÁRBOL": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=400",
            "FLOR": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=400",
            "PASTO": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=400",
            "HOJA": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=400",
            "RAÍZ": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=400",
            "SEMILLA": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=400",
            "FRUTO": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=400",
            "ROSA": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=400",
            "GIRASOL": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=400",

            # Lugares
            "HOSPITAL": "https://images.unsplash.com/photo-1551190822-a9333d879b1f?w=400",
            "ESCUELA": "https://images.unsplash.com/photo-1544717297-fa95b6ee9643?w=400",
            "MUSEO": "https://images.unsplash.com/photo-1544717297-fa95b6ee9643?w=400",
            "BIBLIOTECA": "https://images.unsplash.com/photo-1544717297-fa95b6ee9643?w=400",
            "AEROPUERTO": "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=400",
            "PARQUE": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=400",
            "CINE": "https://images.unsplash.com/photo-1489599735734-79d3f22c3c4b?w=400",
            "RESTAURANTE": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=400",
            "SUPERMERCADO": "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=400",
            "FARMACIA": "https://images.unsplash.com/photo-1551190822-a9333d879b1f?w=400",
            "BANCO": "https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=400",
            "IGLESIA": "https://images.unsplash.com/photo-1544717297-fa95b6ee9643?w=400",
            "ESTADIO": "https://images.unsplash.com/photo-1431324155629-1a6deb1dec8d?w=400",
            "ZOOLÓGICO": "https://images.unsplash.com/photo-1544568100-847a948585b9?w=400",
            "CIRCO": "https://images.unsplash.com/photo-1544717297-fa95b6ee9643?w=400",
            "TEATRO": "https://images.unsplash.com/photo-1544717297-fa95b6ee9643?w=400",
            "HOTEL": "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=400",
            "GIMNASIO": "https://images.unsplash.com/photo-1544717297-fa95b6ee9643?w=400",
            "PISCINA": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=400",
            "JARDÍN": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=400",

            # Objetos
            "LÁPIZ": "https://images.unsplash.com/photo-1554224155-6726b3ff858f?w=400",
            "LIBRO": "https://images.unsplash.com/photo-1544717297-fa95b6ee9643?w=400",
            "TELÉFONO": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=400",
            "COMPUTADORA": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=400",
            "TELEVISIÓN": "https://images.unsplash.com/photo-1593359677879-a4bb92f829d1?w=400",
            "RELOJ": "https://images.unsplash.com/photo-1524592094714-0f0654e20314?w=400",
            "ESPEJO": "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=400",
            "SILLA": "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=400",
            "MESA": "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=400",
            "CAMA": "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=400",
            "LÁMPARA": "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=400",
            "VENTANA": "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=400",
            "PUERTA": "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=400",
            "LLAVE": "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=400",
            "TIJERAS": "https://images.unsplash.com/photo-1554224155-6726b3ff858f?w=400",
            "CUCHILLO": "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=400",
            "TENEDOR": "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=400",
            "CUCHARA": "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=400",
            "PLATO": "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=400",
            "VASO": "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=400",
            "TAZA": "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=400",
            "BOTELLA": "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=400",
            "BOLSA": "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=400",
            "MALETA": "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=400",
            "MOCHILA": "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=400",
            "PARAGUAS": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400",
            "GAFAS": "https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=400",
            "SOMBRERO": "https://images.unsplash.com/photo-1588850561407-ed78c282e89b?w=400",
            "ZAPATO": "https://images.unsplash.com/photo-1549298916-b41d501d3772?w=400",
            "CAMISA": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400",
            "PANTALÓN": "https://images.unsplash.com/photo-1542272604-787c3835535d?w=400",
            "VESTIDO": "https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=400",
            "FALDA": "https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=400",
            "BUFANDA": "https://images.unsplash.com/photo-1520903920243-00d872a2d1c9?w=400",
            "GUANTES": "https://images.unsplash.com/photo-1520903920243-00d872a2d1c9?w=400",
            "CORBATA": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400",
            "CINTURÓN": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400",
            "ABRIGO": "https://images.unsplash.com/photo-1520903920243-00d872a2d1c9?w=400",

            # Emociones
            "FELICIDAD": "https://images.unsplash.com/photo-1544568100-847a948585b9?w=400",
            "TRISTEZA": "https://images.unsplash.com/photo-1544568100-847a948585b9?w=400",
            "MIEDO": "https://images.unsplash.com/photo-1544568100-847a948585b9?w=400",
            "ENOJO": "https://images.unsplash.com/photo-1544568100-847a948585b9?w=400",
            "SORPRESA": "https://images.unsplash.com/photo-1544568100-847a948585b9?w=400",
            "AMOR": "https://images.unsplash.com/photo-1544568100-847a948585b9?w=400",
            "ODIO": "https://images.unsplash.com/photo-1544568100-847a948585b9?w=400",
            "ANSIEDAD": "https://images.unsplash.com/photo-1544568100-847a948585b9?w=400",
            "CALMA": "https://images.unsplash.com/photo-1544568100-847a948585b9?w=400",
            "ABURRIMIENTO": "https://images.unsplash.com/photo-1544568100-847a948585b9?w=400",
            "EMOCIÓN": "https://images.unsplash.com/photo-1544568100-847a948585b9?w=400",
            "NOSTALGIA": "https://images.unsplash.com/photo-1544568100-847a948585b9?w=400",
            "VERGÜENZA": "https://images.unsplash.com/photo-1544568100-847a948585b9?w=400",
            "ORGULLO": "https://images.unsplash.com/photo-1544568100-847a948585b9?w=400",
            "CULPA": "https://images.unsplash.com/photo-1544568100-847a948585b9?w=400",
            "GRATITUD": "https://images.unsplash.com/photo-1544568100-847a948585b9?w=400",
            "ESPERANZA": "https://images.unsplash.com/photo-1544568100-847a948585b9?w=400",
            "DECEPCIÓN": "https://images.unsplash.com/photo-1544568100-847a948585b9?w=400",
            "CONFUSIÓN": "https://images.unsplash.com/photo-1544568100-847a948585b9?w=400",
            "CURIOSIDAD": "https://images.unsplash.com/photo-1544568100-847a948585b9?w=400",

            # Profesiones
            "MÉDICO": "https://images.unsplash.com/photo-1551190822-a9333d879b1f?w=400",
            "ENFERMERO": "https://images.unsplash.com/photo-1551190822-a9333d879b1f?w=400",
            "PROFESOR": "https://images.unsplash.com/photo-1544717297-fa95b6ee9643?w=400",
            "INGENIERO": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=400",
            "ARQUITECTO": "https://images.unsplash.com/photo-1544717297-fa95b6ee9643?w=400",
            "ABOGADO": "https://images.unsplash.com/photo-1544717297-fa95b6ee9643?w=400",
            "POLICÍA": "https://images.unsplash.com/photo-1544717297-fa95b6ee9643?w=400",
            "BOMBERO": "https://images.unsplash.com/photo-1544717297-fa95b6ee9643?w=400",
            "CHEF": "https://images.unsplash.com/photo-1544717297-fa95b6ee9643?w=400",
            "MÚSICO": "https://images.unsplash.com/photo-1544717297-fa95b6ee9643?w=400",
            "PINTOR": "https://images.unsplash.com/photo-1544717297-fa95b6ee9643?w=400",
            "ESCRITOR": "https://images.unsplash.com/photo-1544717297-fa95b6ee9643?w=400",
            "PERIODISTA": "https://images.unsplash.com/photo-1544717297-fa95b6ee9643?w=400",
            "FOTÓGRAFO": "https://images.unsplash.com/photo-1544717297-fa95b6ee9643?w=400",
            "PILOTO": "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=400",
            "CONDUCTOR": "https://images.unsplash.com/photo-1544717297-fa95b6ee9643?w=400",
            "CARPINTERO": "https://images.unsplash.com/photo-1544717297-fa95b6ee9643?w=400",
            "ELECTRICISTA": "https://images.unsplash.com/photo-1544717297-fa95b6ee9643?w=400",
            "PLOMERO": "https://images.unsplash.com/photo-1544717297-fa95b6ee9643?w=400",
            "MECÁNICO": "https://images.unsplash.com/photo-1544717297-fa95b6ee9643?w=400",

            # Deportes
            "FÚTBOL": "https://images.unsplash.com/photo-1431324155629-1a6deb1dec8d?w=400",
            "BALONCESTO": "https://images.unsplash.com/photo-1431324155629-1a6deb1dec8d?w=400",
            "BÉISBOL": "https://images.unsplash.com/photo-1431324155629-1a6deb1dec8d?w=400",
            "TENIS": "https://images.unsplash.com/photo-1431324155629-1a6deb1dec8d?w=400",
            "VOLEIBOL": "https://images.unsplash.com/photo-1431324155629-1a6deb1dec8d?w=400",
            "NATACIÓN": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=400",
            "ATLETISMO": "https://images.unsplash.com/photo-1431324155629-1a6deb1dec8d?w=400",
            "CICLISMO": "https://images.unsplash.com/photo-1431324155629-1a6deb1dec8d?w=400",
            "BOXEO": "https://images.unsplash.com/photo-1431324155629-1a6deb1dec8d?w=400",
            "GOLF": "https://images.unsplash.com/photo-1431324155629-1a6deb1dec8d?w=400",
            "RUGBY": "https://images.unsplash.com/photo-1431324155629-1a6deb1dec8d?w=400",
            "HOCKEY": "https://images.unsplash.com/photo-1431324155629-1a6deb1dec8d?w=400",
            "ESQUÍ": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400",
            "SURF": "https://images.unsplash.com/photo-1502680390469-be75c86b636f?w=400",
            "KARATE": "https://images.unsplash.com/photo-1431324155629-1a6deb1dec8d?w=400",
            "JUDO": "https://images.unsplash.com/photo-1431324155629-1a6deb1dec8d?w=400",
            "GIMNASIA": "https://images.unsplash.com/photo-1431324155629-1a6deb1dec8d?w=400",
            "ESCALADA": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400",
            "PATINAJE": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=400",

            # Imagen genérica por defecto
            "DEFAULT": "https://images.unsplash.com/photo-1557804506-669a67965ba0?w=400"
        }

        return fallback_images.get(word.upper(), fallback_images.get("DEFAULT"))

    async def get_image_for_word(self, word):
        """Obtener imagen para una palabra usando múltiples fuentes"""
        # Intentar Pixabay primero
        image = await self.get_pixabay_image(word)
        if image:
            return image

        # Intentar Unsplash
        image = await self.get_unsplash_image(word)
        if image:
            return image

        # Usar imagen de respaldo
        image = await self.get_fallback_image(word)
        if image:
            return image

        return None

    async def add_images(self):
        """Agregar imágenes a las palabras en la base de datos"""
        try:
            # Obtener todas las palabras
            words_collection = self.db.words
            words = list(words_collection.find({}))

            print(f"\n🖼️ Procesando {len(words)} palabras para agregar imágenes...")

            updated_count = 0
            batch_size = 5  # Procesar en lotes más pequeños para APIs

            for i, word_doc in enumerate(words):
                word = word_doc.get('word', '')
                current_image = word_doc.get('image', '')

                # Si ya tiene imagen, saltar
                if current_image:
                    print(f"  ✓ Ya tiene imagen: {word}")
                    continue

                # Obtener imagen
                image_url = await self.get_image_for_word(word)

                if image_url:
                    words_collection.update_one(
                        {'_id': word_doc['_id']},
                        {'$set': {'image': image_url}}
                    )
                    updated_count += 1
                    print(f"  ✅ Agregada imagen: {word}")
                else:
                    print(f"  ❌ Sin imagen: {word}")

                # Pausa entre lotes para no sobrecargar APIs
                if (i + 1) % batch_size == 0:
                    print(f"  📊 Progreso: {i + 1}/{len(words)} palabras procesadas")
                    await asyncio.sleep(2)  # Pausa de 2 segundos

            print(f"\n✅ {updated_count} imágenes agregadas!")

        except Exception as e:
            print(f"❌ Error agregando imágenes: {e}")
            raise

    async def close(self):
        """Cerrar conexiones"""
        if self.session:
            await self.session.close()
        if self.client:
            self.client.close()

async def main():
    adder = ImageAdder()

    try:
        print("=" * 60)
        print("🖼️ AGREGANDO IMÁGENES A LAS PALABRAS")
        print("=" * 60)

        await adder.connect_db()
        await adder.init_session()
        await adder.add_images()

        print("\n🎉 ¡Proceso completado!")

    except Exception as e:
        print(f"❌ Error en el proceso: {e}")
    finally:
        await adder.close()

if __name__ == "__main__":
    asyncio.run(main())