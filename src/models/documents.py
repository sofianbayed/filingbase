import uuid
from pydantic import BaseModel, ConfigDict
from typing import Union, List

class DocumentPage(BaseModel):
    id: Union[str, uuid.UUID] | None = None
    text: str | None = None
    number: int

class Document(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    id: Union[str, uuid.UUID] | None = None
    title: str

class PdfDocument(Document):
    pages: List[DocumentPage] | None = None

