# pdf_processor.py
import re
from pypdf import PdfReader
from typing import Optional

def extract_text_from_pdf(pdf_path: str) -> Optional[str]:
    try:
        reader = PdfReader(pdf_path)
        full_text = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                full_text.append(text)
        raw = "\n".join(full_text)
        cleaned = clean_text(raw)
        return cleaned
    except Exception as e:
        print(f"提取PDF失败 {pdf_path}: {e}")
        return None

def clean_text(text: str) -> str:
    lines = text.splitlines()
    cleaned_lines = []
    for line in lines:
        # 删除纯数字行（页码）
        if re.match(r'^\s*\d+\s*$', line):
            continue
        # # 删除短标题行如“空城计·第一场”
        # if re.match(r'^\s*【?.*?[场回]】?\s*$', line) and len(line) < 30:
        #     continue
        # 不再删除包含“戏考”、“整理”等字样的行，因为它们是重要的边界标记
        # if re.search(r'(戏考|整理|根据|校注|页眉|页码)', line):
        #     continue
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines)