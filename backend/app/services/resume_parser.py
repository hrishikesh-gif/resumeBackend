from io import BytesIO
from PyPDF2 import PdfReader
from docx import Document


def extract_text_from_file(file_bytes: BytesIO, filename: str):
    """
    Extract text from PDF and DOCX files
    """
    filename = filename.lower()

    # ================= PDF =================
    if filename.endswith(".pdf"):
        try:
            reader = PdfReader(file_bytes)
            text = ""

            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

            return text.strip()

        except Exception as e:
            raise Exception(f"PDF extraction failed: {str(e)}")

    # ================= DOCX =================
    elif filename.endswith(".docx"):
        try:
            doc = Document(file_bytes)
            text = "\n".join([para.text for para in doc.paragraphs])
            return text.strip()

        except Exception as e:
            raise Exception(f"DOCX extraction failed: {str(e)}")

    # ================= DOC (Not Supported) =================
    elif filename.endswith(".doc"):
        raise Exception(
            "Old .doc format is not supported. Please convert to .docx."
        )

    # ================= Unsupported =================
    else:
        raise Exception("Unsupported file format. Upload PDF or DOCX.")