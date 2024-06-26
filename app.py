import argparse
import os
import shutil
import csv
import itertools
from io import StringIO
from flask import Flask, request, redirect, url_for, render_template, send_file, jsonify, session, make_response
from pdf2image import convert_from_path
import secrets

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
TEMP_FOLDER = 'temp'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['TEMP_FOLDER'] = TEMP_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

if not os.path.exists(TEMP_FOLDER):
    os.makedirs(TEMP_FOLDER)

current_pdf_pages = 0

@app.route('/')
def get_started():
    return render_template('get_started.html')

@app.route('/loadpdf', methods=['POST'])
def load_pdf():
    global current_pdf_pages
    
    if 'pdf' not in request.files:
        return "No file part", 400
    
    file = request.files['pdf']
    
    if file.filename == '':
        return "No selected file", 400
    
    if file and file.filename.endswith('.pdf'):
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)
        
        # Remove old temporary directory and create a new one
        if os.path.exists(TEMP_FOLDER):
            shutil.rmtree(TEMP_FOLDER)
        os.makedirs(TEMP_FOLDER)

        # Save pages of the PDF to the temporary directory as PNG files
        current_pdf_pages = save_pdf_pages_as_png(filename, TEMP_FOLDER)
        
        return redirect(url_for('setting'))
    
    return "Invalid file type", 400

def save_pdf_pages_as_png(pdf_path, output_folder):
    images = convert_from_path(pdf_path)
    for i, image in enumerate(images):
        image_path = os.path.join(output_folder, f'page_{i + 1}.png')
        image.save(image_path, 'PNG')
    return len(images)

@app.route('/page/<int:number>', methods=['GET'])
def get_page(number):
    image_path = os.path.join(app.config['TEMP_FOLDER'], f'page_{number}.png')
    if os.path.exists(image_path):
        return send_file(image_path, mimetype='image/png')
    else:
        return "Page not found", 404

@app.route('/setting')
def setting():
    return render_template('setting.html')

@app.route('/go', methods=['POST'])
def go():
    fields = request.json
    session['fields'] = fields
    return 'Fields received', 200

@app.route('/get_total_pages', methods=['GET'])
def get_total_pages():
    return jsonify(total_pages=current_pdf_pages)

@app.route('/get_fields', methods=['GET'])
def get_fields():
    fields = session.get('fields', [])
    return jsonify(fields=fields)

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    si = StringIO()
    cw = csv.writer(si)
    print(data)

    cw.writerow([field['name'] for field in data])

    keys = set(itertools.chain(*(field['texts'].keys() for field in data)))
    for key in keys:
        values = [field['texts'].get(key, []) for field in data]
        maxlen = max(map(len, values))
        for i in range(maxlen):
          cw.writerow([(value[i] if i < len(value) else value[-1]) for value in values])
    
    output = make_response(si.getvalue().encode('cp932', errors = 'replace'))
    output.headers["Content-Disposition"] = "attachment; filename=fields.csv"
    output.headers["Content-type"] = "text/csv; charset=Shift_JIS"
    return output

@app.route('/work')
def work():
    return render_template('work.html')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Flask server to upload and process PDF files")
    parser.add_argument('--host', type=str, default='127.0.0.1', help='IP address to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port number to bind to')
    parser.add_argument('--secret_key', type=str, help='Secret key for the Flask session')
    args = parser.parse_args()

    if args.secret_key:
        app.secret_key = args.secret_key
    else:
        app.secret_key = secrets.token_urlsafe(24)
        print(f"Generated secret key: {app.secret_key}")

    app.run(host=args.host, port=args.port, debug=True)
