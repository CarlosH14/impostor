from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uuid
import random
import string
from typing import Dict
from models import (
    Player,
    GameStatus,
    CreateGameRequest,
    JoinGameRequest,
    StartRoundRequest,
    GetWordRequest,
    GameResponse,
    PlayerWordResponse,
    CreateWordRequest,
    WordResponse
)
from database import connect_to_mongo, close_mongo_connection, get_database

app = FastAPI(title="Impostor Game API", version="1.0.0")

# Almacenamiento en memoria (fallback cuando MongoDB no está disponible)
games_memory: Dict[str, dict] = {}


def generate_game_code(length: int = 6) -> str:
    """
    Genera un código de partida corto y fácil de compartir.
    Usa solo letras mayúsculas y números, evitando caracteres ambiguos (0, O, 1, I).
    """
    chars = string.ascii_uppercase + string.digits
    # Eliminar caracteres ambiguos
    chars = chars.replace('0', '').replace('O', '').replace('1', '').replace('I', '')
    return ''.join(random.choices(chars, k=length))

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Conectar a MongoDB al iniciar la aplicación"""
    await connect_to_mongo()


@app.on_event("shutdown")
async def shutdown_event():
    """Cerrar conexión a MongoDB al cerrar la aplicación"""
    await close_mongo_connection()


@app.get("/")
async def root():
    return {"message": "Impostor Game API", "status": "running"}


@app.post("/game/create", response_model=GameResponse)
async def create_game(request: CreateGameRequest):
    """
    Crea una nueva partida y añade al primer jugador (host).
    """
    db = await get_database()
    
    # Generar código único de partida
    game_id = generate_game_code()
    
    # Verificar que el código no exista (aunque es muy improbable)
    if db:
        while await db.games.find_one({"game_id": game_id}):
            game_id = generate_game_code()
    else:
        while game_id in games_memory:
            game_id = generate_game_code()
    
    player_id = str(uuid.uuid4())
    
    player = Player(
        player_id=player_id,
        name=request.player_name,
        is_impostor=False
    )
    
    game = {
        "game_id": game_id,
        "status": GameStatus.WAITING,
        "players": [player.model_dump()],
        "max_players": request.max_players,
        "current_word": None,
        "impostor_id": None
    }
    
    # Usar MongoDB si está disponible, sino memoria
    if db:
        await db.games.insert_one(game)
    else:
        games_memory[game_id] = game
    
    return GameResponse(
        game_id=game_id,
        status=GameStatus.WAITING,
        players=[player],
        max_players=request.max_players
    )


@app.post("/game/join", response_model=GameResponse)
async def join_game(request: JoinGameRequest):
    """
    Permite a un jugador unirse a una partida existente.
    """
    db = await get_database()
    
    # Buscar en MongoDB o memoria
    if db:
        game = await db.games.find_one({"game_id": request.game_id})
    else:
        game = games_memory.get(request.game_id)
    
    if not game:
        raise HTTPException(status_code=404, detail="Partida no encontrada")
    
    if game["status"] != GameStatus.WAITING:
        raise HTTPException(status_code=400, detail="La partida ya ha comenzado")
    
    if len(game["players"]) >= game["max_players"]:
        raise HTTPException(status_code=400, detail="La partida está llena")
    
    # Verificar si el nombre ya existe
    if any(p["name"] == request.player_name for p in game["players"]):
        raise HTTPException(status_code=400, detail="Ese nombre ya está en uso")
    
    player_id = str(uuid.uuid4())
    player = Player(
        player_id=player_id,
        name=request.player_name,
        is_impostor=False
    )
    
    # Actualizar en la base de datos o memoria
    if db:
        await db.games.update_one(
            {"game_id": request.game_id},
            {"$push": {"players": player.model_dump()}}
        )
        game = await db.games.find_one({"game_id": request.game_id})
    else:
        game["players"].append(player.model_dump())
        games_memory[request.game_id] = game
    
    players = [Player(**p) for p in game["players"]]
    
    return GameResponse(
        game_id=game["game_id"],
        status=game["status"],
        players=players,
        max_players=game["max_players"]
    )


@app.post("/game/start-round")
async def start_round(request: StartRoundRequest):
    """
    Inicia una nueva ronda seleccionando aleatoriamente un impostor
    y asignando palabras a todos los jugadores.
    Siempre usa una palabra aleatoria de la base de datos.
    """
    db = await get_database()
    
    # Buscar en MongoDB o memoria
    if db:
        game = await db.games.find_one({"game_id": request.game_id})
    else:
        game = games_memory.get(request.game_id)
    
    if not game:
        raise HTTPException(status_code=404, detail="Partida no encontrada")
    
    if len(game["players"]) < 3:
        raise HTTPException(status_code=400, detail="Se necesitan al menos 3 jugadores")
    
    # Obtener palabra aleatoria de la base de datos
    if not db:
        raise HTTPException(status_code=503, detail="Base de datos no disponible")
    
    pipeline = [{"$sample": {"size": 1}}]
    words = await db.words.aggregate(pipeline).to_list(length=1)
    
    if not words:
        raise HTTPException(status_code=404, detail="No hay palabras disponibles en la base de datos. Por favor agrega palabras primero.")
    
    word_data = words[0]
    word = word_data["word"]
    hint = word_data["hint"]
    
    # Seleccionar impostor aleatoriamente
    impostor = random.choice(game["players"])
    impostor_id = impostor["player_id"]
    
    # Asignar palabras a los jugadores
    updated_players = []
    
    for player in game["players"]:
        if player["player_id"] == impostor_id:
            player["word"] = "IMPOSTOR"
            player["is_impostor"] = True
            player["hint"] = hint  # Guardar pista para el impostor
        else:
            player["word"] = word
            player["is_impostor"] = False
            player["hint"] = None
        updated_players.append(player)
    
    # Actualizar en la base de datos o memoria
    if db:
        await db.games.update_one(
            {"game_id": request.game_id},
            {
                "$set": {
                    "status": GameStatus.IN_PROGRESS,
                    "current_word": word,
                    "impostor_id": impostor_id,
                    "players": updated_players,
                    "hint": hint
                }
            }
        )
    else:
        game["status"] = GameStatus.IN_PROGRESS
        game["current_word"] = word
        game["impostor_id"] = impostor_id
        game["players"] = updated_players
        game["hint"] = hint
        games_memory[request.game_id] = game
    
    return {
        "message": "Ronda iniciada",
        "game_id": request.game_id,
        "players_count": len(updated_players),
        "word_used": word,
        "has_hint": True
    }


@app.post("/game/get-word", response_model=PlayerWordResponse)
async def get_word(request: GetWordRequest):
    """
    Obtiene la palabra asignada a un jugador específico.
    Si es impostor, también recibe la pista.
    """
    db = await get_database()
    
    # Buscar en MongoDB o memoria
    if db:
        game = await db.games.find_one({"game_id": request.game_id})
    else:
        game = games_memory.get(request.game_id)
    
    if not game:
        raise HTTPException(status_code=404, detail="Partida no encontrada")
    
    if game["status"] != GameStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="La ronda no ha comenzado")
    
    # Buscar el jugador
    player = next((p for p in game["players"] if p["player_id"] == request.player_id), None)
    
    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    
    # Incluir pista solo si es impostor
    hint = player.get("hint") if player["is_impostor"] else None
    
    return PlayerWordResponse(
        player_id=player["player_id"],
        player_name=player["name"],
        word=player["word"],
        is_impostor=player["is_impostor"],
        hint=hint
    )


@app.get("/game/{game_id}", response_model=GameResponse)
async def get_game(game_id: str):
    """
    Obtiene el estado actual de una partida.
    """
    db = await get_database()
    
    # Buscar en MongoDB o memoria
    if db:
        game = await db.games.find_one({"game_id": game_id})
    else:
        game = games_memory.get(game_id)
    
    if not game:
        raise HTTPException(status_code=404, detail="Partida no encontrada")
    
    # No revelar información sensible (palabras e impostores)
    safe_players = [
        Player(
            player_id=p["player_id"],
            name=p["name"],
            is_impostor=False
        ) for p in game["players"]
    ]
    
    return GameResponse(
        game_id=game["game_id"],
        status=game["status"],
        players=safe_players,
        max_players=game["max_players"]
    )


@app.delete("/game/{game_id}")
async def delete_game(game_id: str):
    """
    Elimina una partida.
    """
    db = await get_database()
    
    # Eliminar de MongoDB o memoria
    if db:
        result = await db.games.delete_one({"game_id": game_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Partida no encontrada")
    else:
        if game_id not in games_memory:
            raise HTTPException(status_code=404, detail="Partida no encontrada")
        del games_memory[game_id]
    
    return {"message": "Partida eliminada", "game_id": game_id}


# ============= ENDPOINTS DE PALABRAS =============

@app.post("/words", response_model=WordResponse)
async def create_word(request: CreateWordRequest):
    """
    Crea una nueva palabra en la base de datos.
    """
    db = await get_database()
    
    if not db:
        raise HTTPException(status_code=503, detail="Base de datos no disponible")
    
    word_id = str(uuid.uuid4())
    word_data = {
        "word_id": word_id,
        "word": request.word,
        "hint": request.hint,
        "category": request.category,
        "difficulty": request.difficulty or "medium"
    }
    
    await db.words.insert_one(word_data)
    
    return WordResponse(**word_data)


@app.get("/words", response_model=list[WordResponse])
async def get_all_words():
    """
    Obtiene todas las palabras disponibles.
    """
    db = await get_database()
    
    if not db:
        raise HTTPException(status_code=503, detail="Base de datos no disponible")
    
    words = await db.words.find().to_list(length=1000)
    
    return [WordResponse(**{k: v for k, v in w.items() if k != "_id"}) for w in words]


@app.get("/words/random", response_model=WordResponse)
async def get_random_word():
    """
    Obtiene una palabra aleatoria de la base de datos.
    """
    db = await get_database()
    
    if not db:
        raise HTTPException(status_code=503, detail="Base de datos no disponible")
    
    # Obtener una palabra aleatoria usando agregación
    pipeline = [{"$sample": {"size": 1}}]
    words = await db.words.aggregate(pipeline).to_list(length=1)
    
    if not words:
        raise HTTPException(status_code=404, detail="No hay palabras disponibles")
    
    word = words[0]
    return WordResponse(**{k: v for k, v in word.items() if k != "_id"})


@app.delete("/words/{word_id}")
async def delete_word(word_id: str):
    """
    Elimina una palabra de la base de datos.
    """
    db = await get_database()
    
    if not db:
        raise HTTPException(status_code=503, detail="Base de datos no disponible")
    
    result = await db.words.delete_one({"word_id": word_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Palabra no encontrada")
    
    return {"message": "Palabra eliminada", "word_id": word_id}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
