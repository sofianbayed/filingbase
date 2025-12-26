import os
import base64
from archive.parsers.base import BaseDocumentParser
from src.models.documents import Document
from typing import Union
from mistralai import Mistral
from dotenv import load_dotenv

load_dotenv()
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

class PdfDocumentParser(BaseDocumentParser):

    def __init__(self):
        super().__init__()
        self.mistral = Mistral(api_key=MISTRAL_API_KEY)

    async def parse(self, content: Union[str, bytes]) -> Document:
        content = await self._get_content(content)
        content_hash = self._generate_hash(content)
        content_base64 = await self._encode_pdf(content)
        return content_base64

    @staticmethod
    async def _encode_pdf(content: bytes) -> str:
        return base64.b64encode(content).decode('utf-8')


url = "https://s204.q4cdn.com/645488518/files/doc_financials/2025/q4/FY2025-4th-Quarter-Earnings-Release.pdf"
parser = PdfDocumentParser()
content_base64 = parser._get_content(url)
ocr_response = parser.mistral.ocr.process(
    model="mistral-ocr-latest",
    document={
        "type": "document_url",
        "document_url": f"data:application/pdf;base64,{content_base64}"
    },
    table_format="html"
)