"""
Springer LNCS Auto-Formatter
Main Flask Application
"""

import os
import uuid
import json
import shutil
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, url_for
from werkzeug.utils import secure_filename

from utils.document_parser import DocumentParser
from utils.style_applier import StyleApplier
from utils.image_processor import ImageProcessor
from utils.template_manager import TemplateManager

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'temp_files')
app.config['OUTPUT_FOLDER'] = os.path.join(os.path.dirname(__file__), 'output')
app.config['TEMPLATES_FOLDER'] = os.path.join(os.path.dirname(__file__), 'templates_storage')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['ALLOWED_DOC_EXTENSIONS'] = {'docx', 'doc', 'txt'}
app.config['ALLOWED_IMAGE_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'tiff', 'tif', 'bmp'}

# Create necessary directories
for folder in [app.config['UPLOAD_FOLDER'], app.config['OUTPUT_FOLDER'], app.config['TEMPLATES_FOLDER']]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# Store processing sessions
processing_sessions = {}


def allowed_file(filename, file_type='doc'):
    """Check if file extension is allowed"""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    if file_type == 'doc':
        return ext in app.config['ALLOWED_DOC_EXTENSIONS']
    elif file_type == 'image':
        return ext in app.config['ALLOWED_IMAGE_EXTENSIONS']
    return False


def generate_session_id():
    """Generate unique session ID"""
    return str(uuid.uuid4())[:8]


# ============================================
# ROUTES - Pages
# ============================================

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


# ============================================
# API ROUTES
# ============================================

@app.route('/api/upload', methods=['POST'])
def upload_files():
    """Handle file uploads"""
    session_id = generate_session_id()
    session_folder = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
    os.makedirs(session_folder, exist_ok=True)
    
    result = {
        'session_id': session_id,
        'document': None,
        'images': [],
        'template': None,
        'status': 'success'
    }
    
    # Handle document upload
    if 'document' in request.files:
        doc_file = request.files['document']
        if doc_file and doc_file.filename and allowed_file(doc_file.filename, 'doc'):
            filename = secure_filename(doc_file.filename)
            doc_path = os.path.join(session_folder, filename)
            doc_file.save(doc_path)
            result['document'] = {
                'filename': filename,
                'path': doc_path
            }
    
    # Handle image uploads
    if 'images' in request.files:
        images = request.files.getlist('images')
        images_folder = os.path.join(session_folder, 'images')
        os.makedirs(images_folder, exist_ok=True)
        
        for img_file in images:
            if img_file and img_file.filename and allowed_file(img_file.filename, 'image'):
                filename = secure_filename(img_file.filename)
                img_path = os.path.join(images_folder, filename)
                img_file.save(img_path)
                result['images'].append({
                    'filename': filename,
                    'path': img_path
                })
    
    # Handle template upload
    if 'template' in request.files:
        template_file = request.files['template']
        if template_file and template_file.filename and allowed_file(template_file.filename, 'doc'):
            filename = secure_filename(template_file.filename)
            template_path = os.path.join(session_folder, 'template_' + filename)
            template_file.save(template_path)
            result['template'] = {
                'filename': filename,
                'path': template_path
            }
    
    # Store session info
    processing_sessions[session_id] = {
        'created_at': datetime.now().isoformat(),
        'folder': session_folder,
        'document': result['document'],
        'images': result['images'],
        'template': result['template'],
        'status': 'uploaded',
        'settings': {}
    }
    
    return jsonify(result)


@app.route('/api/process', methods=['POST'])
def process_document():
    """Process the uploaded document"""
    data = request.json or {}
    session_id = data.get('session_id')
    
    if not session_id or session_id not in processing_sessions:
        return jsonify({'status': 'error', 'message': 'Invalid session ID'}), 400
    
    session = processing_sessions[session_id]
    
    if not session.get('document'):
        return jsonify({'status': 'error', 'message': 'No document uploaded'}), 400
    
    try:
        # Update settings
        settings = data.get('settings', {})
        session['settings'] = settings
        session['status'] = 'processing'
        
        # Parse document
        parser = DocumentParser()
        doc_path = session['document']['path']
        
        if doc_path.endswith('.txt'):
            with open(doc_path, 'r', encoding='utf-8') as f:
                parser.load_from_text(f.read())
        else:
            parser.load_document(doc_path)
        
        parsed_content = parser.parse_sections()
        doc_stats = parser.get_document_stats()
        
        # Process images if any
        images_data = []
        if session.get('images'):
            output_images_folder = os.path.join(app.config['OUTPUT_FOLDER'], session_id, 'images')
            os.makedirs(output_images_folder, exist_ok=True)
            
            img_processor = ImageProcessor(output_images_folder)
            image_paths = [img['path'] for img in session['images']]
            
            target_width = settings.get('image_width', 80) / 100 * 14  # Convert percentage to cm
            img_processor.process_image_list(image_paths, target_width)
            images_data = img_processor.get_images_data()
        
        # Apply Springer styles
        style_applier = StyleApplier()
        style_applier.apply_springer_style(parsed_content)
        
        # Insert images
        if images_data:
            style_applier.insert_images_at_positions(images_data)
        
        # Save formatted document
        output_folder = os.path.join(app.config['OUTPUT_FOLDER'], session_id)
        os.makedirs(output_folder, exist_ok=True)
        
        output_filename = f"formatted_{session['document']['filename']}"
        if not output_filename.endswith('.docx'):
            output_filename = output_filename.rsplit('.', 1)[0] + '.docx'
        
        output_path = os.path.join(output_folder, output_filename)
        style_applier.save_document(output_path)
        
        # Update session
        session['status'] = 'completed'
        session['output'] = {
            'path': output_path,
            'filename': output_filename
        }
        session['parsed_content'] = {
            'title': parsed_content.get('title', ''),
            'authors': parsed_content.get('authors', []),
            'abstract': parsed_content.get('abstract', {}),
            'keywords': parsed_content.get('keywords', []),
            'sections': [{'type': s.get('type'), 'title': s.get('title')} 
                        for s in parsed_content.get('sections', [])]
        }
        session['stats'] = doc_stats
        session['changes'] = style_applier.get_changes_log()
        session['figure_count'] = style_applier.figure_counter
        
        return jsonify({
            'status': 'success',
            'session_id': session_id,
            'stats': doc_stats,
            'changes': session['changes'],
            'figure_count': session['figure_count'],
            'output_filename': output_filename
        })
        
    except Exception as e:
        session['status'] = 'error'
        session['error'] = str(e)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/preview/<session_id>', methods=['GET'])
def get_preview(session_id):
    """Get formatted document preview"""
    if session_id not in processing_sessions:
        return jsonify({'status': 'error', 'message': 'Invalid session ID'}), 400
    
    session = processing_sessions[session_id]
    
    # Generate HTML preview from parsed content
    preview_html = generate_preview_html(session)
    
    return jsonify({
        'status': 'success',
        'html': preview_html,
        'parsed_content': session.get('parsed_content', {}),
        'stats': session.get('stats', {}),
        'changes': session.get('changes', [])
    })


@app.route('/api/download/<session_id>/<format_type>', methods=['GET'])
def download_file(session_id, format_type):
    """Download formatted document"""
    if session_id not in processing_sessions:
        return jsonify({'status': 'error', 'message': 'Invalid session ID'}), 400
    
    session = processing_sessions[session_id]
    
    if session.get('status') != 'completed':
        return jsonify({'status': 'error', 'message': 'Document not yet processed'}), 400
    
    output_folder = os.path.join(app.config['OUTPUT_FOLDER'], session_id)
    
    if format_type == 'docx':
        # Return DOCX file
        if session.get('output'):
            return send_file(
                session['output']['path'],
                as_attachment=True,
                download_name=session['output']['filename']
            )
    
    elif format_type == 'pdf':
        # Try to convert to PDF
        try:
            from docx2pdf import convert
            docx_path = session['output']['path']
            pdf_path = docx_path.replace('.docx', '.pdf')
            
            if not os.path.exists(pdf_path):
                convert(docx_path, pdf_path)
            
            return send_file(
                pdf_path,
                as_attachment=True,
                download_name=session['output']['filename'].replace('.docx', '.pdf')
            )
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'PDF conversion failed: {str(e)}. Please download DOCX and convert manually.'
            }), 500
    
    elif format_type == 'zip':
        # Create ZIP with all files
        zip_path = os.path.join(output_folder, 'formatted_paper.zip')
        
        if not os.path.exists(zip_path):
            shutil.make_archive(
                zip_path.replace('.zip', ''),
                'zip',
                output_folder
            )
        
        return send_file(
            zip_path,
            as_attachment=True,
            download_name='formatted_paper.zip'
        )
    
    return jsonify({'status': 'error', 'message': 'Invalid format type'}), 400


