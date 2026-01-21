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
    word: Optional[str] = None
    is_impostor: bool = False


class CreateGameRequest(BaseModel):
    player_name: str
    max_players: int = 8


class JoinGameRequest(BaseModel):
    player_name: str
    game_id: str


class StartRoundRequest(BaseModel):
    game_id: str


class GetWordRequest(BaseModel):
    game_id: str
    player_id: str


class GameResponse(BaseModel):
    game_id: str
    status: GameStatus
    players: List[Player]
    max_players: int
    current_word: Optional[str] = None
    round_number: int = 0


class PlayerWordResponse(BaseModel):
    player_id: str
    player_name: str
    word: str
    is_impostor: bool
    hint: Optional[str] = None  # Pista para el impostor


class Word(BaseModel):
    word_id: Optional[str] = None
    word: str
    hint: str  # Pista para ayudar al impostor
    category: Optional[str] = None
    difficulty: Optional[str] = "medium"  # easy, medium, hard


class CreateWordRequest(BaseModel):
    word: str
    hint: str
    category: Optional[str] = None
    difficulty: Optional[str] = "medium"


class WordResponse(BaseModel):
    word_id: str
    word: str
    hint: str
    category: Optional[str] = None
    difficulty: str
