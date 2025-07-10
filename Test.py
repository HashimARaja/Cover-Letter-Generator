import os
import sys
from pathlib import Path
import requests
from PyPDF2 import PdfReader
from fpdf import FPDF
from dotenv import load_dotenv
from google import genai
import json
from pathlib import Path

if getattr(sys, "frozen", False):
    # running as a bundle
    BASE_DIR = Path(sys.executable).parent
else:
    # running from source
    BASE_DIR = Path(__file__).resolve().parent




path1 = BASE_DIR / "Header.txt"
with path1.open("r", encoding="utf-8") as f:
    info1: dict = json.load(f)


Path("Cover_Letters").mkdir(exist_ok=True)


# Load environment variables from local .env file (if present)
load_dotenv()

# Configuration
API_ENDPOINT = os.getenv(
    "GEMINI_API_ENDPOINT",
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
)
client = genai.Client(api_key=info1["api_key"])


# Base directory and resume path (expects resume.pdf in same folder)

RESUME_PATH =  BASE_DIR / "resume.pdf"


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract text from all pages of the PDF resume."""
    reader = PdfReader(str(pdf_path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)
from reportlab.lib.pagesizes import LETTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime
from pathlib import Path


def save_to_pdf(text: str, output_path: Path):
    """Generate a cover letter PDF with Times New Roman, 11pt, and header at top left."""
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=LETTER,
        leftMargin=inch,
        rightMargin=inch,
        topMargin=inch,
        bottomMargin=inch
    )

    # Styles: both header and body use Times New Roman, 11pt
    header_style = ParagraphStyle(
        name="Header",
        fontName="Times-Roman",
        fontSize=11,
        leading=14,
        spaceAfter=6,
        alignment=0  # left-aligned
    )
    body_style = ParagraphStyle(
        name="Body",
        fontName="Times-Roman",
        fontSize=11,
        leading=14,
        firstLineIndent=24,
        spaceAfter=12,
        alignment=4  # justified text
    )

    story = []
    # Top-left header: name, email, phone
    story.append(Paragraph(info1["name"], header_style))
    story.append(Paragraph(info1["email"], header_style))
    story.append(Paragraph(info1["number"], header_style))
    story.append(Spacer(1, 12))  # space before date or body

    # Optional: add date below header
    story.append(Paragraph(datetime.now().strftime("%B %d, %Y"), header_style))
    story.append(Spacer(1, 24))  # extra space before body content

    # Body paragraphs
    n = len(text.strip().split("\n\n"))
    for para in text.strip().split("\n\n"):
        if (n > 3):
            story.append(Paragraph(para, body_style))
        else:
            story.append(Paragraph(para, header_style))
        n = n - 1
    
    doc.build(story)




def main():
    # Ensure resume is present
    

    # Prompt user for job description
    job_desc = input("Enter the full job description:\n")

    # Extract resume text
    resume_text = extract_text_from_pdf(RESUME_PATH)

    # First API call: generate human-like cover letter text
    prompt_letter = (
        "Using the resume provided below as context and the following job description, "
        "write a personalized, human-sounding cover letter. Respond ONLY with the cover letter text. DO NOT LEAVE ANY AREA UNFILLED WITH PLACEHOLDERS LIKE '{company name}', simply fill it out to your best knowledge.\n\n"
        f"Resume:\n{resume_text}\n\nJob Description:\n{job_desc}"
    )
    cover_text = str(client.models.generate_content(
    model="gemini-2.0-flash", contents = prompt_letter, ).text)

    # Second API call: derive filename from job description
    prompt_title = (
        "Based solely on the following job description, return EXACTLY the filename in this format: "
        "Cover Letter - <Company> - <Position> (without any extra text).\n\n"
        f"Job Description:\n{job_desc}"
    )
    title_text = str(client.models.generate_content(
    model="gemini-2.0-flash", contents = prompt_title, ).text)

    print()
    print(f"Generated Cover Letter Title: {title_text}")
    print()
    print("Cover Letter Text:", cover_text)

    # Sanitize filename and define output path
    safe_title = title_text.replace("/", "_").strip()
    output_pdf = BASE_DIR / "Cover_Letters" / f"{safe_title}.pdf"

    # Save the cover letter PDF
    save_to_pdf(cover_text, output_pdf)
    print(f"Cover letter saved as {output_pdf}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("❌ Error:", e)
    finally:
        input("\nPress Enter to exit…")

