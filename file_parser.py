import PyPDF2
import docx
import io
from typing import Dict, Any

def parse_pdf(file_content: bytes) -> str:
    """Извлечь текст из PDF"""
    try:
        pdf_file = io.BytesIO(file_content)
        reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        return f"Ошибка парсинга PDF: {str(e)}"

def parse_docx(file_content: bytes) -> str:
    """Извлечь текст из DOCX"""
    try:
        docx_file = io.BytesIO(file_content)
        doc = docx.Document(docx_file)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text.strip()
    except Exception as e:
        return f"Ошибка парсинга DOCX: {str(e)}"

def parse_resume_file(filename: str, file_content: bytes) -> Dict[str, Any]:
    """Парсит резюме из файла"""
    filename_lower = filename.lower()
    
    if filename_lower.endswith('.pdf'):
        text = parse_pdf(file_content)
    elif filename_lower.endswith('.docx'):
        text = parse_docx(file_content)
    else:
        return {"error": "Неподдерживаемый формат. Используй PDF или DOCX"}
    
    if text.startswith("Ошибка"):
        return {"error": text}
    
    return {
        "success": True,
        "text": text,
        "filename": filename
    }