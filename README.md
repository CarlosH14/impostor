# Impostor Game API

API REST desarrollada con FastAPI para el juego del impostor.

## Descripción del Juego

El juego consiste en un grupo de X jugadores donde hay 1 impostor. En una ronda del juego, cada jugador recibe una palabra. Todos los jugadores normales reciben la misma palabra, excepto el impostor que recibe la palabra "IMPOSTOR".

## Instalación

1. Instalar dependencias:
```bash
pip install -r requirements.txt
```

2. Ejecutar el servidor:
```bash
python main.py
```

O con uvicorn directamente:
```bash
uvicorn main:app --reload
```

El servidor estará disponible en `http://localhost:8000`

## Endpoints

### 1. Crear Partida
**POST** `/game/create`

Crea una nueva partida y añade al primer jugador (host).

**Body:**
```json
{
  "player_name": "Carlos",
  "max_players": 8
}
```

**Response:**
```json
{
  "game_id": "uuid-generado",
  "status": "waiting",
  "players": [...],
  "max_players": 8
}
```

### 2. Unirse a Partida
**POST** `/game/join`

Permite a un jugador unirse a una partida existente.

**Body:**
```json
{
  "player_name": "Maria",
  "game_id": "uuid-de-la-partida"
}
```

### 3. Iniciar Ronda
**POST** `/game/start-round`

Inicia una ronda seleccionando aleatoriamente un impostor y asignando palabras.

**Body:**
```json
{
  "game_id": "uuid-de-la-partida",
  "word": "PIZZA"
}
```

**Response:**
```json
{
  "message": "Ronda iniciada",
  "game_id": "uuid-de-la-partida",
  "players_count": 5
}
```

### 4. Obtener Palabra del Jugador
**POST** `/game/get-word`

Obtiene la palabra asignada a un jugador específico.

**Body:**
```json
{
  "game_id": "uuid-de-la-partida",
  "player_id": "uuid-del-jugador"
}
```

**Response:**
```json
{
  "player_id": "uuid-del-jugador",
  "player_name": "Carlos",
  "word": "PIZZA",
  "is_impostor": false
}
```

O si es el impostor:
```json
{
  "player_id": "uuid-del-jugador",
  "player_name": "Maria",
  "word": "IMPOSTOR",
  "is_impostor": true
}
```

### 5. Obtener Estado de Partida
**GET** `/game/{game_id}`

Obtiene el estado actual de una partida (sin revelar palabras ni impostores).

### 6. Eliminar Partida
**DELETE** `/game/{game_id}`

Elimina una partida.

## Documentación Interactiva

FastAPI genera documentación automática:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Flujo del Juego

1. Un jugador crea una partida con `POST /game/create`
2. Otros jugadores se unen con `POST /game/join`
3. Cuando todos estén listos, se inicia la ronda con `POST /game/start-round` (especificando la palabra)
4. Cada jugador consulta su palabra con `POST /game/get-word`
5. El impostor recibirá "IMPOSTOR" y los demás recibirán la palabra real

## Despliegue en Vercel con MongoDB Atlas

### 1. Configurar MongoDB Atlas (GRATIS)

1. Crea una cuenta en [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Crea un cluster gratuito (M0 Sandbox - 512MB)
3. Ve a "Database Access" y crea un usuario con contraseña
4. Ve a "Network Access" y agrega `0.0.0.0/0` (permitir acceso desde cualquier IP)
5. Haz clic en "Connect" → "Connect your application"
6. Copia tu connection string (algo como: `mongodb+srv://username:password@cluster.mongodb.net/`)

### 2. Desplegar en Vercel

1. Instala Vercel CLI (opcional):
```bash
npm i -g vercel
```

2. Sube tu código a GitHub

3. Importa el proyecto en [Vercel](https://vercel.com):
   - Ve a vercel.com/new
   - Selecciona tu repositorio
   - Configura las variables de entorno:
     - `MONGODB_URL`: Tu connection string de MongoDB Atlas
     - `DATABASE_NAME`: `impostor_game`

4. Despliega:
```bash
vercel --prod
```

O simplemente haz push a GitHub y Vercel desplegará automáticamente.

### Variables de Entorno

Crea un archivo `.env` local (ya está en .gitignore):
```bash
# MongoDB
MONGODB_URL=mongodb+srv://tu-usuario:tu-password@cluster.mongodb.net/?retryWrites=true&w=majority
DATABASE_NAME=impostor_game
```

## Notas

- Los datos se almacenan en **MongoDB Atlas** (plan gratuito: 512MB)
- Se requieren mínimo 3 jugadores para iniciar una ronda
- Los nombres de jugadores deben ser únicos dentro de una partida
- Vercel tiene un límite de 10 segundos para funciones serverless
- MongoDB Atlas es gratuito hasta 512MB de almacenamiento
