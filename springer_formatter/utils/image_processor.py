"""
Image Processor for Springer LNCS Formatter
Processes images to meet Springer publication standards
"""

import os
from PIL import Image
from typing import Dict, List, Optional, Tuple
import re


class ImageProcessor:
    """Process images for Springer LNCS format"""
    
    # Springer requirements
    MIN_DPI = 300
    MAX_WIDTH_CM = 14  # Maximum width for figures
    SUPPORTED_FORMATS = ['.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp']
    
    def __init__(self, output_dir: str = None):
        self.output_dir = output_dir or 'processed_images'
        self.processed_images = []
        self.warnings = []
        
        # Create output directory if needed
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def process_image(self, image_path: str, target_width_cm: float = 12) -> Dict:
        """Process a single image"""
        if not os.path.exists(image_path):
            return {'success': False, 'error': f'File not found: {image_path}'}
        
        try:
            img = Image.open(image_path)
            original_size = img.size
            original_mode = img.mode
            
            result = {
                'original_path': image_path,
                'original_size': original_size,
                'original_mode': original_mode
            }
            
            # Check and convert color mode
            if img.mode == 'RGBA':
                # Convert RGBA to RGB (with white background)
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])
                img = background
            elif img.mode not in ['RGB', 'L', 'CMYK']:
                img = img.convert('RGB')
            
            # Calculate target size
            dpi = self._get_dpi(img)
            target_width_px = int((target_width_cm / 2.54) * dpi)
            
            # Resize if necessary
            if img.width > target_width_px:
                ratio = target_width_px / img.width
                new_height = int(img.height * ratio)
                img = img.resize((target_width_px, new_height), Image.Resampling.LANCZOS)
                result['resized'] = True
                result['new_size'] = img.size
            else:
                result['resized'] = False
                result['new_size'] = img.size
            
            # Check DPI
            current_dpi = self._get_dpi(img)
            if current_dpi < self.MIN_DPI:
                self.warnings.append(f"Image {os.path.basename(image_path)} has low DPI ({current_dpi}). Recommended: {self.MIN_DPI}+")
                result['dpi_warning'] = True
            
            # Generate output filename
            base_name = os.path.splitext(os.path.basename(image_path))[0]
            output_filename = f"fig_{len(self.processed_images) + 1}_{base_name}.png"
            output_path = os.path.join(self.output_dir, output_filename)
            
            # Save processed image
            img.save(output_path, 'PNG', dpi=(300, 300))
            
            result['success'] = True
            result['processed_path'] = output_path
            result['figure_number'] = len(self.processed_images) + 1
            
            self.processed_images.append(result)
            
            return result
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def process_folder(self, folder_path: str, target_width_cm: float = 12) -> List[Dict]:
        """Process all images in a folder"""
        results = []
        
        if not os.path.exists(folder_path):
            return [{'success': False, 'error': f'Folder not found: {folder_path}'}]
        
        # Get all image files
        image_files = []
        for file in os.listdir(folder_path):
            ext = os.path.splitext(file)[1].lower()
            if ext in self.SUPPORTED_FORMATS:
                image_files.append(os.path.join(folder_path, file))
        
        # Sort files naturally
        image_files.sort(key=self._natural_sort_key)
        
        # Process each image
        for image_path in image_files:
            result = self.process_image(image_path, target_width_cm)
            results.append(result)
        
        return results
    
    def process_image_list(self, image_paths: List[str], target_width_cm: float = 12) -> List[Dict]:
        """Process a list of image files"""
        results = []
        
        for image_path in image_paths:
            result = self.process_image(image_path, target_width_cm)
            results.append(result)
        
        return results
    
    def generate_caption(self, image_path: str, figure_number: int = None) -> str:
        """Generate a caption from filename"""
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        
        # Clean up the filename
        caption = base_name.replace('_', ' ').replace('-', ' ')
        caption = re.sub(r'^fig\s*\d*\s*', '', caption, flags=re.IGNORECASE)
        caption = re.sub(r'^\d+\s*', '', caption)
        caption = caption.strip().capitalize()
        
        if not caption:
            caption = f"Figure description"
        
        return caption
    
    def get_images_data(self) -> List[Dict]:
        """Get processed images data for document insertion"""
        images_data = []
        
        for i, img_info in enumerate(self.processed_images, 1):
            if img_info.get('success'):
                caption = self.generate_caption(img_info['original_path'], i)
                images_data.append({
                    'path': img_info['processed_path'],
                    'caption': caption,
                    'number': i,
                    'width': 5.5,  # inches for docx
                    'original_path': img_info['original_path']
                })
        
        return images_data
    
    def _get_dpi(self, img: Image.Image) -> int:
        """Get image DPI"""
        try:
            dpi = img.info.get('dpi', (72, 72))
            return int(dpi[0]) if isinstance(dpi, tuple) else int(dpi)
        except:
            return 72  # Default DPI
    
    def _natural_sort_key(self, s: str) -> List:
        """Natural sort key for filenames"""
        return [int(text) if text.isdigit() else text.lower()
                for text in re.split(r'(\d+)', s)]
    
    def get_processing_summary(self) -> Dict:
        """Get summary of image processing"""
        successful = sum(1 for img in self.processed_images if img.get('success'))
        failed = len(self.processed_images) - successful
        
        return {
            'total_processed': len(self.processed_images),
            'successful': successful,
            'failed': failed,
            'warnings': self.warnings,
            'output_directory': self.output_dir
        }
    
    def validate_image(self, image_path: str) -> Dict:
        """Validate an image against Springer requirements"""
        validation = {
            'path': image_path,
            'valid': True,
            'issues': []
        }
        
        if not os.path.exists(image_path):
            validation['valid'] = False
            validation['issues'].append('File not found')
            return validation
        
        try:
            img = Image.open(image_path)
            
            # Check format
            ext = os.path.splitext(image_path)[1].lower()
            if ext not in self.SUPPORTED_FORMATS:
                validation['issues'].append(f'Unsupported format: {ext}')
            
            # Check DPI
            dpi = self._get_dpi(img)
            if dpi < self.MIN_DPI:
                validation['issues'].append(f'Low resolution: {dpi} DPI (recommended: {self.MIN_DPI}+)')
            
            # Check size
            width_cm = (img.width / dpi) * 2.54
            if width_cm > self.MAX_WIDTH_CM:
                validation['issues'].append(f'Image too wide: {width_cm:.1f}cm (max: {self.MAX_WIDTH_CM}cm)')
            
            # Check color mode
            if img.mode not in ['RGB', 'L', 'CMYK', 'RGBA']:
                validation['issues'].append(f'Unusual color mode: {img.mode}')
            
            validation['width'] = img.width
            validation['height'] = img.height
            validation['dpi'] = dpi
            validation['mode'] = img.mode
            
            if validation['issues']:
                validation['valid'] = False
            
        except Exception as e:
            validation['valid'] = False
            validation['issues'].append(f'Error reading image: {str(e)}')
        
        return validation


def process_images_for_document(image_paths: List[str], output_dir: str) -> List[Dict]:
    """Convenience function to process images for document insertion"""
    processor = ImageProcessor(output_dir)
    processor.process_image_list(image_paths)
    return processor.get_images_data()
