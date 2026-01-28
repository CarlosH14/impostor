"""
Script para mejorar definiciones usando un diccionario español gratuito
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

class DefinitionUpdater:
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

    async def get_spanish_definition(self, word):
        """Obtener definición usando diccionario español gratuito"""
        try:
            # Usar Free Dictionary API para español
            url = f"https://api.dictionaryapi.dev/api/v2/entries/es/{word.lower()}"

            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if data and len(data) > 0:
                        meanings = data[0].get('meanings', [])
                        if meanings:
                            definitions = meanings[0].get('definitions', [])
                            if definitions:
                                definition = definitions[0].get('definition', '')
                                if definition:
                                    # Limpiar y formatear
                                    definition = definition.strip()
                                    # Remover números y puntos al inicio
                                    definition = re.sub(r'^\d+\.\s*', '', definition)
                                    return definition[:200]  # Limitar longitud

        except Exception as e:
            print(f"⚠️ Error obteniendo definición para '{word}': {e}")

        return None

    async def get_backup_definition(self, word):
        """Definición de respaldo usando patrones"""
        # Diccionario de definiciones mejoradas manuales para palabras comunes
        improved_definitions = {
            # Comida colombiana
            "BANDEJA PAISA": "Plato típico colombiano con frijoles, carne molida, chicharrón, huevo, arroz y plátano",
            "AJIACO": "Sopa bogotana con pollo, papas, mazorca y guascas",
            "SANCOCHO": "Sopa colombiana con carne, plátano, yuca y verduras",
            "PANDEBONO": "Pan redondo de queso y almidón típico de la región paisa",
            "BUÑUELO": "Dulce navideño frito hecho con queso y harina",
            "NATILLA": "Postre cremoso de maíz dulce típico de Navidad",
            "CHANGUA": "Sopa de leche con huevo cocido típica de Bogotá",
            "LECHONA": "Cerdo relleno de arroz y carne asada al horno",
            "TAMAL": "Masa de maíz rellena envuelta en hoja y cocida",
            "PATACÓN": "Plátano verde aplastado y frito dos veces",
            "CHICHARRÓN": "Piel de cerdo frita hasta quedar crujiente",
            "MAZAMORRA": "Bebida espesa de maíz tierno con leche",
            "OBLEAS": "Galletas delgadas rellenas de arequipe y queso",
            "AREQUIPE": "Dulce de leche espeso hecho con azúcar y leche",
            "BOCADILLO": "Dulce sólido de guayaba con azúcar",
            "AGUA DE PANELA": "Bebida caliente de azúcar de caña diluida",
            "CHOLADO": "Bebida fría con hielo raspado, frutas y leche condensada",
            "LULADA": "Bebida refrescante de lulo con agua y azúcar",
            "CHAMPÚS": "Bebida espesa de maíz, piña y lulo",
            "HORMIGA CULONA": "Hormiga grande comestible frita, especialidad santandereana",
            "CALDO DE COSTILLA": "Sopa de costillas de res con papa y verduras",
            "SUDADO": "Guiso de pescado o carne con verduras y cilantro",
            "CUCHUCO": "Sopa boyacense de trigo con costilla de cerdo",
            "MUTE": "Sopa santandereana de maíz, frijol y carne de cerdo",

            # Frutas colombianas
            "LULO": "Fruta ácida redonda de color anaranjado, típica de Colombia",
            "GUANÁBANA": "Fruta tropical grande verde con pulpa blanca cremosa",
            "CURUBA": "Fruta alargada amarilla de clima frío, muy dulce",
            "UCHUVA": "Fruta pequeña amarilla envuelta en cáscara comestible",
            "GRANADILLA": "Fruta redonda con semillas dulces en interior gelatinoso",
            "MARACUYÁ": "Fruta ácida amarilla con semillas en pulpa aromática",
            "ZAPOTE": "Fruta tropical negra por fuera, blanca cremosa por dentro",
            "PITAYA": "Fruta tropical amarilla con escamas y semillas negras",
            "TOMATE DE ÁRBOL": "Fruta roja alargada muy ácida para jugos",
            "BOROJÓ": "Fruta del Pacífico colombiana con pulpa verde ácida",

            # Lugares colombianos
            "PÁRAMO": "Ecosistema de alta montaña con frailejones y clima frío",
            "FINCA": "Propiedad rural con casa y terrenos cultivables",
            "VEREDA": "División territorial rural más pequeña que un municipio",
            "TIENDA": "Establecimiento pequeño de barrio que vende víveres básicos",
            "PLAZA DE MERCADO": "Mercado tradicional al aire libre con puestos de venta",
            "MALECÓN": "Paseo peatonal junto al río o mar con vista",
            "CORREDOR": "Pasillo interior de la casa en arquitectura colombiana",
            "PATIO": "Espacio abierto interior de la casa rodeado de paredes",

            # Animales colombianos
            "GUACAMAYA": "Ave grande tropical de colores rojo, azul y amarillo",
            "TUCÁN": "Ave tropical con pico grande colorido y negro",
            "PEREZOSO": "Mamífero arborícola que se mueve muy lentamente",
            "OSO DE ANTEOJOS": "Único oso de Sudamérica con manchas blancas",
            "CÓNDOR": "Ave rapaz enorme de los Andes colombianos",
            "JAGUAR": "Felino grande manchado de la selva amazónica",
            "CHIGÜIRO": "Roedor grande similar al capibara, vive en agua",
            "ARMADILLO": "Mamífero con caparazón duro que se enrolla",
            "MARIPOSA MORPHO": "Mariposa grande de alas azules iridiscentes",
            "RANA DARDO": "Rana pequeña venenosa de colores brillantes",

            # Objetos y cultura colombiana
            "RUANA": "Poncho tradicional de lana tejido en Boyacá",
            "SOMBRERO VUELTIAO": "Sombrero tejido de caña típico de la costa",
            "CARRIEL": "Bolso de cuero curtido tradicional paisa",
            "MOCHILA WAYÚU": "Bolso tejido con diseños coloridos de la Guajira",
            "HAMACA": "Tela colgante para descansar o dormir",
            "TOTUMA": "Recipiente hecho de calabaza seca",
            "CHUZO": "Brocheta de carne asada en palo",

            # Plantas colombianas
            "CAFÉ": "Grano para preparar bebida energética y estimulante",
            "PALMA DE CERA": "Árbol nacional alto con tronco blanco",
            "FRAILEJÓN": "Planta peluda del páramo con hojas gruesas",
            "ORQUÍDEA": "Flor nacional delicada y variada en colores",
            "GUADUA": "Bambú gigante usado en construcción colombiana",
            "PLÁTANO": "Fruta alargada verde o amarilla para cocinar",

            # Transporte colombiano
            "CHIVA": "Bus colorido y decorado típico de pueblos",
            "JEEP": "Vehículo todoterreno usado en zonas rurales",
            "MOTOTAXI": "Moto con cabina para transportar pasajeros",
            "TRANSMILENIO": "Sistema masivo de buses articulados en Bogotá",
            "METROCABLE": "Teleférico urbano para transporte público",

            # Juegos y deportes colombianos
            "TEJO": "Juego tradicional de lanzar disco a pólvora",
            "SAPO": "Juego de lanzar fichas a agujeros en madera",
            "BOLAS CRIOLLAS": "Deporte de lanzar bolas pesadas de hierro",

            # Música colombiana
            "VALLENATO": "Género musical del Caribe con acordeón",
            "CUMBIA": "Ritmo y baile tradicional colombiano festivo",
            "BAMBUCO": "Música andina instrumental con flautas",
            "CARRANGA": "Música campesina de Boyacá con arpa",
            "MAPALÉ": "Baile afro del Pacífico colombiano",

            # Definiciones mejoradas para palabras comunes
            "PIZZA": "Masa circular horneada con salsa de tomate, queso y diversos ingredientes",
            "HAMBURGUESA": "Pan redondo relleno con carne molida cocida y vegetales",
            "SUSHI": "Preparación japonesa de arroz con pescado crudo o mariscos",
            "TACO": "Tortilla de maíz doblada rellena de carne y salsa",
            "PASTA": "Alimento elaborado con harina de trigo en diversas formas",
            "HELADO": "Postre congelado dulce hecho con leche o crema",
            "CHOCOLATE": "Producto dulce hecho con cacao y azúcar",
            "PAELLA": "Plato español de arroz con mariscos, carne y verduras",
            "EMPANADA": "Masa rellena de carne o verduras, doblada y horneada",
            "SANDWICH": "Dos rebanadas de pan con relleno entre ellas",
            "ENSALADA": "Mezcla de vegetales frescos crudos con aderezo",
            "AREPA": "Pan plano de maíz blanco típico de Colombia y Venezuela",
            "CEVICHE": "Pescado crudo marinado en jugo de limón con verduras",
            "BURRITO": "Tortilla grande enrollada con frijoles, carne y arroz",
            "LASAÑA": "Pasta horneada en capas con carne, queso y salsa",
            "CROISSANT": "Pan francés hojaldrado en forma de media luna",
            "DONUT": "Rosquilla dulce frita cubierta de azúcar o glaseado",
            "WAFFLE": "Pan con forma cuadriculada hecho en molde especial",
            "PANQUEQUE": "Torta plana dulce cocida en sartén",
            "GALLETA": "Dulce pequeño horneado, generalmente crujiente",
            "YOGURT": "Producto lácteo fermentado espeso y cremoso",
            "CEREAL": "Grano procesado para consumo humano, especialmente desayuno",
            "QUESO": "Producto lácteo sólido obtenido por fermentación",
            "JAMÓN": "Carne curada de pierna de cerdo",
            "SALCHICHA": "Embutido de carne molida en forma cilíndrica",
            "POLLO": "Ave doméstica criada para consumo humano",
            "CARNE": "Tejido muscular de animales para alimentación",
            "PESCADO": "Animal acuático con escamas usado como alimento",
            "HUEVO": "Óvulo de ave, especialmente gallina, comestible",
            "TORTILLA": "Disco plano de maíz o trigo para preparar alimentos",
            "PERRO": "Mamífero doméstico canino, compañero fiel del humano",
            "GATO": "Mamífero felino doméstico pequeño e independiente",
            "ELEFANTE": "Mamífero grande con trompa larga y colmillos",
            "LEÓN": "Felino grande con melena, llamado rey de la selva",
            "DELFÍN": "Mamífero marino inteligente que nada en grupos",
            "PINGÜINO": "Ave marina que no vuela, vive en zonas frías",
            "MARIPOSA": "Insecto con alas coloridas delicadas",
            "COCODRILO": "Reptil grande acuático con mandíbulas poderosas",
            "JIRAFA": "Mamífero alto con cuello largo y manchas",
            "CEBRA": "Mamífero con rayas blancas y negras características",
            "TIGRE": "Felino grande con rayas naranjas y negras",
            "OSO": "Mamífero grande peludo omnívoro",
            "MONO": "Primate arborícola inteligente con cola prensil",
            "SERPIENTE": "Reptil largo sin patas que se arrastra",
            "BALLENA": "Mamífero marino enorme que respira por espiráculo",
            "TIBURÓN": "Pez grande depredador con dientes afilados",
            "ÁGUILA": "Ave rapaz grande con vista muy aguda",
            "BÚHO": "Ave nocturna con ojos grandes y rotatorios",
            "PATO": "Ave acuática con pico plano y patas palmeadas",
            "GALLINA": "Ave doméstica que pone huevos comestibles",
            "CONEJO": "Mamífero pequeño con orejas largas y cola corta",
            "RATÓN": "Roedor pequeño con cola larga y hocico puntiagudo",
            "CABALLO": "Mamífero doméstico grande usado para montar",
            "VACA": "Mamífero doméstico hembra que produce leche",
            "OVEJA": "Mamífero doméstico cubierto de lana",
            "CERDO": "Mamífero doméstico rosado criado para carne",
            "TORTUGA": "Reptil con caparazón duro que camina lentamente",
            "RANA": "Anfibio verde que salta y croa",
            "ABEJA": "Insecto que produce miel y poliniza flores",
            "HORMIGA": "Insecto trabajador que vive en colonias organizadas",
            "ARAÑA": "Arácnido con ocho patas que teje telarañas",
            "MOSCA": "Insecto volador pequeño molesto",
            "MOSQUITO": "Insecto volador que pica y chupa sangre",
            "CANGREJO": "Crustáceo con pinzas que camina lateralmente",
            "PULPO": "Molusco marino con ocho tentáculos",
            "PLAYA": "Extensión de arena junto al mar o lago",
            "MONTAÑA": "Elevación natural del terreno muy alta",
            "HOSPITAL": "Institución médica donde se atienden enfermos",
            "ESCUELA": "Institución educativa donde se enseña a niños",
            "MUSEO": "Lugar que exhibe objetos artísticos e históricos",
            "BIBLIOTECA": "Lugar con colección de libros para consulta",
            "AEROPUERTO": "Instalación para despegue y aterrizaje de aviones",
            "PARQUE": "Área verde pública para recreación",
            "CINE": "Sala para proyección de películas",
            "RESTAURANTE": "Establecimiento que sirve comidas preparadas",
            "SUPERMERCADO": "Tienda grande que vende alimentos y productos",
            "FARMACIA": "Establecimiento que vende medicamentos",
            "BANCO": "Institución financiera que guarda dinero",
            "IGLESIA": "Templo religioso cristiano",
            "ESTADIO": "Recinto deportivo grande con graderías",
            "ZOOLÓGICO": "Parque que exhibe animales salvajes",
            "CIRCO": "Espectáculo con artistas, animales y payasos",
            "TEATRO": "Lugar para representaciones artísticas escénicas",
            "HOTEL": "Establecimiento con habitaciones para hospedaje",
            "GIMNASIO": "Lugar con equipos para hacer ejercicio",
            "PISCINA": "Construcción con agua para nadar",
            "JARDÍN": "Terreno cultivado con flores y plantas",
            "BOSQUE": "Área extensa cubierta de árboles",
            "DESIERTO": "Región árida con poca vegetación",
            "SELVA": "Bosque tropical denso con mucha biodiversidad",
            "RÍO": "Corriente natural de agua dulce",
            "LAGO": "Masa de agua dulce rodeada de tierra",
            "OCÉANO": "Masa enorme de agua salada",
            "VOLCÁN": "Montaña que expulsa lava y cenizas",
            "CUEVA": "Cavidad subterránea natural en roca",
            "LÁPIZ": "Instrumento para escribir con mina de grafito",
            "LIBRO": "Conjunto de hojas impresas encuadernadas",
            "TELÉFONO": "Aparato para comunicación a distancia por voz",
            "COMPUTADORA": "Máquina electrónica para procesar información",
            "TELEVISIÓN": "Aparato para recibir y mostrar imágenes transmitidas",
            "RELOJ": "Dispositivo que indica la hora",
            "ESPEJO": "Superficie pulida que refleja imágenes",
            "SILLA": "Mueble con respaldo para sentarse",
            "MESA": "Mueble plano elevado sostenido por patas",
            "CAMA": "Mueble acolchado para dormir",
            "LÁMPARA": "Artefacto que produce luz artificial",
            "VENTANA": "Abertura en pared con vidrio para luz",
            "PUERTA": "Panel móvil que cierra entrada o salida",
            "LLAVE": "Objeto metálico para abrir cerraduras",
            "TIJERAS": "Herramienta con dos hojas afiladas para cortar",
            "CUCHILLO": "Herramienta con hoja afilada para cortar alimentos",
            "TENEDOR": "Utensilio con puntas para pinchar comida",
            "CUCHARA": "Utensilio cóncavo para líquidos y alimentos",
            "PLATO": "Recipiente plano para servir comida",
            "VASO": "Recipiente cilíndrico para beber líquidos",
            "TAZA": "Recipiente con asa para bebidas calientes",
            "BOTELLA": "Recipiente de vidrio o plástico para líquidos",
            "BOLSA": "Contenedor flexible de tela o plástico",
            "MALETA": "Equipaje con ruedas para transportar ropa",
            "MOCHILA": "Bolsa con correas para llevar en espalda",
            "PARAGUAS": "Objeto plegable que protege de la lluvia",
            "GAFAS": "Lentes con marco para corregir o proteger vista",
            "SOMBRERO": "Prenda que cubre y protege la cabeza",
            "ZAPATO": "Calzado que protege el pie",
            "CAMISA": "Prenda de vestir para torso con mangas",
            "PANTALÓN": "Prenda que cubre piernas desde cintura",
            "VESTIDO": "Prenda femenina de una pieza",
            "FALDA": "Prenda femenina que cubre desde cintura",
            "BUFANDA": "Tela larga para abrigar cuello",
            "GUANTES": "Prendas que cubren las manos",
            "CORBATA": "Tira decorativa que se anuda al cuello",
            "CINTURÓN": "Correa que sujeta el pantalón a la cintura",
            "ABRIGO": "Prenda gruesa para proteger del frío",
            "FÚTBOL": "Deporte con balón entre dos equipos de once jugadores",
            "BALONCESTO": "Deporte de encestar balón en canasta alta",
            "BÉISBOL": "Deporte con bate y pelota entre dos equipos",
            "TENIS": "Deporte con raqueta sobre red entre dos jugadores",
            "VOLEIBOL": "Deporte de golpear balón sobre red",
            "NATACIÓN": "Deporte de nadar en agua",
            "ATLETISMO": "Deportes de pista y campo con carreras y saltos",
            "CICLISMO": "Deporte de competir en bicicleta",
            "BOXEO": "Deporte de combate con guantes entre dos personas",
            "GOLF": "Deporte de meter pelota en hoyo con palo",
            "RUGBY": "Deporte de contacto con balón ovalado",
            "HOCKEY": "Deporte con palo y disco sobre hielo",
            "ESQUÍ": "Deporte de deslizarse sobre nieve con esquís",
            "SURF": "Deporte de deslizarse sobre olas del mar",
            "KARATE": "Arte marcial japonés de golpes con manos y pies",
            "JUDO": "Arte marcial de lanzamientos y llaves",
            "GIMNASIA": "Deporte de acrobacias y flexibilidad corporal",
            "ESCALADA": "Deporte de subir paredes o montañas",
            "PATINAJE": "Deporte de deslizarse sobre patines",
            "MÉDICO": "Profesional que diagnostica y trata enfermedades",
            "ENFERMERO": "Profesional que cuida pacientes en hospital",
            "PROFESOR": "Profesional que enseña conocimientos en institución educativa",
            "INGENIERO": "Profesional que diseña y construye estructuras",
            "ARQUITECTO": "Profesional que diseña edificios y espacios",
            "ABOGADO": "Profesional experto en derecho y leyes",
            "POLICÍA": "Agente que mantiene orden público y seguridad",
            "BOMBERO": "Profesional que apaga incendios y rescata personas",
            "CHEF": "Profesional que prepara alimentos en restaurante",
            "MÚSICO": "Profesional que interpreta música con instrumentos",
            "PINTOR": "Profesional que crea arte visual con pinturas",
            "ESCRITOR": "Profesional que crea textos literarios",
            "PERIODISTA": "Profesional que investiga y reporta noticias",
            "FOTÓGRAFO": "Profesional que captura imágenes con cámara",
            "PILOTO": "Profesional que maneja aviones",
            "CONDUCTOR": "Profesional que maneja vehículos terrestres",
            "CARPINTERO": "Profesional que trabaja madera para construcción",
            "ELECTRICISTA": "Profesional que instala y repara sistemas eléctricos",
            "PLOMERO": "Profesional que instala y repara tuberías",
            "MECÁNICO": "Profesional que repara vehículos y máquinas",
            "SOL": "Estrella central del sistema solar que da luz",
            "LUNA": "Satélite natural de la Tierra",
            "ESTRELLA": "Cuerpo celeste luminoso visible de noche",
            "NUBE": "Masa de vapor de agua suspendida en atmósfera",
            "LLUVIA": "Precipitación de agua desde nubes",
            "NIEVE": "Precipitación de cristales de hielo",
            "VIENTO": "Movimiento del aire en la atmósfera",
            "TRUENO": "Sonido fuerte causado por rayo",
            "RAYO": "Descarga eléctrica entre nube y tierra",
            "ARCOÍRIS": "Arco de colores en cielo después de lluvia",
            "ÁRBOL": "Planta perenne grande con tronco leñoso",
            "FLOR": "Parte reproductiva colorida de las plantas",
            "PASTO": "Hierba verde que cubre el suelo",
            "HOJA": "Parte plana verde de las plantas",
            "RAÍZ": "Parte subterránea que absorbe agua y nutrientes",
            "SEMILLA": "Parte de planta que da origen a nueva",
            "FRUTO": "Parte de planta que contiene semillas",
            "ROSA": "Flor con pétalos suaves y espinas",
            "GIRASOL": "Flor grande amarilla que sigue al sol",
            "FELICIDAD": "Estado emocional de alegría y satisfacción",
            "TRISTEZA": "Estado emocional de pena y melancolía",
            "ENOJO": "Estado emocional de irritación y molestia",
            "MIEDO": "Estado emocional de temor ante peligro",
            "SORPRESA": "Estado emocional ante algo inesperado",
            "AMOR": "Sentimiento profundo de afecto hacia alguien",
            "ODIO": "Sentimiento intenso de repulsión",
            "ANSIEDAD": "Estado de preocupación y nerviosismo",
            "CALMA": "Estado de tranquilidad y paz interior",
            "ABURRIMIENTO": "Estado de falta de interés o entretenimiento",
            "EMOCIÓN": "Estado de excitación o entusiasmo intenso",
            "NOSTALGIA": "Sentimiento de añoranza por el pasado",
            "VERGÜENZA": "Sentimiento de incomodidad social",
            "ORGULLO": "Sentimiento de satisfacción personal",
            "CULPA": "Sentimiento de haber hecho algo malo",
            "GRATITUD": "Sentimiento de agradecimiento",
            "ESPERANZA": "Sentimiento de expectativa positiva",
            "DECEPCIÓN": "Sentimiento cuando no se cumple expectativa",
            "CONFUSIÓN": "Estado mental de desorientación",
            "CURIOSIDAD": "Deseo de conocer o aprender algo",
            "CABEZA": "Parte superior del cuerpo con cerebro",
            "CARA": "Parte frontal de la cabeza",
            "OJO": "Órgano de la vista",
            "OREJA": "Órgano del oído",
            "NARIZ": "Órgano del olfato y respiración",
            "BOCA": "Abertura para comer y hablar",
            "DIENTE": "Pieza dura en boca para masticar",
            "LENGUA": "Músculo en boca para saborear",
            "CUELLO": "Parte que conecta cabeza y torso",
            "HOMBRO": "Articulación entre brazo y torso",
            "BRAZO": "Extremidad superior del cuerpo",
            "MANO": "Extremo del brazo con dedos",
            "DEDO": "Extensión de mano o pie",
            "PECHO": "Parte frontal del torso",
            "ESPALDA": "Parte posterior del torso",
            "ESTÓMAGO": "Órgano que digiere alimentos",
            "CORAZÓN": "Órgano que bombea sangre",
            "PULMÓN": "Órgano para respirar oxígeno",
            "PIERNA": "Extremidad inferior del cuerpo",
            "PIE": "Extremo de la pierna para caminar",
            "RODILLA": "Articulación en medio de la pierna",
            "CODO": "Articulación en medio del brazo",
            "HUESO": "Estructura dura que forma esqueleto",
            "MÚSCULO": "Tejido que produce movimiento",
            "PIEL": "Tejido que cubre el cuerpo",
            "SANGRE": "Líquido rojo que circula por cuerpo",
            "CEREBRO": "Órgano central del sistema nervioso",
            "PELO": "Filamento que crece en piel",
            "UÑA": "Lámina dura en extremo de dedos",
            "CEJA": "Pelo sobre los ojos",
        }

        return improved_definitions.get(word.upper(), None)

    async def improve_definition(self, word, current_definition):
        """Mejorar definición usando múltiples fuentes"""
        # Intentar diccionario español primero
        definition = await self.get_spanish_definition(word)
        if definition:
            return definition

        # Usar definición de respaldo mejorada
        backup = await self.get_backup_definition(word)
        if backup:
            return backup

        # Si no se encuentra mejor definición, mantener la actual
        return current_definition

    async def update_definitions(self):
        """Actualizar definiciones en la base de datos"""
        try:
            # Obtener todas las palabras
            words_collection = self.db.words
            words = list(words_collection.find({}))

            print(f"\n📝 Procesando {len(words)} palabras...")

            updated_count = 0
            batch_size = 10  # Procesar en lotes para no sobrecargar

            for i, word_doc in enumerate(words):
                word = word_doc.get('word', '')
                current_definition = word_doc.get('definition', '')

                # Mejorar definición
                improved_definition = await self.improve_definition(word, current_definition)

                # Actualizar si cambió
                if improved_definition != current_definition:
                    words_collection.update_one(
                        {'_id': word_doc['_id']},
                        {'$set': {'definition': improved_definition}}
                    )
                    updated_count += 1
                    print(f"  ✓ Mejorada: {word}")
                else:
                    print(f"  - Sin cambio: {word}")

                # Pequeña pausa para no sobrecargar APIs
                if (i + 1) % batch_size == 0:
                    print(f"  📊 Progreso: {i + 1}/{len(words)} palabras procesadas")
                    await asyncio.sleep(1)  # Pausa de 1 segundo

            print(f"\n✅ {updated_count} definiciones mejoradas!")

        except Exception as e:
            print(f"❌ Error actualizando definiciones: {e}")
            raise

    async def close(self):
        """Cerrar conexiones"""
        if self.session:
            await self.session.close()
        if self.client:
            self.client.close()

async def main():
    updater = DefinitionUpdater()

    try:
        print("=" * 60)
        print("🔧 MEJORANDO DEFINICIONES CON DICCIONARIOS ESPAÑOLES")
        print("=" * 60)

        await updater.connect_db()
        await updater.init_session()
        await updater.update_definitions()

        print("\n🎉 ¡Proceso completado!")

    except Exception as e:
        print(f"❌ Error en el proceso: {e}")
    finally:
        await updater.close()

if __name__ == "__main__":
    asyncio.run(main())
