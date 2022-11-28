from __future__ import annotations

from datetime import date, datetime
from typing import Annotated

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from starlite_saqlalchemy import dto


class Base(DeclarativeBase):
    """ORM base class.

    All SQLAlchemy ORM models must inherit from DeclarativeBase. We also
    define some common columns that we want to be present on every model
    in our domain.
    """

    id: Mapped[int] = mapped_column(primary_key=True)
    created: Mapped[datetime]
    updated: Mapped[datetime]


class Author(Base):
    """A domain model.

    In addition to the columns defined on `Base` we have "name" and
    "dob".
    """

    __tablename__ = "authors"
    name: Mapped[str]
    dob: Mapped[date]


# This creates a DTO, which is simply a Pydantic model that inherits
# from our special  `FromMapped` subclass. We call it "WriteDTO" as it
# is the model that we'll use to parse client data as they try to
# "write" to (that is, create or update) authors in our domain.
WriteDTO = dto.FromMapped[Annotated[Author, "write"]]

# we can inspect the fields that are available on the DTO
print(WriteDTO.__fields__)

# {
#     "id": ModelField(name="id", type=int, required=True),
#     "created": ModelField(name="created", type=datetime, required=True),
#     "updated": ModelField(name="updated", type=datetime, required=True),
#     "name": ModelField(name="name", type=str, required=True),
#     "dob": ModelField(name="dob", type=date, required=True),
# }
