from pydantic import BaseModel
from typing import Optional, Dict, List
from enum import Enum


class GameStatus(str, Enum):
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"


class Player(BaseModel):
    player_id: str
    name: str
    phone_number: Optional[str] = None  # Formato: +52XXXXXXXXXX
    word: Optional[str] = None
    is_impostor: bool = False


class CreateGameRequest(BaseModel):
    player_name: str
    phone_number: Optional[str] = None  # Formato: +52XXXXXXXXXX
    max_players: int = 8


class JoinGameRequest(BaseModel):
    player_name: str
    phone_number: Optional[str] = None  # Formato: +52XXXXXXXXXX
    game_id: str


class StartRoundRequest(BaseModel):
    game_id: str
    word: str


class GetWordRequest(BaseModel):
    game_id: str
    player_id: str


class GameResponse(BaseModel):
    game_id: str
    status: GameStatus
    players: List[Player]
    max_players: int
    current_word: Optional[str] = None


class PlayerWordResponse(BaseModel):
    player_id: str
    player_name: str
    word: str
    is_impostor: bool
