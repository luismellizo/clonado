"""
Resource Optimizer Module
Optimizes images, CSS, and JS for production-ready performance.
"""
import logging
import os
import aiofiles
import re

logger = logging.getLogger(__name__)

class ResourceOptimizer:
    """Optimizes web resources."""
    
    @staticmethod
    async def optimize_image(input_path: str, output_path: str = None) -> bool:
        """Compress and optimize images using Pillow."""
        if not output_path:
            output_path = input_path
            
        try:
            from PIL import Image
            
            # Open image
            with Image.open(input_path) as img:
                
                # Convert RGBA to RGB for JPEG compatibility if needed
                if img.mode == 'RGBA' and output_path.lower().endswith(('.jpg', '.jpeg')):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3])
                    img = background
                
                # Resize if massive (> 2500px)
                max_dimension = 2500
                if max(img.size) > max_dimension:
                    ratio = max_dimension / max(img.size)
                    new_size = tuple(int(dim * ratio) for dim in img.size)
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # Save optimized
                save_kwargs = {'optimize': True}
                
                if output_path.lower().endswith(('.jpg', '.jpeg')):
                    save_kwargs['quality'] = 80
                    img.save(output_path, 'JPEG', **save_kwargs)
                    
                elif output_path.lower().endswith('.png'):
                    # PNG compression level (default is 6, max 9)
                    save_kwargs['compress_level'] = 9 
                    img.save(output_path, 'PNG', **save_kwargs)
                    
                elif output_path.lower().endswith('.webp'):
                    save_kwargs['quality'] = 80
                    img.save(output_path, 'WEBP', **save_kwargs)
                else:
                    # Just save if format not specially handled
                    img.save(output_path)
                    
            return True
        except Exception as e:
            logger.warning(f"⚠️ Image optimization failed for {os.path.basename(input_path)}: {e}")
            return False
    
    @staticmethod
    async def minify_css(input_path: str, output_path: str = None) -> bool:
        """Minify CSS content."""
        if not output_path:
            output_path = input_path
            
        try:
            import csscompressor
            
            async with aiofiles.open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = await f.read()
            
            minified = csscompressor.compress(content)
            
            if minified and len(minified) < len(content):
                async with aiofiles.open(output_path, 'w', encoding='utf-8') as f:
                    await f.write(minified)
                return True
                
        except ImportError:
            logger.warning("csscompressor not installed, skipping minification")
        except Exception as e:
            logger.warning(f"⚠️ CSS minification failed: {e}")
            
            # Fallback: simple regex minification
            try:
                async with aiofiles.open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = await f.read()
                
                # Remove comments
                compact = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
                # Collapse whitespace
                compact = re.sub(r'\s+', ' ', compact)
                # Remove spaces around punctuation
                compact = re.sub(r'\s*([:;{}])\s*', r'\1', compact)
                
                async with aiofiles.open(output_path, 'w', encoding='utf-8') as f:
                    await f.write(compact)
                return True
            except:
                pass
                
        return False

    @staticmethod
    async def minify_js(input_path: str, output_path: str = None) -> bool:
        """Simple JS minification/cleanup."""
        if not output_path:
            output_path = input_path
            
        try:
            async with aiofiles.open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = await f.read()
            
            # Very basic minification safety: just remove big comment blocks and excessive whitespace
            # Full JS minification is risky without a parser like Terser, so we play it safe
            
            # Remove multi-line comments
            compact = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
            
            # We DONT remove line breaks in JS to avoid breaking missing semicolon code
            
            # Only save if we actually reduced size
            if len(compact) < len(content):
                async with aiofiles.open(output_path, 'w', encoding='utf-8') as f:
                    await f.write(compact)
                return True
                
        except Exception as e:
            logger.warning(f"⚠️ JS cleanup failed: {e}")
            
        return False
