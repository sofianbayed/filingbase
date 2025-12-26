import os
import io
import json
import hashlib
import asyncio
import asyncio.tasks
asyncio.create_task = asyncio.tasks.create_task
import pandas as pd
from src.models.documents import *
from src.loaders.base import BaseDocumentLoader
from dotenv import load_dotenv
from mistralai import Mistral, OCRResponse
from pydantic import BaseModel
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage

load_dotenv()

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

TABLE_DESCRIPTION_PROMPT = """
Analyze this table and provide a brief, informative caption (1-2 sentences) that describes:
1. What type of data the table contains
2. What periods or categories are covered
3. Any units or currencies used

Do not include specific numerical values in the caption.

Table (markdown format):
{table_markdown}

Surrounding context:
{context}

Respond with only the caption, no preamble.
"""


class TableDescription(BaseModel):
    """Schema for the table description"""
    description: str


class MistralDocumentLoader(BaseDocumentLoader):

    def __init__(
        self,
        file_path: str,
        describe_tables: bool = True,
        description_model: str = "openai:gpt-5-mini",
        max_concurrent_descriptions: int = 5,
    ):
        super().__init__()
        self.file_path = file_path
        self.describe_tables = describe_tables
        self.mistral = Mistral(api_key=MISTRAL_API_KEY)
        self.llm = init_chat_model(model=description_model)
        self._semaphore = asyncio.Semaphore(max_concurrent_descriptions)

    async def load(self) -> Document:
        if not self._is_url(self.file_path):
            raise ValueError("MistralDocumentLoader only supports URL file paths.")

        url_hash = hashlib.md5(self.file_path.encode()).hexdigest()
        cache_path = f"caches/mistral_ocr_{url_hash}.json"
        if os.path.exists(cache_path):
            with open(cache_path, "r", encoding="utf-8") as f:
                cached_data = json.load(f)
            ocr_response = OCRResponse.model_validate(cached_data)
            print("Loaded OCR response from cache.")
        else:
            ocr_response = await self.mistral.ocr.process_async(
                model="mistral-ocr-latest",
                document={
                    "type": "document_url",
                    "document_url": self.file_path,
                },
                table_format="html",
            )
            os.makedirs("caches", exist_ok=True)
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(ocr_response.model_dump(), f, ensure_ascii=False, indent=2)
            print("Saved OCR response to cache.")

        pages = []
        description_tasks = []

        for p in ocr_response.pages:
            page_markdown = p.markdown
            page_number = p.index + 1
            page_tables = []

            for t in p.tables:
                table_html = t.content
                table_df = pd.read_html(io.StringIO(table_html))[0]
                table_markdown = table_df.to_markdown(index=False)

                table = Table(
                    html=table_html,
                    markdown=table_markdown,
                    description=None,
                )

                page_markdown = page_markdown.replace(
                    f"[{t.id}]({t.id})", table_markdown
                )
                page_tables.append(table)

                if self.describe_tables:
                    context = self._extract_table_context(p.markdown, t.id)
                    description_tasks.append(
                        self._describe_table_with_semaphore(table, context)
                    )

            page = DocumentPage(
                markdown=page_markdown,
                number=page_number,
                tables=page_tables,
            )
            pages.append(page)

        if description_tasks:
            await asyncio.gather(*description_tasks)

        return Document(pages=pages)

    @staticmethod
    def _extract_table_context(page_markdown: str, table_id: str, window: int = 300) -> str:
        """Extract text surrounding the table placeholder for context."""
        placeholder = f"[{table_id}]({table_id})"
        pos = page_markdown.find(placeholder)

        if pos == -1:
            return page_markdown[:window]

        start = max(0, pos - window)
        end = min(len(page_markdown), pos + len(placeholder) + window)

        context = page_markdown[start:end]
        context = context.replace(placeholder, "[TABLE]")

        return context

    async def _describe_table_with_semaphore(self, table: Table, context: str) -> None:
        async with self._semaphore:
            result = await self._describe_table(table, context)
            table.description = result["description"]

    async def _describe_table(self, table: Table, context: str) -> TableDescription:
        messages = [
            HumanMessage(
                content=TABLE_DESCRIPTION_PROMPT.format(
                    table_markdown=table.markdown,
                    context=context,
                )
            )
        ]

        response = await self.llm.with_structured_output(TableDescription).ainvoke(messages)
        return response.model_dump()