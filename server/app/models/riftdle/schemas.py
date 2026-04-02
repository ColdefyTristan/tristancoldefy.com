from enum import Enum

from sqlmodel import SQLModel
from datetime import date


class ClueType(str, Enum):
    date = "date"
    genre = "genre"
    espece = "espece"
    region = "region"
    ressource = "ressource"
    position = "position"


class GuessIn(SQLModel):
    champion_name: str


class ClueIn(SQLModel):
    clue: ClueType


class RiftdleAttemptDayOut(SQLModel):
    day: date
    is_finished: bool
    champions: list[str]
    clues: list[str]
    clue_points: int


class RiftdleAttemptTodayWrapperOut(SQLModel):
    exists: bool
    attempt: RiftdleAttemptDayOut | None = None
