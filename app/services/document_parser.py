import os
import fitz  # PyMuPDF
import docx
import pandas as pd
from typing import List
from docx.document import Document
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph

def iter_block_items(parent):
    """
    Yield each paragraph and table child within *parent*, in document order.
    Each returned value is an instance of either Table or Paragraph.
    """
    if isinstance(parent, Document):
        parent_elm = parent.element.body
    else:
        return
        
    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)

class DocumentParser:
    def parse_document(self, file_path: str, filename: str) -> str:
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        if ext == 'pdf':
            return self._parse_pdf(file_path)
        elif ext == 'docx':
            return self._parse_docx(file_path)
        elif ext == 'txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        elif ext in ['csv', 'xlsx']:
            return self._parse_spreadsheet(file_path, ext)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    @staticmethod
    def _parse_pdf(file_path: str) -> str:
        # We will keep PDF parsing simple for now, but real enterprise PDF parsing
        # requires complex layout analysis. PyMuPDF does provide blocks.
        doc = fitz.open(file_path)
        text_content = []
        for page in doc:
            text_content.append(page.get_text("text"))
        return "\n".join(text_content)

    @staticmethod
    def _parse_docx(file_path: str) -> str:
        doc = docx.Document(file_path)
        text_content = []
        
        current_section = "General"
        
        for block in iter_block_items(doc):
            if isinstance(block, Paragraph):
                text = block.text.strip()
                if not text:
                    continue
                # Simple heuristic for section headers (e.g. "3.6 Application Health")
                # Look for numbers followed by dots, then text, usually bold or short
                if text[0].isdigit() and (' ' in text) and len(text) < 150:
                    current_section = text
                
                text_content.append(f"[SECTION: {current_section}] " + text)
                
            elif isinstance(block, Table):
                for row in block.rows:
                    row_data = []
                    for cell in row.cells:
                        c_text = cell.text.strip().replace('\n', ' ')
                        if c_text and c_text not in row_data:
                            row_data.append(c_text)
                    if row_data:
                        text_content.append(f"[SECTION: {current_section}] " + " | ".join(row_data))
                        
        return "\n".join(text_content)

    @staticmethod
    def _parse_spreadsheet(file_path: str, ext: str) -> str:
        if ext == 'csv':
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
            
        text_content = []
        for _, row in df.iterrows():
            row_data = [str(val).strip() for val in row.values if pd.notna(val)]
            if row_data:
                text_content.append(" | ".join(row_data))
                
        return "\n".join(text_content)

document_parser = DocumentParser()
