import pdfplumber
from typing import List, Dict, Any, Optional

def extract_trc_rules_from_pdf(pdf_path: str, page_number: int) -> List[Dict[str, Any]]:
    """
    Extract TRC rules from a specific page in a CMS PDF document.
    """
    rules: List[Dict[str, Any]] = []

    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_number - 1]
        tables: List[List[List[Optional[str]]]] = page.extract_tables()

    if not tables:
        raise ValueError("No tables found on the page.")

    for table in tables:
        if len(table[0]) < 5:
            continue  # skip malformed tables

        for row in table[1:]:
            if len(row) < 5:
                continue

            code, rule_type, title, short_def, full_def = row[:5]

            rules.append({
                "rule_id": f"TRC{(code or '').zfill(3)}",
                "cms_code": (code or "").strip(),
                "severity": (rule_type or "").strip(),
                "name": (title or "").strip(),
                "description": (short_def or "").strip(),
                 "definition": (full_def or "").strip(),
                "layer": 2
            })

    return rules
