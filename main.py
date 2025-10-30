from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uuid
import random
from typing import Dict
from models import (
    Player,
    GameStatus,
    CreateGameRequest,
    JoinGameRequest,
    StartRoundRequest,
    GetWordRequest,
    GameResponse,
    PlayerWordResponse
)
from database import connect_to_mongo, close_mongo_connection, get_database

app = FastAPI(title="Impostor Game API", version="1.0.0")

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
    db = get_database()
    game_id = str(uuid.uuid4())
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
    
    await db.games.insert_one(game)
    
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
    db = get_database()
    game = await db.games.find_one({"game_id": request.game_id})
    
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
    
    # Actualizar en la base de datos
    await db.games.update_one(
        {"game_id": request.game_id},
        {"$push": {"players": player.model_dump()}}
    )
    
    # Obtener partida actualizada
    game = await db.games.find_one({"game_id": request.game_id})
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
    """
    db = get_database()
    game = await db.games.find_one({"game_id": request.game_id})
    
    if not game:
        raise HTTPException(status_code=404, detail="Partida no encontrada")
    
    if len(game["players"]) < 3:
        raise HTTPException(status_code=400, detail="Se necesitan al menos 3 jugadores")
    
    # Seleccionar impostor aleatoriamente
    impostor = random.choice(game["players"])
    impostor_id = impostor["player_id"]
    
    # Asignar palabras a los jugadores
    updated_players = []
    for player in game["players"]:
        if player["player_id"] == impostor_id:
            player["word"] = "IMPOSTOR"
            player["is_impostor"] = True
        else:
            player["word"] = request.word
            player["is_impostor"] = False
        updated_players.append(player)
    
    # Actualizar en la base de datos
    await db.games.update_one(
        {"game_id": request.game_id},
        {
            "$set": {
                "status": GameStatus.IN_PROGRESS,
                "current_word": request.word,
                "impostor_id": impostor_id,
                "players": updated_players
            }
        }
    )
    
    return {
        "message": "Ronda iniciada",
        "game_id": request.game_id,
        "players_count": len(updated_players)
    }


@app.post("/game/get-word", response_model=PlayerWordResponse)
async def get_word(request: GetWordRequest):
    """
    Obtiene la palabra asignada a un jugador específico.
    """
    db = get_database()
    game = await db.games.find_one({"game_id": request.game_id})
    
    if not game:
        raise HTTPException(status_code=404, detail="Partida no encontrada")
    
    if game["status"] != GameStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="La ronda no ha comenzado")
    
    # Buscar el jugador
    player = next((p for p in game["players"] if p["player_id"] == request.player_id), None)
    
    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    
    return PlayerWordResponse(
        player_id=player["player_id"],
        player_name=player["name"],
        word=player["word"],
        is_impostor=player["is_impostor"]
    )


@app.get("/game/{game_id}", response_model=GameResponse)
async def get_game(game_id: str):
    """
    Obtiene el estado actual de una partida.
    """
    db = get_database()
    game = await db.games.find_one({"game_id": game_id})
    
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
    db = get_database()
    result = await db.games.delete_one({"game_id": game_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Partida no encontrada")
    
    return {"message": "Partida eliminada", "game_id": game_id}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
