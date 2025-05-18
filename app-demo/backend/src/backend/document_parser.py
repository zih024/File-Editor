import asyncio
import base64
from enum import Enum
import os
from typing import Dict, List, Literal

from openai import AsyncOpenAI

import pymupdf
from pydantic import BaseModel, Field

import logging

logger = logging.getLogger(__name__)


class BlockType(str, Enum):
    """
    Classification of document block types.

    Categorizes different structural and content elements found in documents for
    more accurate parsing, indexing, and retrieval.
    """

    HEADER = "Header"
    FOOTER = "Footer"
    TITLE = "Title"
    SECTION_HEADER = "Section Header"
    PAGE_NUMBER = "Page Number"
    LIST_ITEM = "List Item"
    FIGURE = "Figure"
    TABLE = "Table"
    IMAGE = "Image"
    KEY_VALUE = "Key Value"
    TEXT = "Text"
    COMMENT = "Comment"


class DocumentBlock(BaseModel):
    """
    A block of content extracted from a document. Blocks are single units of
    information in a document. Each distinct element (paragraphs, headers,
    images, titles, tables) is typically a separate block.
    """

    type: BlockType = Field(
        description="Semantic type classification of the document block."
    )
    page_num: int = Field(
        description="Page number (1-indexed) where the block is located."
    )
    content: str = Field(
        description="""
        Raw content of the block, may be empty.
        - Leave empty for images.
        - For tables and figures, use a HTML table to represent the underlying
        data. And use `rowspan` and `colspan` attributes for merged cells. For
        example:

        ```
        <table>
            <tr>
                <th>Header 1</th>
                <th>Header 2</th>
            </tr>
            <tr>
                <td>Data 1</td>
                <td>Data 2</td>
            </tr>
        </table>
        ```
        """
    )
    semantic_content: str = Field(
        description="""Semantic in-detail description of the content or data in
        the block."""
    )


class AIDocumentBlockSchema(BaseModel):
    """
    A block of content extracted from a document. Blocks are single units of
    information in a document. Each distinct element (paragraphs, headers,
    images, titles, tables) is typically a separate block.
    """

    type: BlockType = Field(
        description="Semantic type classification of the document block."
    )
    content: str = Field(
        description="""
        Raw content of the block, may be empty.

        - For tables and figures, use a HTML table to represent the underlying
        data. And use `rowspan` and `colspan` attributes for merged cells. For
        example:

        ```
        <table>
            <tr>
                <th>Header 1</th>
                <th>Header 2</th>
            </tr>
            <tr>
                <td>Data 1</td>
                <td>Data 2</td>
            </tr>
        </table>
        ```
        """
    )
    semantic_content: str = Field(
        description="""Semantic in-detail description of the content or data in
        the block."""
    )


class AIDocumentParseResponseSchema(BaseModel):
    """
    Response from OpenAI for a single document block.
    """

    blocks: List[AIDocumentBlockSchema] = Field(
        description="List of document blocks"
    )


class DocumentChunk(BaseModel):
    """
    A chunk of content from a document. Chunks are composed of one or more
    blocks. Possible chunking strategies:
    - Variable chunking (number of characters)
    - Section Chunking (chunking by section)
    - Page Chunking (chunking by page)
    - Block Chunking (each block is a chunk)
    """

    content: str = Field(
        description="Full textual content of the chunk for display and processing"
    )
    embed: str = Field(
        description="Content optimized for embedding and semantic retrieval"
    )
    blocks: List[DocumentBlock] = Field(
        description="Constituent document blocks that compose this chunk"
    )


class ParsedDocument(BaseModel):
    """
    A fully parsed document broken into retrievable chunks.

    Represents the complete extraction of structured content from a document,
    organized into logical chunks for efficient storage, retrieval, and analysis.
    """

    chunks: List[DocumentChunk] = Field(
        description="Organized collection of document chunks"
    )


