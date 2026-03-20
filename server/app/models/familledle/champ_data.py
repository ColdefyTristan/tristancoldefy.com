from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB


class ChampData(SQLModel, table=True):
    __tablename__ = "champ_data"

    name: str = Field(primary_key=True, index=True)

    skin_number: int = Field(default=0, ge=0)

    family_mastery: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False),
    )

    mobility: int = Field(default=0, ge=0)
    randomness: int = Field(default=0, ge=0)

    cc_quantity: int = Field(default=0, ge=0)

    icon_url: str
    mean_hex: str
    mean_hue: int

    is_champ_of_the_day: bool = False
