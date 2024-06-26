import argparse
from flask import Flask, request, redirect, url_for, render_template, send_file, jsonify
import os
import shutil
from pdf2image import convert_from_path

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

@app.route('/npages', methods=['GET'])
def get_number_of_pages():
    return jsonify(npages=current_pdf_pages)

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

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Flask server to upload and process PDF files")
    parser.add_argument('--host', type=str, default='127.0.0.1', help='IP address to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port number to bind to')
    args = parser.parse_args()

    app.run(host=args.host, port=args.port, debug=True)