async def load_pdf(bytes: bytes) -> ParsedDocument:
    """
    Load a PDF document from bytes.

    Converts raw binary PDF data into a structured document object that can
    be parsed for content extraction.

    Args:
        bytes: Raw binary data of the PDF document

    Returns:
        A pymupdf.Document object representing the loaded document
    """
    logger.info("Loading PDF document from bytes")
    try:
        doc = pymupdf.open(stream=bytes, filetype="pdf")
        logger.info(f"Successfully loaded PDF with {len(doc)} pages")
        return doc
    except Exception as e:
        logger.error(f"Error loading PDF: {str(e)}")
        raise


async def extract_page_data(
    document: pymupdf.Document,
) -> List[Dict[str, str]]:
    """
    Extract text and images from each page of the document.

    Args:
        document: A pymupdf.Document object

    Returns:
        A list of dictionaries containing text and image for each page
    """
    logger.info(f"Extracting data from {len(document)} pages")
    page_data = []

    for page_num in range(len(document)):
        logger.info(f"Processing page {page_num + 1}")
        page = document[page_num]

        # Extract text
        text = page.get_text()

        # Extract image
        pix = page.get_pixmap(alpha=False)
        img_bytes = pix.tobytes("jpeg")
        img_base64 = base64.b64encode(img_bytes).decode("utf-8")

        page_data.append(
            {
                "page_num": page_num + 1,  # 1-indexed
                "text": text,
                "image_base64": img_base64,
            }
        )
        logger.info(
            f"Extracted {len(text)} chars of text and image from page {page_num + 1}"
        )

    logger.info(f"Completed extraction of {len(page_data)} pages")
    return page_data


async def analyze_page_with_openai(
    client: AsyncOpenAI,
    page_num: int,
    page_text: str,
    image_base64: str,
) -> List[DocumentBlock]:
    """
    Analyze a single page with OpenAI asynchronously.

    Args:
        client: AsyncOpenAI client instance
        page_num: Page number
        page_text: Text content of the page
        image_base64: Base64 encoded image data for the page

    Returns:
        List of DocumentBlock objects for the page
    """

    logger.info(f"Sending page {page_num} to OpenAI for analysis")

    # Prepare the prompt
    prompt = """
    Parse the provided PDF page data (underlying text and full-page image) and
    identify all document blocks.
    """

    messages = [
        {"role": "system", "content": prompt},
        {
            "role": "user",
            "content": f"Page {page_num} text: ```{page_text}```",
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": f"Page {page_num} image:"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_base64}",
                        "detail": "auto",
                    },
                },
            ],
        },
    ]

    page_blocks = []
    try:
        response = await client.beta.chat.completions.parse(
            model="gpt-4.1-mini-2025-04-14",
            messages=messages,
            response_format=AIDocumentParseResponseSchema,
        )

        response_message = response.choices[0].message

        if response_message.refusal:
            logger.error(
                f"OpenAI refused to parse page {page_num}: "
                f"{response_message.refusal}"
            )
            return []

        blocks_data = response_message.parsed.blocks

        logger.info(f"Received {len(blocks_data)} blocks for page {page_num}")

        for block_data in blocks_data:
            block = DocumentBlock(
                type=block_data.type,
                page_num=page_num,
                content=block_data.content,
                semantic_content=block_data.semantic_content,
            )
            logger.info(f"Page {page_num}; Block:\n{block}")
            page_blocks.append(block)

    except Exception as e:
        logger.error(f"Error analyzing page {page_num}: {str(e)}")

    return page_blocks


