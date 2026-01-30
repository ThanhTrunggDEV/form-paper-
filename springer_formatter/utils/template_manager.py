"""
Template Manager for Springer LNCS Formatter
Manages and applies document templates
"""

import os
from docx import Document
from typing import Dict, List, Optional
import shutil


class TemplateManager:
    """Manage document templates"""
    
    AVAILABLE_TEMPLATES = {
        'springer_lncs': {
            'name': 'Springer LNCS',
            'description': 'Lecture Notes in Computer Science format',
            'page_size': 'A4',
            'margins': {'top': 2.5, 'bottom': 2.5, 'left': 2.5, 'right': 2.5}
        },
        'ieee': {
            'name': 'IEEE Conference',
            'description': 'IEEE two-column conference format',
            'page_size': 'Letter',
            'margins': {'top': 2.0, 'bottom': 2.0, 'left': 1.75, 'right': 1.75}
        },
        'acm': {
            'name': 'ACM SIG',
            'description': 'ACM Special Interest Group format',
            'page_size': 'Letter',
            'margins': {'top': 2.5, 'bottom': 2.5, 'left': 2.5, 'right': 2.5}
        }
    }
    
    def __init__(self, templates_dir: str = None):
        self.templates_dir = templates_dir or 'templates_storage'
        self.current_template = 'springer_lncs'
        
        # Create templates directory if needed
        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir)
    
    def get_available_templates(self) -> List[Dict]:
        """Get list of available templates"""
        templates = []
        
        for key, info in self.AVAILABLE_TEMPLATES.items():
            template = {
                'id': key,
                'name': info['name'],
                'description': info['description'],
                'page_size': info['page_size'],
                'has_file': self._template_file_exists(key)
            }
            templates.append(template)
        
        return templates
    
    def get_template_info(self, template_id: str) -> Optional[Dict]:
        """Get information about a specific template"""
        if template_id in self.AVAILABLE_TEMPLATES:
            info = self.AVAILABLE_TEMPLATES[template_id].copy()
            info['id'] = template_id
            info['has_file'] = self._template_file_exists(template_id)
            return info
        return None
    
    def set_current_template(self, template_id: str) -> bool:
        """Set the current template"""
        if template_id in self.AVAILABLE_TEMPLATES:
            self.current_template = template_id
            return True
        return False
    
    def get_current_template(self) -> Dict:
        """Get current template info"""
        return self.get_template_info(self.current_template)
    
    def load_template_document(self, template_id: str = None) -> Optional[Document]:
        """Load a template as a Document object"""
        template_id = template_id or self.current_template
        template_path = self._get_template_path(template_id)
        
        if os.path.exists(template_path):
            try:
                return Document(template_path)
            except Exception as e:
                print(f"Error loading template: {e}")
        
        # Return new document if template file doesn't exist
        return Document()
    
    def save_template(self, document: Document, template_id: str) -> bool:
        """Save a document as a template"""
        template_path = self._get_template_path(template_id)
        
        try:
            document.save(template_path)
            return True
        except Exception as e:
            print(f"Error saving template: {e}")
            return False
    
    def upload_template(self, file_path: str, template_id: str) -> bool:
        """Upload a custom template file"""
        if not os.path.exists(file_path):
            return False
        
        template_path = self._get_template_path(template_id)
        
        try:
            shutil.copy2(file_path, template_path)
            
            # Add to available templates if new
            if template_id not in self.AVAILABLE_TEMPLATES:
                self.AVAILABLE_TEMPLATES[template_id] = {
                    'name': template_id.replace('_', ' ').title(),
                    'description': 'Custom uploaded template',
                    'page_size': 'A4',
                    'margins': {'top': 2.5, 'bottom': 2.5, 'left': 2.5, 'right': 2.5}
                }
            
            return True
        except Exception as e:
            print(f"Error uploading template: {e}")
            return False
    
    def get_template_styles(self, template_id: str = None) -> Dict:
        """Get style settings for a template"""
        template_id = template_id or self.current_template
        
        # Default Springer LNCS styles
        if template_id == 'springer_lncs':
            return {
                'title': {
                    'font': 'Times New Roman',
                    'size': 14,
                    'bold': True,
                    'alignment': 'center'
                },
                'author': {
                    'font': 'Times New Roman',
                    'size': 11,
                    'alignment': 'center'
                },
                'abstract': {
                    'font': 'Times New Roman',
                    'size': 10,
                    'italic': True,
                    'prefix': 'Abstract.'
                },
                'heading1': {
                    'font': 'Times New Roman',
                    'size': 12,
                    'bold': True
                },
                'heading2': {
                    'font': 'Times New Roman',
                    'size': 11,
                    'bold': True
                },
                'body': {
                    'font': 'Times New Roman',
                    'size': 11,
                    'line_spacing': 1.0
                },
                'caption': {
                    'font': 'Times New Roman',
                    'size': 10,
                    'alignment': 'center'
                },
                'reference': {
                    'font': 'Times New Roman',
                    'size': 9
                }
            }
        
        elif template_id == 'ieee':
            return {
                'title': {
                    'font': 'Times New Roman',
                    'size': 24,
                    'bold': True,
                    'alignment': 'center'
                },
                'author': {
                    'font': 'Times New Roman',
                    'size': 11,
                    'alignment': 'center'
                },
                'abstract': {
                    'font': 'Times New Roman',
                    'size': 9,
                    'bold_prefix': True,
                    'prefix': 'Abstract—'
                },
                'heading1': {
                    'font': 'Times New Roman',
                    'size': 10,
                    'bold': True,
                    'uppercase': True
                },
                'body': {
                    'font': 'Times New Roman',
                    'size': 10,
                    'columns': 2
                }
            }
        
        elif template_id == 'acm':
            return {
                'title': {
                    'font': 'Linux Libertine',
                    'size': 18,
                    'bold': True,
                    'alignment': 'center'
                },
                'author': {
                    'font': 'Linux Libertine',
                    'size': 11,
                    'alignment': 'center'
                },
                'body': {
                    'font': 'Linux Libertine',
                    'size': 10,
                    'columns': 2
                }
            }
        
        # Default styles
        return {
            'title': {'font': 'Times New Roman', 'size': 14, 'bold': True},
            'body': {'font': 'Times New Roman', 'size': 11}
        }
    
    def _get_template_path(self, template_id: str) -> str:
        """Get the file path for a template"""
        return os.path.join(self.templates_dir, f"{template_id}.docx")
    
    def _template_file_exists(self, template_id: str) -> bool:
        """Check if a template file exists"""
        return os.path.exists(self._get_template_path(template_id))


# Global template manager instance
_template_manager = None


def get_template_manager(templates_dir: str = None) -> TemplateManager:
    """Get or create the global template manager"""
    global _template_manager
    if _template_manager is None:
        _template_manager = TemplateManager(templates_dir)
    return _template_manager
