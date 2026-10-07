from pathlib import Path


class InputProcessor:
    """
    SentinelAI Input Processor

    Responsibility:
        Extract textual content from different input sources.
        Supported:
        - Plain text
        - TXT
        - Markdown
        - PDF
        - DOCX
        - HTML
        - Source code
        - Images / OCR
    """

    # public method
    def process_text(self, text: str):
        """
        Process direct user text.
        """
        if text is None:
            raise ValueError("Input text cannot be None")
        return {
            "source_type": "text",
            "source_name": None,
            "content": text,
            "metadata": {
                "extraction_method": "direct_text",
                "extraction_status": "success",
            },
        }

    def process_file(self, file_path: str):
        """
        Detect file type and extract its content.
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        extension = path.suffix.lower()

        # PDF
        if extension == ".pdf":
            return self._process_pdf(path)

        # DOCX
        elif extension == ".docx":
            return self._process_docx(path)

        # TXT
        elif extension == ".txt":
            return self._process_text_file(path, source_type="text")

        # Markdown
        elif extension == ".md":
            return self._process_text_file(path, source_type="markdown")

        # HTML
        elif extension in [".html", ".htm"]:
            return self._process_html(path)

        # source code
        elif extension in [
            ".py",
            ".js",
            ".ts",
            ".java",
            ".cpp",
            ".c",
            ".h",
            ".cs",
            ".go",
            ".rs",
            ".php",
            ".rb",
            ".sql",
            ".json",
            ".xml",
            ".yaml",
            ".yml",
            ".sh",
            ".bat",
        ]:
            return self._process_text_file(path, source_type="source_code")

        # Image
        elif extension in [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif"]:
            return self.process_image(str(path))

        else:
            raise ValueError(f"Unsupported file format: {extension}")

    # PDF
    def _process_pdf(self, path: Path):
        """
        Extract text from PDF.

        Strategy:

        1. Try normal PDF text extraction.
        2. If meaningful text is found, use it.
        3. If PDF has little/no extractable text,
           fall back to OCR.
        """
        content = self._extract_pdf_text(path)

        if content and content.strip():
            return {
                "source_type": "pdf",
                "source_name": path.name,
                "content": content,
                "metadata": {
                    "file_extension": ".pdf",
                    "extraction_method": "pdf_text",
                    "extraction_status": "success",
                },
            }
        # OCR Fallback
        ocr_content = self._ocr_pdf(path)

        if ocr_content and ocr_content.strip():
            return {
                "source_type": "pdf",
                "source_name": path.name,
                "content": ocr_content,
                "metadata": {
                    "file_extension": ".pdf",
                    "extraction_method": "pdf_ocr",
                    "extraction_status": "success_with_ocr",
                },
            }
        return {
            "source_type": "pdf",
            "source_name": path.name,
            "content": "",
            "metadata": {
                "file_extension": ".pdf",
                "extraction_method": "pdf_text_and_ocr",
                "extraction_status": "failed",
            },
        }

    def _extract_pdf_text(self, path: Path):
        """
        Extract text from text-based PDF.

        pypdf preserves textual content including
        headers/footers when they are present in the PDF's
        text layer.

        No content cleaning is performed.
        """
        from pypdf import PdfReader

        reader = PdfReader(str(path))

        pages = []

        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text()
            if text:
                pages.append(f"\n[PAGE {page_number}]\n" + text)

        return "\n".join(pages)

    # PDF OCR fallback
    def _ocr_pdf(self, path: Path):
        """
        OCR fallback for scanned/image-based PDFs.

        Converts PDF pages to images and runs EasyOCR.

        Requires:
            pip install pdf2image easyocr

        Also requires Poppler to be installed on the system.
        """
        from pdf2image import convert_from_path
        import easyocr

        reader = easyocr.Reader(["en"], gpu=False)
        pages = convert_from_path(str(path), dpi=200)

        extracted_pages = []

        for page_number, image in enumerate(pages, start=1):
            results = reader.readtext(image, detail=0)

            page_text = "\n".join(results)

            if page_text:
                extracted_pages.append(f"\n[PAGE {page_number}]\n" + page_text)

        return "\n".join(extracted_pages)

    # DOCX
    def _process_docx(self, path: Path):
        """
        Extract:

        - document paragraphs
        - tables
        - headers
        - footers

        Nothing is intentionally removed.
        """
        from docx import Document

        document = Document(str(path))

        sections = []

        # Headers and footers

        for section_number, section in enumerate(document.sections, start=1):
            # Header
            header_text = self._extract_docx_container(section.header)

            if header_text:
                sections.append(
                    f"\n[HEADER - SECTION {section_number}]\n" + header_text
                )

            # Footer
            footer_text = self._extract_docx_container(section.footer)

            if footer_text:
                sections.append(
                    f"\n[FOOTER - SECTION {section_number}]\n" + footer_text
                )

        # Main document paragraphs
        for paragraph in document.paragraphs:
            if paragraph.text:
                sections.append(paragraph.text)

        # Tables
        for table_number, table in enumerate(document.tables, start=1):
            sections.append(f"\n[TABLE {table_number}]\n")

            for row in table.rows:
                cells = []

                for cell in row.cells:
                    cells.append(cell.text)

                sections.append(" | ".join(cells))

        content = "\n".join(sections)

        return {
            "source_type": "docx",
            "source_name": path.name,
            "content": content,
            "metadata": {
                "file_extension": ".docx",
                "extraction_method": "python_docx",
                "extraction_status": "success",
            },
        }

    def _extract_docx_container(self, container):
        """
        Extract paragraphs and tables from a DOCX
        header/footer container.
        """

        parts = []

        for paragraph in container.paragraphs:
            if paragraph.text:
                parts.append(paragraph.text)

        for table in container.tables:
            for row in table.rows:
                cells = []

                for cell in row.cells:
                    cells.append(cell.text)

                parts.append(" | ".join(cells))

        return "\n".join(parts)

    # Text/markdown/cources code
    def _process_text_file(self, path: Path, source_type: str):

        content = path.read_text(encoding="utf-8", errors="ignore")

        return {
            "source_type": source_type,
            "source_name": path.name,
            "content": content,
            "metadata": {
                "file_extension": path.suffix.lower(),
                "extraction_method": "direct_file_read",
                "extraction_status": "success",
            },
        }

    # HTML
    def _process_html(self, path: Path):
        """
        Extract visible HTML text.

        HTML tags are converted to their textual content.

        Script/style elements are excluded because they are
        executable/presentation markup rather than normal
        document text.
        """

        from bs4 import BeautifulSoup

        html = path.read_text(encoding="utf-8", errors="ignore")

        soup = BeautifulSoup(html, "html.parser")

        # Remove non-visible/executable elements.
        for element in soup(["script", "style", "noscript"]):
            element.decompose()

        content = soup.get_text(separator="\n")

        return {
            "source_type": "html",
            "source_name": path.name,
            "content": content,
            "metadata": {
                "file_extension": path.suffix.lower(),
                "extraction_method": "beautifulsoup",
                "extraction_status": "success",
            },
        }

    # Image/OCR
    def process_image(self, image_path: str):
        """
        Extract text from image using OCR.
        """

        path = Path(image_path)

        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        import easyocr

        reader = easyocr.Reader(["en"], gpu=False)

        results = reader.readtext(str(path), detail=0)

        content = "\n".join(results)

        return {
            "source_type": "image",
            "source_name": path.name,
            "content": content,
            "metadata": {
                "file_extension": path.suffix.lower(),
                "extraction_method": "easyocr",
                "extraction_status": "success",
            },
        }