async def analyze_with_openai(
    page_data: List[Dict[str, str]],
    max_concurrency: int = 10,
) -> List[DocumentBlock]:
    """
    Use OpenAI's model to analyze the document and identify blocks.

    Args:
        page_data: List of dictionaries containing text and images for each page

    Returns:
        List of DocumentBlock objects
    """
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    all_blocks = []

    # Process pages in batches to control concurrency
    semaphore = asyncio.Semaphore(max_concurrency)

    async def process_page_with_semaphore(page):
        async with semaphore:
            return await analyze_page_with_openai(
                client=client,
                page_num=page["page_num"],
                page_text=page["text"],
                image_base64=page["image_base64"],
            )

    # Create tasks for all pages
    tasks = [process_page_with_semaphore(page) for page in page_data]

    # Gather results
    results = await asyncio.gather(*tasks)

    # Combine all blocks from all pages
    for page_blocks in results:
        all_blocks.extend(page_blocks)

    logger.info(
        f"Analysis complete. Identified {len(all_blocks)} blocks across all pages"
    )
    return all_blocks


async def process_page(page_num: int, page_blocks: list, client) -> DocumentChunk:
    logger.info(
        f"Creating chunk for page {page_num} with {len(page_blocks)} blocks"
    )
    # Combine all text content
    content = "\n".join(
        [block.content for block in page_blocks if block.content]
    )

    prompt = """
    Create a detailed semantic description of this page content
    optimized for vector embedding and semantic search. Include key
    concepts, entities, relationships, and main ideas. Be
    comprehensive but focused.
    """
    response = await client.chat.completions.create(
        model="gpt-4.1-mini-2025-04-14",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": content},
        ],
        temperature=0,
        max_tokens=1024,
    )

    embed_text = response.choices[0].message.content
    logger.info(f"Generated embedding text for page {page_num}")
    return DocumentChunk(
        content=content, embed=embed_text, blocks=page_blocks
    )


async def create_chunks_from_blocks(
    blocks: List[DocumentBlock],
    mode: Literal[
        "page", "block"
    ] = "page", 
) -> List[DocumentChunk]:
    """
    Organize blocks into chunks by grouping blocks from the same page and
    generating an embedding-optimized description for each page.

    Args:
        blocks: List of DocumentBlock objects
        client: AsyncOpenAI client instance

    Returns:
        List of DocumentChunk objects
    """
    logger.info(f"Creating chunks from {len(blocks)} blocks")

    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    if mode == "page":
        # Group blocks by page
        pages = {}
        for block in blocks:
            page_num = block.page_num
            if page_num not in pages:
                pages[page_num] = []
            pages[page_num].append(block)

        # Create a semaphore to limit concurrency
        semaphore = asyncio.Semaphore(10)  # Limit to 10 concurrent requests

        async def process_page_with_semaphore(page_num: int, page_blocks: list) -> DocumentChunk:
            async with semaphore:
                return await process_page(page_num, page_blocks, client)

        # Process pages in parallel with concurrency control
        tasks = [
            process_page_with_semaphore(page_num, page_blocks)
            for page_num, page_blocks in pages.items()
        ]
        chunks = await asyncio.gather(*tasks)
    else:
        chunks = [
            DocumentChunk(
                content=block.content,
                embed=block.semantic_content,
                blocks=[block],
            )
            for block in blocks
        ]

    logger.info(f"Created {len(chunks)} chunks")
    return chunks


async def parse_pdf(
    pdf_bytes: bytes,
) -> ParsedDocument:
    """
    Parse a PDF document into structured content asynchronously.

    Args:
        pdf_bytes: The raw PDF bytes to parse

    Returns:
        A ParsedDocument containing the hierarchical structure of document content
    """
    logger.info("Starting async PDF parsing process")
    try:
        # Load the document from bytes
        document = await load_pdf(pdf_bytes)

        # Extract text and images from each page
        page_data = await extract_page_data(document)

        # Use OpenAI to analyze the content and identify blocks asynchronously
        blocks = await analyze_with_openai(page_data)

        # Organize blocks into chunks
        chunks = await create_chunks_from_blocks(blocks, mode="page")

        logger.info("Async PDF parsing completed successfully")
        return ParsedDocument(chunks=chunks)
    except Exception as e:
        logger.error(f"Async PDF parsing failed: {str(e)}")
        raise
