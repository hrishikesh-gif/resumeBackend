from PyPDF2 import PdfReader


def extract_text_from_pdf(file):
    """
    Extract text from uploaded PDF file
    """
    reader = PdfReader(file)
    text = ""

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"

    return text.strip()
