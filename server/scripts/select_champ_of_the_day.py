from sqlmodel import Session, select
from sqlalchemy import func, update

from app.db import engine
from app.models.tables import ChampData


def select_champ_of_the_day():

    with Session(engine) as session:
        # 1) unset current champ of the day (if any)
        session.exec(
            update(ChampData)
            .where(ChampData.is_champ_of_the_day == True)  # noqa: E712
            .values(is_champ_of_the_day=False)
        )

        # 2) pick a random champ
        champ = session.exec(
            select(ChampData).order_by(func.random()).limit(1)
        ).one_or_none()

        if champ is None:
            raise RuntimeError("No ChampData rows found")

        # 3) set it as champ of the day
        session.exec(
            update(ChampData)
            .where(ChampData.name == champ.name)
            .values(is_champ_of_the_day=True)
        )

        session.commit()
        print(f"champ_of_the_day = {champ.name}")


if __name__ == "__main__":
    select_champ_of_the_day()