@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Get current settings"""
    default_settings = {
        'font_family': 'Times New Roman',
        'section_numbers': True,
        'image_width': 80,
        'auto_detect': True,
        'template': 'springer_lncs',
        'margins': {
            'top': 2.5,
            'bottom': 2.5,
            'left': 2.5,
            'right': 2.5
        },
        'line_spacing': 1.0
    }
    return jsonify(default_settings)


@app.route('/api/settings', methods=['POST'])
def update_settings():
    """Update settings"""
    data = request.json or {}
    session_id = data.get('session_id')
    settings = data.get('settings', {})
    
    if session_id and session_id in processing_sessions:
        processing_sessions[session_id]['settings'] = settings
    
    return jsonify({'status': 'success', 'settings': settings})


@app.route('/api/templates', methods=['GET'])
def get_templates():
    """Get available templates"""
    manager = TemplateManager(app.config['TEMPLATES_FOLDER'])
    templates = manager.get_available_templates()
    return jsonify(templates)


@app.route('/api/session/<session_id>', methods=['GET'])
def get_session_info(session_id):
    """Get session information"""
    if session_id not in processing_sessions:
        return jsonify({'status': 'error', 'message': 'Invalid session ID'}), 400
    
    session = processing_sessions[session_id]
    
    return jsonify({
        'status': 'success',
        'session_id': session_id,
        'document': session.get('document'),
        'images': session.get('images', []),
        'processing_status': session.get('status'),
        'stats': session.get('stats'),
        'changes': session.get('changes', [])
    })


@app.route('/api/cleanup/<session_id>', methods=['DELETE'])
def cleanup_session(session_id):
    """Clean up session files"""
    if session_id in processing_sessions:
        session = processing_sessions[session_id]
        
        # Remove session folder
        if os.path.exists(session.get('folder', '')):
            shutil.rmtree(session['folder'], ignore_errors=True)
        
        # Remove output folder
        output_folder = os.path.join(app.config['OUTPUT_FOLDER'], session_id)
        if os.path.exists(output_folder):
            shutil.rmtree(output_folder, ignore_errors=True)
        
        del processing_sessions[session_id]
    
    return jsonify({'status': 'success'})


# ============================================
# Helper Functions
# ============================================

def generate_preview_html(session):
    """Generate HTML preview of the formatted document"""
    parsed = session.get('parsed_content', {})
    
    html_parts = ['<div class="preview-content">']
    
    # Title
    if parsed.get('title'):
        html_parts.append(f'<h1 class="preview-title">{parsed["title"]}</h1>')
    
    # Authors
    if parsed.get('authors'):
        authors_html = ', '.join([a.get('name', '') for a in parsed['authors']])
        html_parts.append(f'<p class="preview-authors">{authors_html}</p>')
    
    # Abstract
    abstract = parsed.get('abstract', {})
    if isinstance(abstract, dict):
        abstract_text = abstract.get('text', '')
    else:
        abstract_text = str(abstract)
    
    if abstract_text:
        html_parts.append(f'''
        <div class="preview-abstract">
            <strong>Abstract.</strong> <em>{abstract_text}</em>
        </div>''')
    
    # Keywords
    if parsed.get('keywords'):
        keywords_html = ' · '.join(parsed['keywords'])
        html_parts.append(f'<p class="preview-keywords"><strong>Keywords:</strong> {keywords_html}</p>')
    
    # Sections
    for i, section in enumerate(parsed.get('sections', []), 1):
        section_type = section.get('type', '')
        section_title = section.get('title', '')
        html_parts.append(f'<h2 class="preview-heading">{i}. {section_title}</h2>')
        html_parts.append('<p class="preview-body">[Section content...]</p>')
    
    html_parts.append('</div>')
    
    return '\n'.join(html_parts)


# ============================================
# Main
# ============================================

if __name__ == '__main__':
    print("\n" + "="*50)
    print("  SPRINGER LNCS AUTO-FORMATTER")
    print("="*50)
    print(f"  Server running at: http://127.0.0.1:5000")
    print("="*50 + "\n")
    
    app.run(host='127.0.0.1', port=5000, debug=True)
