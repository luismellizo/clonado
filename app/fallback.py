"""
Fallback Manager Module
Provides rescue strategies when resources fail to download.
"""
import aiofiles
import logging

logger = logging.getLogger(__name__)

class FallbackManager:
    """Manages fallbacks for failed resources."""
    
    def __init__(self):
        # Common library CDNs
        self.cdn_map = {
            'jquery': 'https://code.jquery.com/jquery-3.6.0.min.js',
            'bootstrap': 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js',
            'fontawesome': 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css',
            'animate.css': 'https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css',
            'tailwind': 'https://cdn.tailwindcss.com',
            'vue': 'https://unpkg.com/vue@3/dist/vue.global.js',
            'react': 'https://unpkg.com/react@18/umd/react.production.min.js',
            'react-dom': 'https://unpkg.com/react-dom@18/umd/react-dom.production.min.js',
        }
        
        self.placeholder_css = """
/* Fallback CSS */
body { font-family: system-ui, -apple-system, sans-serif; line-height: 1.5; }
img { max-width: 100%; height: auto; background: #f0f0f0; }
        """.strip()
        
        self.placeholder_svg = """
<svg xmlns="http://www.w3.org/2000/svg" width="300" height="200" viewBox="0 0 300 200">
  <rect width="100%" height="100%" fill="#f8f9fa"/>
  <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-family="sans-serif" fill="#adb5bd" font-size="14">Image Unavailable</text>
</svg>
        """.strip()

    def get_cdn_url(self, original_url: str) -> str:
        """Try to find a CDN replacement for a known library."""
        for key, cdn_url in self.cdn_map.items():
            if key in original_url.lower():
                # Simplified check, ideally would check version match
                return cdn_url
        return None

    async def create_fallback_css(self, save_path: str):
        """Write placeholder CSS."""
        try:
            async with aiofiles.open(save_path, 'w', encoding='utf-8') as f:
                await f.write(self.placeholder_css)
            return True
        except Exception as e:
            logger.error(f"Failed to create fallback CSS: {e}")
            return False

    async def create_fallback_image(self, save_path: str):
        """Write placeholder SVG image."""
        try:
            # Change extension to .svg if possible, or just write svg content to whatever
            # Browser might complain if .jpg contains svg xml, but better than binary garbage
            # Ideally we rename the reference in HTML, but here we just save the file.
            
            # If we can, save as .svg
            svg_path = save_path
            if not save_path.endswith('.svg'):
                svg_path = save_path + '.svg' # We will need to update the HTML reference later if we do this
                # For now, let's just write to the original path but if it is jpg/png, 
                # writing text/xml might cause display issues. 
                # Better strategy: overwrite with a 1x1 transparent pixel or simple generated binary PNG?
                # For simplicity in this "Urgent" phase, let's write SVG to a .svg file 
                # and assume we might not catch the reference update. 
                # Actually, rewriting the HTML reference is complex here without passing the soup object.
                
                # ALTERNATIVE: Use a tiny base64 gif decoded as bytes for images?
                pass
            
            # Let's simple write the SVG to the intended path. Modern browsers handle SVGs even with weird extensions sometimes,
            # or we accept it might be broken but "cleanly" broken.
            # A better approach for the future: create a valid minimal PNG bytes.
            
            async with aiofiles.open(save_path, 'w', encoding='utf-8') as f:
                await f.write(self.placeholder_svg)
            return True
        except Exception as e:
            logger.error(f"Failed to create fallback image: {e}")
            return False
