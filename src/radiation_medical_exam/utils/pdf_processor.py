"""
PDF processing utilities for radiation medical exam documentation.
"""
import os
from pypdf import PdfReader
from typing import Dict, List


class PDFProcessor:
    """Handle PDF document processing and content extraction."""
    
    def __init__(self, base_path: str):
        self.base_path = base_path
        self._cache: Dict[str, str] = {}
    
    async def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text content from a PDF file."""
        if pdf_path in self._cache:
            return self._cache[pdf_path]
        
        full_path = os.path.join(self.base_path, pdf_path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"PDF not found: {full_path}")
        
        try:
            # Extract text using pypdf
            reader = PdfReader(full_path)
            text_content = []
            
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text.strip():  # Only add non-empty pages
                    text_content.append(f"--- PAGE {page_num + 1} ---\n{page_text}")
            
            extracted_text = "\n\n".join(text_content)
            
            # Cache the result
            self._cache[pdf_path] = extracted_text
            return extracted_text
            
        except Exception as e:
            raise ValueError(f"Error processing PDF {pdf_path}: {str(e)}")
    
    async def extract_chapter(self, pdf_path: str, chapter_num: int) -> str:
        """Extract a specific chapter from the PDF."""
        full_text = await self.extract_text_from_pdf(pdf_path)
        
        # Simple chapter extraction - look for chapter markers
        lines = full_text.split('\n')
        chapter_lines = []
        in_chapter = False
        
        for line in lines:
            line_upper = line.strip().upper()
            
            # Start of target chapter
            if f"CHAPTER {chapter_num}" in line_upper or f"CH-{chapter_num}" in line_upper:
                in_chapter = True
                chapter_lines.append(line)
                continue
            
            # End of chapter (next chapter starts)
            if in_chapter and ("CHAPTER" in line_upper and str(chapter_num + 1) in line_upper):
                break
            
            if in_chapter:
                chapter_lines.append(line)
        
        if not chapter_lines:
            return f"Chapter {chapter_num} not found in PDF"
        
        return "\n".join(chapter_lines)
    
    def get_available_pdfs(self) -> List[str]:
        """Get list of available PDF files."""
        if not os.path.exists(self.base_path):
            return []
        
        pdf_files = []
        for file in os.listdir(self.base_path):
            if file.lower().endswith('.pdf'):
                pdf_files.append(file)
        
        return pdf_files
