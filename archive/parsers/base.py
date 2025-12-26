import os
import hashlib
from urllib.parse import urlparse
from pathlib import Path
from abc import ABC, abstractmethod
from typing import List, Union
from src.models.documents import Document

class ParserError(Exception):
    pass

class InvalidContentError(Exception):
    pass

class BaseDocumentParser(ABC):

    @abstractmethod
    async def parse(self, content: Union[str, bytes]) -> Document:
        pass

    async def _get_content(self, content: Union[str, bytes]) -> bytes:
        if isinstance(content, bytes):
            return content

        if isinstance(content, str):
            if self._is_url(content):
                return await self._fetch_from_url(content)

            # Otherwise treat as file path
            return await self._read_from_path(content)

        raise InvalidContentError(f"Unsupported content type: {type(content)}")

    @staticmethod
    async def _read_from_path(content: str) -> bytes:
        path = Path(content)
        if not path.exists():
            raise FileNotFoundError(f"The file at {content} does not exist.")
        with open(path, 'rb') as file:
            return file.read()


    @staticmethod
    async def _fetch_from_url(url: str) -> bytes:
        import aiohttp

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=30) as response:
                    if response.status != 200:
                        raise ParserError(f"HTTP {response.status} fetching {url}")

                    content = await response.read()

                    return content
        except aiohttp.ClientError as e:
            raise ParserError(f"Network error fetching {url}: {e}")

    @staticmethod
    def _is_url(content: str) -> bool:
        try:
            result = urlparse(content)
            return result.scheme in ('http', 'https')
        except Exception:
            return False

    @staticmethod
    def _generate_hash(content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()
