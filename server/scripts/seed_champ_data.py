import json
from pathlib import Path

from sqlalchemy.dialects.postgresql import insert
from sqlmodel import Session

from app.db import engine
from app.models.tables import ChampData


data_path = (Path(__file__).resolve().parent / "../data/champ_data.json").resolve()
data = json.loads(data_path.read_text(encoding="utf-8"))

rows = [{**payload, "name": name} for name, payload in data.items()]

table = ChampData.__table__
stmt = insert(table).values(rows)
stmt = stmt.on_conflict_do_update(
    index_elements=[table.c.name],
    set_={c.name: getattr(stmt.excluded, c.name) for c in table.c if c.name != "name"},
)

with Session(engine) as session:
    session.exec(stmt)
    session.commit()
