# Open-source tool options

Read this only when a route needs a tool the user does not yet have. Offer two options at most, say what it costs the user (install, licence), and wait for their choice. Check the current licence and version on the linked page before recommending; the notes below are the licence families seen when this was written.

## Contents

- Text extraction
- OCR
- Table extraction
- Form fields
- Choosing

## Text extraction

| Option | Good for | Note | Source |
|---|---|---|---|
| pdfplumber (Python) | Text with positions, per-page cropping, tables by ruling lines | MIT family licence | https://github.com/jsvine/pdfplumber |
| pypdf (Python) | Plain text, page ranges, reading and writing form fields | BSD family licence; layout of extracted text is basic | https://github.com/py-pdf/pypdf |
| pdftotext from Poppler (command line) | Fast bulk text with a layout mode | GPL family licence; a system package, not a pip package | https://poppler.freedesktop.org |
| PyMuPDF (Python) | Fast text, rendering pages to images, form fields | AGPL or paid commercial licence: tell the user before suggesting it for a product | https://pymupdf.readthedocs.io |

## OCR

| Option | Good for | Note | Source |
|---|---|---|---|
| Tesseract (command line engine) | OCR of page images, many languages through language packs | Apache-style licence; needs the language data for each language installed | https://github.com/tesseract-ocr/tesseract |
| OCRmyPDF (command line, Python) | Turns a scanned PDF into a searchable PDF using Tesseract | MPL family licence; needs Tesseract and Ghostscript on the machine | https://github.com/ocrmypdf/OCRmyPDF |

OCR output is a guess. Digits and look-alike letters (O and 0, l and 1, S and 5) are the usual errors, so numbers always get a spot check. Right-to-left and mixed-script documents need the matching language pack and a manual read of word order.

## Table extraction

| Option | Good for | Note | Source |
|---|---|---|---|
| pdfplumber table finder | Bordered and lightly bordered tables | Tunable line and text strategies | https://github.com/jsvine/pdfplumber |
| Camelot (Python) | "lattice" mode for ruled tables, "stream" mode for whitespace tables | MIT family licence; lattice mode needs extra system software in some versions | https://camelot-py.readthedocs.io |
| tabula-py (Python wrapper) | Tables in digital PDFs | Needs a Java runtime | https://github.com/tabulapdf/tabula-py |

Scans need OCR first. Table tools on an image-only PDF return nothing, which is why triage comes first.

## Form fields

| Option | Good for | Note | Source |
|---|---|---|---|
| pypdf | List fields, set values, write a new file | Use the library's documented option that makes viewers redraw field values | https://github.com/py-pdf/pypdf |
| PyMuPDF | Widgets API for fields and options | AGPL note above | https://pymupdf.readthedocs.io |
| qpdf (command line) | Inspect structure, decrypt files the user has the password for | Apache-style licence; not a form filler | https://github.com/qpdf/qpdf |

## Choosing

1. Digital PDF, text only: pdftotext or pdfplumber.
2. Digital PDF with tables: pdfplumber first; Camelot if columns are separated only by space.
3. Scan: OCRmyPDF when a searchable PDF is wanted, otherwise Tesseract on page images, then the table or text steps above.
4. Form: pypdf unless the user already has another library.
