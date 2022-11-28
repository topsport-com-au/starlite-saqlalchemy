from __future__ import annotations

from datetime import date, datetime
from typing import Annotated

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from starlite_saqlalchemy import dto


class Base(DeclarativeBase):
    """ORM base class.

    Using the dto.field() function, we've annotated that these columns
    are read-only.
    """

    id: Mapped[int] = mapped_column(primary_key=True, info=dto.field("read-only"))
    created: Mapped[datetime] = mapped_column(info=dto.field("read-only"))
    updated: Mapped[datetime] = mapped_column(info=dto.field("read-only"))


class Author(Base):
    """Domain object."""

    __tablename__ = "authors"
    name: Mapped[str]
    dob: Mapped[date]


WriteDTO = dto.FromMapped[Annotated[Author, "write"]]

# now when we inspect our fields, we can see that our "write" purposed
# DTO does not include any of the fields that we marked as "read-only"
# fields.
print(WriteDTO.__fields__)

# {
#     "name": ModelField(name="name", type=str, required=True),
#     "dob": ModelField(name="dob", type=date, required=True),
# }
