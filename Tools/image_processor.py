#!/usr/bin/env python3
"""
OpenLLM Toolkit - Image Processing and Vision
Provides image reading, analysis, and text extraction capabilities
"""

import os
import io
import base64
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import tempfile

logger = logging.getLogger(__name__)

# Optional imports with fallbacks
try:
    from PIL import Image, ImageEnhance, ImageFilter
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("PIL/Pillow not available. Install with: pip install Pillow")

try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    logger.warning("OpenCV not available. Install with: pip install opencv-python")

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logger.warning("Tesseract not available. Install with: pip install pytesseract")

class ImageFormat(Enum):
    """Supported image formats"""
    JPEG = "jpeg"
    PNG = "png"
    GIF = "gif"
    BMP = "bmp"
    WEBP = "webp"
    TIFF = "tiff"
    SVG = "svg"

class AnalysisType(Enum):
    """Types of image analysis"""
    BASIC_INFO = "basic_info"
    TEXT_EXTRACTION = "text_extraction"
    OBJECT_DETECTION = "object_detection"
    SCENE_DESCRIPTION = "scene_description"
    COLOR_ANALYSIS = "color_analysis"
    QUALITY_ASSESSMENT = "quality_assessment"

@dataclass
class ImageInfo:
    """Image information structure"""
    path: str
    format: ImageFormat
    width: int
    height: int
    size_bytes: int
    color_mode: str
    has_transparency: bool
    is_animated: bool = False
    frames: int = 1
    dpi: Optional[Tuple[int, int]] = None

@dataclass
class TextExtraction:
    """Extracted text information"""
    text: str
    confidence: float
    bounding_boxes: List[Dict[str, Any]]
    language: Optional[str] = None
    orientation: Optional[float] = None

@dataclass
class ColorAnalysis:
    """Color analysis results"""
    dominant_colors: List[Tuple[int, int, int]]
    color_palette: List[str]
    brightness: float
    contrast: float
    saturation: float
    temperature: str  # "warm" or "cool"

@dataclass
class ImageAnalysisResult:
    """Complete image analysis result"""
    success: bool
    message: str
    image_info: Optional[ImageInfo] = None
    text_extraction: Optional[TextExtraction] = None
    color_analysis: Optional[ColorAnalysis] = None
    scene_description: Optional[str] = None
    objects_detected: Optional[List[Dict]] = None
    quality_score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

