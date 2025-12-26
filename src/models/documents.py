import uuid
from pydantic import BaseModel, ConfigDict
from typing import Union, List

class Table(BaseModel):
    id: Union[str, uuid.UUID] | None = None
    html: str
    markdown: str
    description: str | None = None

class DocumentPage(BaseModel):
    id: Union[str, uuid.UUID] | None = None
    markdown: str
    number: int
    tables: List[Table] = []

class Document(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    id: Union[str, uuid.UUID] | None = None
    title: str | None = None
    pages: List[DocumentPage] = []
