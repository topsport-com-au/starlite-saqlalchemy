from datetime import datetime

from pydantic import BaseModel as BaseModel
from pydantic import Field


class Base(BaseModel):
    """
    Base schema model for input deserialization and validation, and output serialization.

    Attributes
    ----------
    created : datetime
        Date/time of instance creation. Read-only attribute.
    updated: datetime
        Date/time of last instance update. Read-only attribute.
    """

    class Config:
        extra = "ignore"
        arbitrary_types_allowed = True
        orm_mode = True

    created: datetime = Field(default_factory=datetime.utcnow)
    updated: datetime = Field(default_factory=datetime.utcnow)
