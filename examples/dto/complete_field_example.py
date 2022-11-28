from __future__ import annotations

from pydantic import Field, constr
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from starlite_saqlalchemy import dto


def check_email(email: str) -> str:
    """Validate an email."""
    if "@" not in email:
        raise ValueError("Invalid email!")
    return email


class Base(DeclarativeBase):
    """Our ORM base class."""


class Thing(Base):
    """Something in our domain."""

    __tablename__ = "things"
    # demonstrates marking a field as "read-only" and overriding the generated pydantic `FieldInfo`
    # for the DTO field.
    id = mapped_column(
        primary_key=True, info=dto.field("read-only", pydantic_field=Field(alias="identifier"))
    )
    # demonstrates overriding the type assigned to the field in generated DTO
    always_upper: Mapped[str] = mapped_column(info=dto.field(pydantic_type=constr(to_upper=True)))
    # demonstrates setting a field as "private"
    private: Mapped[str] = mapped_column(info=dto.field("private"))
    # demonstrates setting a validator for the field
    email: Mapped[str] = mapped_column(info=dto.field(validators=[check_email]))
