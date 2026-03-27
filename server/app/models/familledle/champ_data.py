from sqlmodel import SQLModel, Field
from sqlalchemy import Column, text
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
    intension: int = Field(default=0, ge=0)

    vote: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False),
    )
    regime: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False),
    )
    pilosite: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False),
    )

    genre: str | None = Field(default=None)
    ressource: str | None = Field(default=None)
    portee: str | None = Field(default=None)
    annee_sortie: str | None = Field(default=None)

    role: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False, server_default=text("'[]'")),
    )
    espece: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False, server_default=text("'[]'")),
    )
    region: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False, server_default=text("'[]'")),
    )

    icon_url: str
    mean_hex: str
    mean_hue: int
