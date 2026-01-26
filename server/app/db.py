from sqlmodel import create_engine, Session
from app.settings import settings

connect_args = (
    {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
)
engine = create_engine(settings.DATABASE_URL, echo=True, connect_args=connect_args)

"""
def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)
"""


def get_session():
    with Session(engine) as session:
        try:
            yield session
            if session.new or session.dirty or session.deleted:
                session.commit()
        except:
            session.rollback()
            raise
