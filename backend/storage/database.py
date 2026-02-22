import datetime as dt
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel, Session, create_engine

from backend.config import settings


class Round(SQLModel, table=True):
    __tablename__ = "rounds"

    id: Optional[int] = Field(default=None, primary_key=True)
    telegram_user_id: str = ""
    date: dt.date = Field(default_factory=dt.date.today)
    course_name: Optional[str] = None
    is_seed: bool = False
    created_at: dt.datetime = Field(
        default_factory=lambda: dt.datetime.now(dt.timezone.utc)
    )

    holes: list["Hole"] = Relationship(back_populates="round")


class Hole(SQLModel, table=True):
    __tablename__ = "holes"

    id: Optional[int] = Field(default=None, primary_key=True)
    round_id: int = Field(foreign_key="rounds.id")
    hole_number: int
    gir: bool = False
    putts_taken: int = 0

    round: Optional[Round] = Relationship(back_populates="holes")
    putts: list["Putt"] = Relationship(back_populates="hole")


class Putt(SQLModel, table=True):
    __tablename__ = "putts"

    id: Optional[int] = Field(default=None, primary_key=True)
    hole_id: int = Field(foreign_key="holes.id")
    putt_number: int
    distance: str  # "Gimmie", "3ft", "10ft", etc.

    hole: Optional[Hole] = Relationship(back_populates="putts")


engine = create_engine(settings.database_url, echo=False)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    return Session(engine)