class ImageProcessor:
    """Main image processing class"""
    
    def __init__(self):
        self.max_image_size = 20 * 1024 * 1024  # 20MB limit
        self.max_dimensions = (4096, 4096)
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif', '.svg'}
        
        # Check available capabilities
        self.capabilities = {
            'basic_processing': PIL_AVAILABLE,
            'advanced_processing': OPENCV_AVAILABLE,
            'text_extraction': TESSERACT_AVAILABLE,
            'vision_models': True  # Will be available through LLM providers
        }
    
    def is_image_file(self, file_path: str) -> bool:
        """Check if file is a supported image format"""
        extension = Path(file_path).suffix.lower()
        return extension in self.supported_formats
    
    def get_image_info(self, image_path: str) -> ImageInfo:
        """Extract basic image information"""
        if not PIL_AVAILABLE:
            raise Exception("PIL/Pillow required for image processing")
        
        path = Path(image_path)
        if not path.exists():
            raise Exception("Image file not found")
        
        try:
            with Image.open(path) as img:
                # Determine format
                format_map = {
                    'JPEG': ImageFormat.JPEG,
                    'PNG': ImageFormat.PNG,
                    'GIF': ImageFormat.GIF,
                    'BMP': ImageFormat.BMP,
                    'WEBP': ImageFormat.WEBP,
                    'TIFF': ImageFormat.TIFF
                }
                img_format = format_map.get(img.format, ImageFormat.JPEG)
                
                # Basic properties
                width, height = img.size
                size_bytes = path.stat().st_size
                color_mode = img.mode
                has_transparency = 'transparency' in img.info or color_mode in ('RGBA', 'LA')
                
                # Animation info for GIFs
                is_animated = hasattr(img, 'is_animated') and img.is_animated
                frames = getattr(img, 'n_frames', 1) if is_animated else 1
                
                # DPI info
                dpi = img.info.get('dpi', None)
                
                return ImageInfo(
                    path=str(path),
                    format=img_format,
                    width=width,
                    height=height,
                    size_bytes=size_bytes,
                    color_mode=color_mode,
                    has_transparency=has_transparency,
                    is_animated=is_animated,
                    frames=frames,
                    dpi=dpi
                )
                
        except Exception as e:
            raise Exception(f"Error reading image: {str(e)}")
    
    def encode_image_base64(self, image_path: str, max_size: Optional[Tuple[int, int]] = None) -> str:
        """Encode image as base64 for LLM vision models"""
        if not PIL_AVAILABLE:
            raise Exception("PIL/Pillow required for image encoding")
        
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                # Resize if needed
                if max_size:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Save to bytes
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=85, optimize=True)
                img_bytes = buffer.getvalue()
                
                # Encode as base64
                return base64.b64encode(img_bytes).decode('utf-8')
                
        except Exception as e:
            raise Exception(f"Error encoding image: {str(e)}")
    
    def extract_text_tesseract(self, image_path: str) -> TextExtraction:
        """Extract text using Tesseract OCR"""
        if not TESSERACT_AVAILABLE:
            raise Exception("Tesseract OCR not available")
        
        try:
            # Load image
            image = Image.open(image_path)
            
            # Preprocess image for better OCR
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Enhance image quality
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)
            
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(2.0)
            
            # Extract text with detailed info
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            # Filter out low-confidence text
            text_parts = []
            bounding_boxes = []
            confidences = []
            
            for i in range(len(data['text'])):
                text = data['text'][i].strip()
                conf = float(data['conf'][i])
                
                if text and conf > 30:  # Filter low confidence
                    text_parts.append(text)
                    confidences.append(conf)
                    
                    bounding_boxes.append({
                        'text': text,
                        'confidence': conf,
                        'x': data['left'][i],
                        'y': data['top'][i],
                        'width': data['width'][i],
                        'height': data['height'][i]
                    })
            
            # Combine text
            full_text = ' '.join(text_parts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            # Detect language (simple heuristic)
            language = self._detect_language(full_text)
            
            # Detect orientation
            orientation = None
            try:
                osd = pytesseract.image_to_osd(image, output_type=pytesseract.Output.DICT)
                orientation = osd.get('rotate', 0)
            except:
                pass
            
            return TextExtraction(
                text=full_text,
                confidence=avg_confidence,
                bounding_boxes=bounding_boxes,
                language=language,
                orientation=orientation
            )
            
        except Exception as e:
            raise Exception(f"Error extracting text: {str(e)}")
    
    def analyze_colors(self, image_path: str) -> ColorAnalysis:
        """Analyze image colors and properties"""
        if not PIL_AVAILABLE:
            raise Exception("PIL/Pillow required for color analysis")
        
        try:
            with Image.open(image_path) as img:
                # Convert to RGB
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize for faster processing
                img.thumbnail((200, 200), Image.Resampling.LANCZOS)
                
                # Get color statistics
                pixels = list(img.getdata())
                
                # Calculate dominant colors
                from collections import Counter
                color_counts = Counter(pixels)
                dominant_colors = [color for color, count in color_counts.most_common(5)]
                
                # Convert to hex palette
                color_palette = [f"#{r:02x}{g:02x}{b:02x}" for r, g, b in dominant_colors]
                
                # Calculate brightness, contrast, saturation
                brightness = sum(sum(pixel) for pixel in pixels) / (len(pixels) * 3) / 255
                
                # Simple contrast calculation
                grays = [sum(pixel) / 3 for pixel in pixels]
                contrast = (max(grays) - min(grays)) / 255 if grays else 0
                
                # Saturation calculation
                saturations = []
                for r, g, b in pixels:
                    max_val = max(r, g, b)
                    min_val = min(r, g, b)
                    saturation = (max_val - min_val) / max_val if max_val > 0 else 0
                    saturations.append(saturation)
                avg_saturation = sum(saturations) / len(saturations)
                
                # Temperature (warm vs cool)
                avg_r = sum(pixel[0] for pixel in pixels) / len(pixels)
                avg_b = sum(pixel[2] for pixel in pixels) / len(pixels)
                temperature = "warm" if avg_r > avg_b else "cool"
                
                return ColorAnalysis(
                    dominant_colors=dominant_colors,
                    color_palette=color_palette,
                    brightness=brightness,
                    contrast=contrast,
                    saturation=avg_saturation,
                    temperature=temperature
                )
                
        except Exception as e:
            raise Exception(f"Error analyzing colors: {str(e)}")
    
    def assess_quality(self, image_path: str) -> float:
        """Assess image quality (0.0 - 1.0)"""
        if not OPENCV_AVAILABLE:
            # Fallback to basic quality assessment
            return self._basic_quality_assessment(image_path)
        
        try:
            # Load image with OpenCV
            img = cv2.imread(image_path)
            if img is None:
                raise Exception("Could not load image")
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Calculate Laplacian variance (blur detection)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Normalize to 0-1 scale (empirically determined thresholds)
            quality_score = min(1.0, laplacian_var / 1000.0)
            
            return quality_score
            
        except Exception as e:
            logger.warning(f"OpenCV quality assessment failed: {e}")
            return self._basic_quality_assessment(image_path)
    
    def _basic_quality_assessment(self, image_path: str) -> float:
        """Basic quality assessment using PIL"""
        try:
            info = self.get_image_info(image_path)
            
            # Simple heuristics
            score = 0.5  # Base score
            
            # Resolution bonus
            total_pixels = info.width * info.height
            if total_pixels > 1920 * 1080:
                score += 0.2
            elif total_pixels > 1280 * 720:
                score += 0.1
            
            # File size vs resolution ratio
            bytes_per_pixel = info.size_bytes / total_pixels
            if bytes_per_pixel > 2:  # Good compression ratio
                score += 0.2
            
            # Format bonus
            if info.format in [ImageFormat.PNG, ImageFormat.TIFF]:
                score += 0.1
            
            return min(1.0, score)
            
        except Exception:
            return 0.5  # Default score
    
    def _detect_language(self, text: str) -> Optional[str]:
        """Simple language detection"""
        if not text:
            return None
        
        # Very basic heuristics
        text_lower = text.lower()
        
        # Check for common English words
        english_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        english_count = sum(1 for word in english_words if word in text_lower)
        
        if english_count >= 2:
            return 'en'
        
        # Check for numbers/digits
        if any(char.isdigit() for char in text):
            return 'numeric'
        
        return 'unknown'
    
    async def analyze_with_vision_model(self, image_path: str, prompt: str = "Describe this image") -> str:
        """Analyze image using LLM vision models"""
        try:
            # Import LLM manager
            from ..Core.llm_manager import llm_manager, LLMRequest
            
            # Encode image
            base64_image = self.encode_image_base64(image_path, max_size=(1024, 1024))
            
            # Create request for vision model
            request = LLMRequest(
                messages=[{"role": "user", "content": prompt}],
                images=[base64_image]
            )
            
            # Generate response
            response = await llm_manager.generate(request)
            return response.content
            
        except Exception as e:
            raise Exception(f"Error analyzing with vision model: {str(e)}")
    
    def comprehensive_analysis(self, image_path: str, analysis_types: List[AnalysisType] = None) -> ImageAnalysisResult:
        """Perform comprehensive image analysis"""
        if analysis_types is None:
            analysis_types = [
                AnalysisType.BASIC_INFO,
                AnalysisType.COLOR_ANALYSIS,
                AnalysisType.QUALITY_ASSESSMENT
            ]
        
        try:
            result = ImageAnalysisResult(success=True, message="Analysis completed")
            
            # Basic info (always included)
            if AnalysisType.BASIC_INFO in analysis_types:
                result.image_info = self.get_image_info(image_path)
            
            # Text extraction
            if AnalysisType.TEXT_EXTRACTION in analysis_types and TESSERACT_AVAILABLE:
                try:
                    result.text_extraction = self.extract_text_tesseract(image_path)
                except Exception as e:
                    logger.warning(f"Text extraction failed: {e}")
            
            # Color analysis
            if AnalysisType.COLOR_ANALYSIS in analysis_types:
                try:
                    result.color_analysis = self.analyze_colors(image_path)
                except Exception as e:
                    logger.warning(f"Color analysis failed: {e}")
            
            # Quality assessment
            if AnalysisType.QUALITY_ASSESSMENT in analysis_types:
                try:
                    result.quality_score = self.assess_quality(image_path)
                except Exception as e:
                    logger.warning(f"Quality assessment failed: {e}")
            
            # Add metadata
            result.metadata = {
                'capabilities_used': {
                    'pil': PIL_AVAILABLE,
                    'opencv': OPENCV_AVAILABLE,
                    'tesseract': TESSERACT_AVAILABLE
                },
                'analysis_types': [t.value for t in analysis_types]
            }
            
            return result
            
        except Exception as e:
            return ImageAnalysisResult(
                success=False,
                message=f"Analysis failed: {str(e)}"
            )
    
    def create_thumbnail(self, image_path: str, output_path: str, size: Tuple[int, int] = (256, 256)) -> bool:
        """Create thumbnail of image"""
        if not PIL_AVAILABLE:
            raise Exception("PIL/Pillow required for thumbnail creation")
        
        try:
            with Image.open(image_path) as img:
                img.thumbnail(size, Image.Resampling.LANCZOS)
                img.save(output_path, optimize=True, quality=85)
                return True
        except Exception as e:
            logger.error(f"Error creating thumbnail: {e}")
            return False
    
    def batch_process_images(self, image_paths: List[str], analysis_types: List[AnalysisType] = None) -> List[ImageAnalysisResult]:
        """Process multiple images in batch"""
        results = []
        for image_path in image_paths:
            try:
                result = self.comprehensive_analysis(image_path, analysis_types)
                results.append(result)
            except Exception as e:
                results.append(ImageAnalysisResult(
                    success=False,
                    message=f"Failed to process {image_path}: {str(e)}"
                ))
        return results

# Global instance
image_processor = ImageProcessor()

# Convenience functions for beginners
def read_image(image_path: str) -> Dict[str, Any]:
    """Simple image reading for beginners"""
    result = image_processor.comprehensive_analysis(image_path)
    if not result.success:
        raise Exception(result.message)
    
    return {
        'path': result.image_info.path if result.image_info else image_path,
        'width': result.image_info.width if result.image_info else 0,
        'height': result.image_info.height if result.image_info else 0,
        'format': result.image_info.format.value if result.image_info else 'unknown',
        'text': result.text_extraction.text if result.text_extraction else None,
        'colors': result.color_analysis.color_palette if result.color_analysis else [],
        'quality': result.quality_score
    }

def extract_text_from_image(image_path: str) -> str:
    """Simple text extraction for beginners"""
    if not image_processor.capabilities['text_extraction']:
        raise Exception("Text extraction not available. Install: pip install pytesseract")
    
    result = image_processor.extract_text_tesseract(image_path)
    return result.text

async def describe_image(image_path: str, question: str = "What do you see in this image?") -> str:
    """Simple image description for beginners"""
    return await image_processor.analyze_with_vision_model(image_path, question)

if __name__ == "__main__":
    # Example usage
    processor = ImageProcessor()
    
    print(f"Available capabilities: {processor.capabilities}")
    
    # Test with a sample image (if exists)
    test_image = "test_image.jpg"
    if Path(test_image).exists():
        result = processor.comprehensive_analysis(test_image)
        print(f"Analysis result: {result.success}")
        print(f"Message: {result.message}")
    else:
        print("No test image found. Create 'test_image.jpg' to test functionality.")