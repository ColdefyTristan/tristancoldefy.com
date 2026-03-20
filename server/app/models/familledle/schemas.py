from sqlmodel import SQLModel
from datetime import date


class GuessIn(SQLModel):
    champion_name: str


class FamilledleAttemptDayOut(SQLModel):
    day: date
    is_finished: bool
    champions: list[str]


class FamilledleAttemptTodayWrapperOut(SQLModel):
    exists: bool
    attempt: FamilledleAttemptDayOut | None = None
