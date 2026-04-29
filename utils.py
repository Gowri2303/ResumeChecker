"""
Utility functions for PDF text extraction and text processing.
"""

import PyPDF2
import io
import re


def extract_text_from_pdf(uploaded_file) -> str:
    """
    Extract text content from an uploaded PDF file.
    
    Args:
        uploaded_file: Streamlit UploadedFile object (PDF)
    
    Returns:
        Extracted text as a string
    """
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        
        # Reset file pointer for potential re-reads
        uploaded_file.seek(0)
        
        return text.strip()
    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")


def clean_text(text: str) -> str:
    """
    Clean and normalize extracted text.
    
    Args:
        text: Raw extracted text
    
    Returns:
        Cleaned text string
    """
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s.,;:!?/\-@#&()+]', '', text)
    return text.strip()


def extract_skills_from_text(text: str, skill_list: list) -> list:
    """
    Find which skills from a given list appear in the text.
    
    Args:
        text: Resume text (lowercased)
        skill_list: List of skills to search for
    
    Returns:
        List of matched skills
    """
    text_lower = text.lower()
    matched = []
    for skill in skill_list:
        # Use word boundary matching for short skills to avoid false positives
        if len(skill) <= 3:
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower):
                matched.append(skill)
        else:
            if skill.lower() in text_lower:
                matched.append(skill)
    return list(set(matched))  # Remove duplicates
