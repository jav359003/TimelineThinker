"""
Document parsing service for extracting text from PDFs and Markdown files.
"""
from typing import Optional, Tuple
import PyPDF2
import markdown
import io
from pathlib import Path


class DocumentService:
    """
    Service for extracting text from document files (PDF, Markdown).
    """

    def extract_text_from_pdf(self, file_content: bytes) -> Tuple[str, dict]:
        """
        Extract text from PDF file.

        Args:
            file_content: Binary PDF file content

        Returns:
            Tuple of (extracted_text, metadata_dict)
        """
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))

            text_parts = []
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)

            extracted_text = "\n\n".join(text_parts)

            metadata = {
                "page_count": len(pdf_reader.pages),
                "file_type": "pdf"
            }

            return extracted_text, metadata

        except Exception as e:
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")

    def extract_text_from_markdown(self, file_content: bytes) -> Tuple[str, dict]:
        """
        Extract text from Markdown file.

        Args:
            file_content: Binary markdown file content

        Returns:
            Tuple of (extracted_text, metadata_dict)
        """
        try:
            # Decode markdown content
            text = file_content.decode('utf-8')

            metadata = {
                "file_type": "markdown",
                "char_count": len(text)
            }

            # Return raw markdown text (we could convert to HTML if needed)
            return text, metadata

        except Exception as e:
            raise ValueError(f"Failed to extract text from Markdown: {str(e)}")

    def extract_text_from_file(
        self,
        file_content: bytes,
        filename: str
    ) -> Tuple[str, dict]:
        """
        Extract text from file based on extension.

        Args:
            file_content: Binary file content
            filename: Original filename (used to determine type)

        Returns:
            Tuple of (extracted_text, metadata_dict)

        Raises:
            ValueError: If file type is not supported
        """
        file_extension = Path(filename).suffix.lower()

        if file_extension == '.pdf':
            return self.extract_text_from_pdf(file_content)
        elif file_extension in ['.md', '.markdown']:
            return self.extract_text_from_markdown(file_content)
        elif file_extension == '.txt':
            # Plain text
            text = file_content.decode('utf-8')
            metadata = {"file_type": "text"}
            return text, metadata
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")


def get_document_service() -> DocumentService:
    """
    Get document service instance.

    Returns:
        DocumentService instance
    """
    return DocumentService()
