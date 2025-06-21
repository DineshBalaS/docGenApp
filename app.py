from flask import Flask, render_template, request, send_file, url_for, session
from model import generate_docx, generate_pptx
import os
import uuid
import re

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'generated'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
app.secret_key = os.environ.get("7338887062", os.urandom(24))

PLACEHOLDERS = [
    "client name",
    "property address",
    "property type",
    "total area",
    "constraints",
    "constraints - e.g.,",
    "local council name",
    "scope of work",
    "proposed use",
    "existing use",
    "PD/ Full PP/ House holder",
    "timeline 1",
    "timeline 2",
    "property address - sample 1",
    "property address - sample 2",
    "property - sample 1 - screenshot",
    "property - sample 1 - image",
    "property - sample 2 - screenshot",
    "property - sample 2 - image",
    "list of documents required",
    "Link 1",
    "Link 2",
    "Planning description in 2 lines",
    "Planning description in 2 lines- 2",
    "subject to property constraints similar to “whether that’s for guests, a home office, or just your own cosy retreat.”",
    "proposed change of use"
]

IMAGE_FIELDS = [
    "property - sample 1 - screenshot",
    "property - sample 1 - image",
    "property - sample 2 - screenshot",
    "property - sample 2 - image"
]

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        session_id = str(uuid.uuid4())
        session_folder = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
        os.makedirs(session_folder, exist_ok=True)
        data = {}

        for key in PLACEHOLDERS:
            if key in IMAGE_FIELDS:
                uploaded_file = request.files.get(key)
                if uploaded_file and uploaded_file.filename:
                    filename = uploaded_file.filename
                    filepath = os.path.join(session_folder, filename)
                    uploaded_file.save(filepath)
                    data[key] = filepath
                    data[f"{key}__web"] = os.path.join('generated', session_id, filename)
                else:
                    data[key] = ''
                    data[f"{key}__web"] = ''
            else:
                # Handle multi-select / checkboxes
                values = request.form.getlist(key)
                if key == 'list of documents required':
                    # store raw list for PPT bullet generation
                    data[key] = values
                    # fallback string for DOCX or preview
                    data[f"{key}__str"] = ", ".join(values)
                else:
                    data[key] = ", ".join(values) if len(values) > 1 else request.form.get(key, '')
                    
        session['form_data'] = data.copy()

        # Generate files
        client_name = request.form.get('client name', 'ProposalClient').strip().replace(' ', '_')
        safe_name = re.sub(r'[^\w\-]', '', client_name)  # Remove unsafe characters

        docx_filename = f"{safe_name}_Proposal.docx"
        pptx_filename = f"{safe_name}_Presentation.pptx"

        docx_path = os.path.join(app.config['UPLOAD_FOLDER'], docx_filename)
        pptx_path = os.path.join(app.config['UPLOAD_FOLDER'], pptx_filename)

        

        generate_docx(data, output_path=docx_path)
        generate_pptx(data, output_path=pptx_path)

        return render_template('preview.html', data=data,
                       docx_file=url_for('download_file', filename=docx_filename),
                       pptx_file=url_for('download_file', filename=pptx_filename))

    previous_data = session.pop('form_data', None)
    return render_template('index.html', placeholders=PLACEHOLDERS, previous_data=previous_data)

@app.route('/download/<filename>')
def download_file(filename):
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    return send_file(path, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6900, debug=True)
