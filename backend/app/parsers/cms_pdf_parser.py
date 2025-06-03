# backend/app/parsers/cms_pdf_parser.py

import pdfplumber
from typing import List, Dict


def extract_trc_rules_from_pdf(pdf_path: str, page_number: int) -> List[Dict]:
    """
    Extract TRC rules from a specific page in a CMS PDF document.
    """
    rules = []
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_number - 1]
        table = page.extract_table()

        if not table or len(table[0]) < 5:
            raise ValueError("Expected a 5-column TRC table")

        headers = table[0]
        for row in table[1:]:
            if len(row) < 5:
                continue

            code, rule_type, title, short_def, full_def = row[:5]

            rules.append({
                "rule_id": f"TRC{code.zfill(3)}",
                "cms_code": code.strip(),
                "severity": rule_type.strip(),              # e.g., "R"
                "name": title.strip(),                      # e.g., "Incorrect Birth Date"
                "description": short_def.strip(),           # e.g., "BAD BIRTH DATE"
                "definition": full_def.strip(),             # Full definition text
                "layer": 2
            })

    return rules

# -------- Configurable Runner for Testing/Debugging Only --------

if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Extract TRC rules from CMS PDF")
    parser.add_argument("--pdf", required=True, help="Path to CMS PDF file")
    parser.add_argument("--page", type=int, required=True, help="Page number with TRC table")
    parser.add_argument("--output", help="Optional path to save rules as JSON")

    args = parser.parse_args()

    trc_rules = extract_trc_rules_from_pdf(args.pdf, args.page)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(trc_rules, f, indent=2)
        print(f"Saved {len(trc_rules)} rules to {args.output}")
    else:
        print(json.dumps(trc_rules, indent=2))
