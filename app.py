from flask import Flask, render_template, request, send_file, url_for, session, abort, after_this_request, flash
from model import generate_docx, generate_pptx
import os
import uuid
import re
import tempfile
import threading
import shutil
from PIL import Image
from io import BytesIO

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'generated'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
app.secret_key = os.environ.get("7338887062", os.urandom(24))

PLACEHOLDERS = [
    "property address",
    "client name",
    "Property image 1",
    "Property image 2",
    "Property 3D images 2",
    "Property 3D images 1",
    "Interior image 2",
    "Interior image 1",
    "Interior image 4",
    "Interior image 3",
    "existing use",
    "local council name",
    "total area",
    "constraints",
    "OS Map",
    "scope of work",
    "Conceptual Design Chatgpt",
    "Conceptual Floor Plan",
    "Link 1",
    "timeline 1",
    "property address - sample 1",
    "property - sample 1 - screenshot",
    "property - sample 1 - image",
    "Sim app Floor plan 1",
    "Sim app elevation 1",
    "Link 2",
    "timeline 2",
    "property address - sample 2",
    "property - sample 2 - screenshot",
    "property - sample 2 - image",
    "Sim app floor plan 2",
    "Sim app elevation 2",
    "rejected application- image",
    "list of documents required",
    "PD/ Full PP/ House holder",
    "property type",
    "constraints - e.g.",
    "subject to property constraints similar to “whether that’s for guests, a home office, or just your own cosy retreat.”",
    "proposed change of use",
    "Planning description in 2 lines",
    "proposed use"
]

IMAGE_FIELDS = [
    "property - sample 1 - screenshot",
    "property - sample 1 - image",
    "property - sample 2 - screenshot",
    "property - sample 2 - image",
    "Property image 1",
    "Property image 2",
    "Property 3D images 1",
    "Property 3D images 2",
    "Interior image 1",
    "Interior image 2",
    "Interior image 3",
    "Interior image 4",
    "OS Map",
    "scope of work",
    "Conceptual Design Chatgpt",
    "Conceptual Floor Plan",
    "Sim app Floor plan 1",
    "Sim app elevation 1",
    "Sim app floor plan 2",
    "Sim app elevation 2",
    "rejected application- image"
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
                    if not filename.lower().endswith(('.jpg', '.jpeg')):
                        # 🆕 Handle wrong file type
                        data[key] = ''
                        data[f"{key}__web"] = ''
                        flash(f"The file for '{key}' must be a JPEG or JPG.", 'error')
                        continue # 🆕 Skip to the next key
                    
                    uploaded_file.save(filepath)
                    try:
                        Image.open(filepath).verify() # Checks if the image is valid
                        data[key] = filepath
                        data[f"{key}__web"] = os.path.join('generated', session_id, filename)
                        print(f"✅ Successfully validated and saved image: {filepath}")
                    except (IOError, OSError) as e:
                        os.remove(filepath)
                        data[key] = ''
                        data[f"{key}__web"] = ''
                        flash(f"The file for '{key}' is corrupted and could not be used.", 'error')
                        print(f"⚠️ Invalid image file detected and rejected: {filepath}")
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
                    

        # Generate files
        client_name = request.form.get('client name', 'ProposalClient').strip().replace(' ', '_')
        safe_name = re.sub(r'[^\w\-]', '', client_name)  # Remove unsafe characters


        session['form_data'] = data.copy()
        
        print(f"--- DATA FROM FORM ---\n{data}\n--------------------")

        return render_template('preview.html', data=data,
                       docx_file=url_for('download_dynamic', filetype="docx"),
                       pptx_file=url_for('download_dynamic', filetype="pptx"))

    previous_data = session.pop('form_data', None)
    return render_template('index.html', placeholders=PLACEHOLDERS, previous_data=previous_data, IMAGE_FIELDS=IMAGE_FIELDS)

@app.route('/download/<filetype>')
def download_dynamic(filetype):
    data = session.get('form_data')
    if not data:
        abort(400, "Session expired or no data found.")

    client_name = data.get('client name', 'DocGenUser').strip().replace(' ', '_')
    safe_name = re.sub(r'[^\w\-]', '', client_name)
    ext = 'docx' if filetype == 'docx' else 'pptx'
    filename = f"{safe_name}_Generated.{ext}"

    # Generate file in a memory stream
    file_stream = BytesIO()
    if filetype == 'pptx':
        generate_pptx(data, output_path=file_stream)
    elif filetype == 'docx':
        generate_docx(data, output_path=file_stream)
    else:
        abort(404)
    file_stream.seek(0)

    @after_this_request
    def cleanup(response):
        # Your image cleanup logic can remain here
        try:
            for key in data:
                if key in IMAGE_FIELDS and data.get(key):
                    session_folder = os.path.dirname(data[key])
                    if os.path.exists(session_folder):
                        import shutil
                        shutil.rmtree(session_folder)
                        break
        except Exception as e:
            print(f"Cleanup failed: {e}")
        return response

    return send_file(file_stream, as_attachment=True, download_name=filename)



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6900, debug=True)
