"""
Resource Validator Module
Ensures downloaded content is legitimate and safe.
"""
import logging

logger = logging.getLogger(__name__)

class ResourceValidator:
    """Validates that downloaded resources are legitimate."""
    
    @staticmethod
    def is_valid_image(data: bytes, url: str) -> bool:
        """Verify that content is a real image and not an error page."""
        if not data:
            return False
            
        # Check for HTML disguised as image
        if data.lstrip().startswith(b'<!DOCTYPE') or data.lstrip().startswith(b'<html'):
            return False
        
        # Check magic bytes for common formats
        valid_headers = {
            b'\xff\xd8\xff': 'jpg',
            b'\x89PNG': 'png',
            b'GIF89a': 'gif',
            b'GIF87a': 'gif',
            b'<svg': 'svg',
            b'RIFF': 'webp',
            b'\x00\x00\x01\x00': 'ico'
        }
        
        # SVG check needs to be looser as it's text
        if b'<svg' in data[:100].lower():
            return True
            
        return any(data.startswith(h) for h in valid_headers.keys())
    
    @staticmethod
    def is_valid_css(data: bytes) -> bool:
        """Verify that content is real CSS."""
        if not data:
            return False
            
        try:
            text = data.decode('utf-8', errors='ignore').strip()
            
            # Should not be HTML
            if text.lower().startswith('<!doctype') or '<html' in text.lower():
                return False
            
            # Simple heuristic: CSS usually has braces or @rules
            has_css_syntax = any([
                '{' in text and '}' in text,
                '@import' in text,
                '@media' in text,
                '@font-face' in text,
                'body' in text,
                'color:' in text
            ])
            
            return has_css_syntax if len(text) > 20 else True # Allow small CSS snippets
        except:
            return False
    
    @staticmethod
    def is_valid_js(data: bytes) -> bool:
        """Verify that content is real JavaScript."""
        if not data:
            return False
            
        try:
            text = data.decode('utf-8', errors='ignore').strip()
            
            # Should not be HTML
            if text.lower().startswith('<!doctype') or '<html' in text.lower():
                return False
            
            return True
        except:
            return False
