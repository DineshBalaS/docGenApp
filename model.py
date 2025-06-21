from docx import Document
from docx.shared import Inches
from pptx import Presentation
from pptx.util import Inches as PptInches
import os
import re

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'templates_src')
DOCX_TEMPLATE = os.path.join(TEMPLATE_DIR, 'template.docx')
PPTX_TEMPLATE = os.path.join(TEMPLATE_DIR, 'ppt.pptx')

IMAGE_FIELDS = [
    "property - sample 1 - screenshot",
    "property - sample 1 - image",
    "property - sample 2 - screenshot",
    "property - sample 2 - image"
]

if not os.path.exists(DOCX_TEMPLATE):
    raise FileNotFoundError(f"DOCX template not found at: {DOCX_TEMPLATE}")


def clean_placeholder(placeholder):
    return re.sub(r'\(.*?\)|-.*', '', placeholder).strip().lower()


def find_matching_key(raw_placeholder, data_keys):
    raw_clean = raw_placeholder.strip().lower()
    if raw_clean in data_keys:
        return raw_clean
    for key in data_keys:
        if clean_placeholder(raw_placeholder) == key.lower():
            return key
    return None


def replace_in_paragraphs(paragraphs, data):
    for para in paragraphs:
        matches = re.findall(r"\{\{(.*?)\}\}", para.text)
        for raw_ph in matches:
            actual_key = find_matching_key(raw_ph, data)
            if actual_key:
                value = data[actual_key]
                
                # Ensure value is a string
                if isinstance(value, list):
                    value = ", ".join(value)  # Join list items into a single string
                
                if actual_key in IMAGE_FIELDS:
                    image_path = os.path.abspath(value)  # Ensure absolute path
                    if os.path.isfile(image_path):
                        para.clear()
                        para.add_run().add_picture(image_path, width=Inches(4.5))
                    else:
                        print(f"Image file not found: {image_path}")
                        full_ph = f"{{{{{raw_ph}}}}}"
                        para.text = para.text.replace(full_ph, f"[Image missing: {actual_key}]")
                else:
                    full_ph = f"{{{{{raw_ph}}}}}"
                    para.text = para.text.replace(full_ph, value)

def replace_in_tables(tables, data):
    for table in tables:
        for row in table.rows:
            for cell in row.cells:
                replace_in_paragraphs(cell.paragraphs, data)


def generate_docx(data: dict, output_path: str):
    doc = Document(DOCX_TEMPLATE)
    replace_in_paragraphs(doc.paragraphs, data)
    replace_in_tables(doc.tables, data)
    doc.save(output_path)

def generate_pptx(data: dict, output_path: str):
    ppt = Presentation(PPTX_TEMPLATE)
    for slide in ppt.slides:
        for shape in list(slide.shapes):
            if shape.has_text_frame:
                tf = shape.text_frame
                text = "\n".join(run.text for p in tf.paragraphs for run in p.runs)

                # Handle bullet list
                if "{{list of documents required}}" in text:
                    tf.clear()
                    for doc in data.get('list of documents required', []):
                        p = tf.add_paragraph()
                        p.text = doc
                        p.level = 0
                    continue

                # Handle other placeholders
                for para in tf.paragraphs:
                    for run in para.runs:
                        matches = re.findall(r"\{\{(.*?)\}\}", run.text)
                        for raw_ph in matches:
                            actual_key = find_matching_key(raw_ph, data)
                            if actual_key:
                                value = data[actual_key]
                                full_ph = f"{{{{{raw_ph}}}}}"

                                # If image placeholder
                                if actual_key in IMAGE_FIELDS:
                                    image_path = os.path.abspath(value)
                                    if os.path.isfile(image_path):
                                        # Remember shape's position & size
                                        left = shape.left
                                        top = shape.top
                                        width = PptInches(4.5)  # Adjust size as needed
                                        height = None  # Let PowerPoint auto-calculate height

                                        # Remove placeholder text shape
                                        slide.shapes._spTree.remove(shape._element)

                                        # Insert image
                                        slide.shapes.add_picture(image_path, left, top, width=width, height=height)
                                    else:
                                        print(f"⚠️ Image file not found: {image_path}")
                                else:
                                    # Replace text normally
                                    if isinstance(value, list):
                                        value = ", ".join(value)
                                    if isinstance(value, str):
                                        run.text = run.text.replace(full_ph, value)
                                    else:
                                        print(f"⚠️ Non-string for {actual_key}: {type(value)}")
    ppt.save(output_path)
