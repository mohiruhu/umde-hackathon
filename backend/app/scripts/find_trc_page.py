import pdfplumber

pdf_path = "backend/app/resources/CMS_Plan_Comm_User_Guide_v17.8.pdf"

with pdfplumber.open(pdf_path) as pdf:
    for i, page in enumerate(pdf.pages):
        text = page.extract_text()
        if text and "TRC006" in text:
            print(f"✅ Found TRC rules on actual PDF page index {i+1}")
            break
    else:
        print("❌ TRC rules not found in any page.")
