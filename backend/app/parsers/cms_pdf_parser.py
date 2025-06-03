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

        if not table:
            raise ValueError(f"No table found on page {page_number}")

        for row in table[1:]:
            if len(row) < 3:
                continue  # skip malformed rows
            trc_code, title, description = row[:3]

            rule = {
                "rule_id": f"TRC{trc_code.zfill(3)}",
                "name": title.strip(),
                "description": description.strip(),
                "layer": 2,
                "cms_code": trc_code.strip()
            }
            rules.append(rule)

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
