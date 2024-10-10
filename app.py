from flask import Flask, render_template, request, send_file, jsonify
from rembg import remove
from PIL import Image, ImageOps
from io import BytesIO
import os

app = Flask(__name__)

# Helper function to process images
def process_image(file, output_format, quality, background_color=None, background_image=None):
    input_image = Image.open(file.stream)
    output_image = remove(input_image)

    # Replace background if specified
    if background_image:
        background = Image.open(background_image.stream).convert("RGBA")
        background = background.resize(output_image.size)
        output_image = Image.alpha_composite(background, output_image)
    elif background_color:
        # Apply a solid color background if no image is provided
        background = Image.new("RGBA", output_image.size, background_color)
        output_image = Image.alpha_composite(background, output_image)

    # Save the output image in the chosen format and quality
    img_io = BytesIO()
    if output_format == 'JPEG':
        output_image = output_image.convert("RGB")  # JPEG doesn't support transparency
        output_image.save(img_io, 'JPEG', quality=int(quality))
    else:
        output_image.save(img_io, 'PNG')
    img_io.seek(0)
    return img_io

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No file uploaded', 400
        
        files = request.files.getlist('file')  # Get list of files for multiple uploads
        if not files or files[0].filename == '':
            return 'No file selected', 400

        output_format = request.form.get('format', 'PNG')
        quality = request.form.get('quality', 90)
        background_color = request.form.get('background')
        background_image = request.files.get('background-image')

        result_files = []
        for file in files:
            try:
                img_io = process_image(file, output_format, quality, background_color, background_image)
                result_files.append(img_io)
            except Exception as e:
                return f"Error processing file {file.filename}: {e}", 400

        # Send back multiple files as a zip or return one by one depending on your preference
        if len(result_files) == 1:
            return send_file(result_files[0], mimetype=f'image/{output_format.lower()}', as_attachment=True, download_name=f'_rmbg.{output_format.lower()}')
        else:
            # For simplicity, returning only the first image in case of multiple files
            return send_file(result_files[0], mimetype=f'image/{output_format.lower()}', as_attachment=True, download_name=f'_rmbg.{output_format.lower()}')

    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5100)
