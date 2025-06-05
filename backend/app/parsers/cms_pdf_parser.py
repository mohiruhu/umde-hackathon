import pdfplumber
from typing import List, Dict, Any
import re
import json

def extract_trc_rules_from_pdf(pdf_path: str, page_number: int) -> List[Dict[str, Any]]:
    """
    Extract TRC rules from a specific page in a CMS PDF document.
    Uses table parsing first; falls back to regex text extraction if no rules are found.
    """
    rules: List[Dict[str, Any]] = []

    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_number - 1]

        # Try table extraction first
        tables = page.extract_tables()
        print(f"DEBUG: Extracted {len(tables)} tables from page {page_number}")
        if tables:
            for i, row in enumerate(tables[0][:5]):
                print(f"Row {i}: {row}")

            for table in tables:
                if not table or len(table[0]) < 5:
                    continue

                current_rule = None

                for row in table[1:]:
                    if len(row) < 5:
                        continue

                    code, rule_type, title, short_def, full_def = [cell.strip() if cell else "" for cell in row[:5]]
                    code = code.upper()

                    if re.match(r"TRC\d{3}", code):
                        if current_rule:
                            rules.append(current_rule)

                        current_rule = {
                            "rule_id": code,
                            "cms_code": code,
                            "severity": rule_type,
                            "name": title,
                            "description": short_def,
                            "definition": full_def,
                            "layer": 2
                        }
                    elif current_rule:
                        if short_def:
                            current_rule["description"] = str(current_rule.get("description", "")) + " " + short_def
                        if full_def:
                           current_rule["definition"] = str(current_rule.get("definition", "")) + " " + full_def

                if current_rule:
                    rules.append(current_rule)

        # Fallback to regex text extraction
        if not rules:
            print("⚠️ Table parsing failed — falling back to regex text extraction...")
            text = page.extract_text()
            pattern = r"(TRC\d{3})[^\n]*?\n([^\n]+)"
            matches = re.findall(pattern, text)

            for rule_id, desc in matches:
                rules.append({
                    "rule_id": rule_id,
                    "cms_code": rule_id,
                    "severity": "N/A",
                    "doc_link": "https://www.cms.gov/files/document/plan-communications-user-guide-v178.pdf",
                    "name": "Auto-extracted",
                    "description": desc.strip(),
                    "definition": "",
                    "layer": 2
                })


    return rules
def export_rules_to_json(rules: List[Dict[str, Any]], output_path: str) -> None:
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(rules, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    pdf_path = "backend/app/resources/CMS_Plan_Comm_User_Guide_v17.8.pdf"
    page_number = 68  # Confirmed via detection
    output_path = "backend/app/rules/trc_rules.json"

    rules = extract_trc_rules_from_pdf(pdf_path, page_number)
    export_rules_to_json(rules, output_path)

    print(f"✅ Exported {len(rules)} rules to {output_path}")