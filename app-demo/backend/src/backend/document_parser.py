import base64
from enum import Enum
from typing import Dict, List

from pydantic import BaseModel, Field
import logging
import pymupdf

logger = logging.getLogger(__name__)

class BlockType(str, Enum):
    HEADER = "header"
    FOOTER = "footer"
    TITLE = "title"
    SECTION_HEADER = "section_header"
    PAGE_NUMBER = "page_number"
    LIST_ITEM = "list_item"
    FIGURE = "figure"
    TABLE = "table"
    IMAGE = "image"
    KEY_VALUE = "key_value"
    TEXT = "text"
    COMMENT = "comment"
    
def DocumentBlock(BaseModel):

    type: BlockType = Field(
        description="Sementic type classification of the document block."
    )
    page_num: int = Field(
        description="Page number of the document block."
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
        description="""
        Semantic content of the document block.
        """
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
)-> List[Dict[str, str]]:
    # extract text and images from each page of the document
    logger.info(f"Extracting data from {len(document)} pages")
    page_data = []
    for page_num in range(len(document)):
        logger.info(f"processing page {page_num + 1}")
        page = document[page_num]

        text = page.get_text()

        # extract image
        pix = page.get_pixmap(alpha=False)
        img_bytes = pix.tobytes("jpeg")
        img_base64 = base64.b64encode(img_bytes).decode("utf-8")

        page_data.append({
            "page_num": page_num + 1,
            "text": text,
            "image_base64": img_base64,
        })
        logger.info(f"extracted {len(text)} chars of text and image from page {page_num + 1}")
    logger.info(f"Completed extraction of {len(page_data)} pages")
    return page_data

        

