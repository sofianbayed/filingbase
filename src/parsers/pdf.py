import base64
from src.parsers.base import BaseDocumentParser
from src.models.documents import PdfDocument
from typing import Union

class PdfDocumentParser(BaseDocumentParser):

    def __init__(self):
        super().__init__()

    async def parse(self, content: Union[str, bytes]) -> PdfDocument:
        content = await self._get_content(content)
        content_base64 = await self._encode_pdf(content)

    @staticmethod
    async def _encode_pdf(content: bytes) -> str:
        return base64.b64encode(content).decode('utf-8')


url = "https://s204.q4cdn.com/645488518/files/doc_financials/2025/q4/FY2025-4th-Quarter-Earnings-Release.pdf"