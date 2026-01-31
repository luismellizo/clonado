import asyncio
import os
import re
import json
import hashlib
from urllib.parse import urljoin, urlparse, unquote
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import aiofiles
import logging

from app.analyzer import WebAnalyzer, generate_analysis_report
from app.validator import ResourceValidator
from app.optimizer import ResourceOptimizer
from app.fallback import FallbackManager
from app.quality import QualityScorer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ClonerPro:
    """Professional web cloner with organized output structure and quality assurance."""
    
    def __init__(self, url, job_id, output_base_dir="downloads"):
        self.url = url
        self.job_id = job_id
        self.output_dir = os.path.join(output_base_dir, job_id)
        
        # Professional folder structure
        self.dirs = {
            'images': os.path.join(self.output_dir, "assets", "images"),
            'fonts': os.path.join(self.output_dir, "assets", "fonts"),
            'icons': os.path.join(self.output_dir, "assets", "icons"),
            'css': os.path.join(self.output_dir, "css"),
            'js': os.path.join(self.output_dir, "js"),
        }
        
        # Ensure directories exist
        for dir_path in self.dirs.values():
            os.makedirs(dir_path, exist_ok=True)
        
        # Track downloaded resources to avoid duplicates
        self.downloaded = set()
        self.analysis_data = None
        
        # Helpers
        self.fallback_manager = FallbackManager()
        self.validator = ResourceValidator()
        self.optimizer = ResourceOptimizer()
        
    async def capture_site(self):
        """Main capture process."""
        logger.info(f"🚀 Starting capture for {self.url} (Job ID: {self.job_id})")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={'width': 1920, 'height': 1080},
                locale="en-US"
            )
            
            page = await context.new_page()
            
            try:
                # 1. Navigate with extended timeout
                logger.info("📡 Navigating to URL...")
                await page.goto(self.url, wait_until="networkidle", timeout=120000)
                
                # 2. Auto-scroll for lazy loading
                logger.info("📜 Auto-scrolling to trigger lazy load...")
                await self.auto_scroll(page)
                
                # 3. Get fully rendered HTML
                content = await page.content()
                
                # 4. Run analysis
                logger.info("🔍 Analyzing technologies and SEO...")
                analyzer = WebAnalyzer(content, self.url)
                self.analysis_data = analyzer.analyze()
                
                # 5. Process and download all assets
                logger.info("📥 Processing and downloading assets...")
                cleaned_html = await self.process_page(page, content)
                
                # 6. Save index.html
                async with aiofiles.open(os.path.join(self.output_dir, "index.html"), "w", encoding="utf-8") as f:
                    await f.write(cleaned_html)
                
                # 7. Run Quality Assurance
                logger.info("🌟 Running Quality Assurance...")
                scorer = QualityScorer(self.output_dir)
                quality_data = await scorer.analyze_quality()
                self.analysis_data['quality'] = quality_data
                
                # 8. Generate reports
                logger.info("📋 Generating analysis reports...")
                await self.generate_reports(scorer)
                
                logger.info("✅ Capture completed successfully!")
                
            except Exception as e:
                logger.error(f"❌ Error capturing site: {e}")
                raise e
            finally:
                await browser.close()
    
    async def auto_scroll(self, page):
        """Scroll page to trigger lazy loading."""
        await page.evaluate("""
            async () => {
                await new Promise((resolve) => {
                    var totalHeight = 0;
                    var distance = 200;
                    var timer = setInterval(() => {
                        var scrollHeight = document.body.scrollHeight;
                        window.scrollBy(0, distance);
                        totalHeight += distance;

                        if(totalHeight >= scrollHeight - window.innerHeight){
                            clearInterval(timer);
                            window.scrollTo(0, 0);
                            resolve();
                        }
                    }, 50);
                });
            }
        """)
        await page.wait_for_timeout(1500)
    
    async def process_page(self, page, html_content):
        """Process HTML and download all assets."""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 1. Remove trackers
        self.remove_trackers(soup)
        
        # 2. Neutralize forms
        self.neutralize_forms(soup)

        # 2.1 Remove base tag to force local resolution
        for base in soup.find_all('base'):
            base.decompose()
        
        # 3. Download and rewrite images
        await self.process_images(page, soup)
        
        # 4. Download and rewrite CSS
        await self.process_css(page, soup)
        
        # 5. Download and rewrite JS (optional scripts)
        await self.process_js(page, soup)
        
        # 6. Download fonts referenced in CSS
        await self.process_fonts(page, soup)
        
        # 7. Download favicon and icons
        await self.process_icons(page, soup)
        
        # 8. Clean inline styles with external URLs
        self.clean_inline_styles(soup)
        
        return str(soup)
    
    def remove_trackers(self, soup):
        """Remove tracking scripts and pixels."""
        trackers = [
            re.compile(r'facebook', re.I),
            re.compile(r'google-analytics', re.I),
            re.compile(r'googletagmanager', re.I),
            re.compile(r'gtag', re.I),
            re.compile(r'hotjar', re.I),
            re.compile(r'tiktok', re.I),
            re.compile(r'clarity\.ms', re.I),
            re.compile(r'segment\.com', re.I),
            re.compile(r'mixpanel', re.I),
            re.compile(r'amplitude', re.I),
            re.compile(r'intercom', re.I),
            re.compile(r'crisp\.chat', re.I),
            re.compile(r'hubspot', re.I),
        ]
        
        for t in trackers:
            # Script src
            for s in soup.find_all('script', src=t): s.decompose()
            # Iframe src
            for i in soup.find_all('iframe', src=t): i.decompose()
        
        # Inline scripts
        for script in soup.find_all('script', src=False):
            if script.string and any(t.search(script.string) for t in trackers):
                script.decompose()

    def neutralize_forms(self, soup):
        """Neutralize all forms."""
        forms = soup.find_all('form')
        for form in forms:
            form['action'] = '#'
            form['method'] = 'GET'
            form['onsubmit'] = 'event.preventDefault(); return false;'
    
    async def download_resource(self, page, url, save_path, resource_type='auto'):
        """Smart download with Validation, Fallback, and Optimization."""
        if url in self.downloaded:
            return True
        
        try:
            # 1. Try Primary Download
            content = await self._fetch_content(page, url)
            
            # 2. Fallback if failed
            if not content:
                cdn_url = self.fallback_manager.get_cdn_url(url)
                if cdn_url:
                    logger.info(f"🔄 Trying CDN fallback for {url}")
                    content = await self._fetch_content(page, cdn_url)
            
            if not content:
                logger.warning(f"❌ Failed to download {url} (Refusing content)")
                # Final rescue: Create placeholder?
                # Dependent on strictness. For now return False to trigger logic placeholders if needed.
                return False

            # 3. Validate
            is_valid = True
            if resource_type == 'image':
                is_valid = self.validator.is_valid_image(content, url)
            elif resource_type == 'css':
                is_valid = self.validator.is_valid_css(content)
            elif resource_type == 'js':
                is_valid = self.validator.is_valid_js(content)
            
            if not is_valid:
                logger.warning(f"⚠️ Validation failed for {url} ({resource_type})")
                return False

            # 4. Save & Optimize
            self.downloaded.add(url)
            
            # Save temp for optimization
            async with aiofiles.open(save_path, "wb") as f:
                await f.write(content)
                
            # Optimize in place
            if resource_type == 'image':
                await self.optimizer.optimize_image(save_path)
            elif resource_type == 'css':
                await self.optimizer.minify_css(save_path)
            elif resource_type == 'js':
                await self.optimizer.minify_js(save_path)
                
            return True

        except Exception as e:
            logger.warning(f"⚠️ Error downloading {url}: {e}")
            return False

    async def _fetch_content(self, page, url):
        """Raw fetch helper."""
        try:
            response = await page.request.get(url, timeout=30000)
            if response.status == 200:
                return await response.body()
        except:
            pass
        return None

    def sanitize_filename(self, url: str, default_ext: str = '') -> str:
        """Generate a clean, readable filename."""
        parsed = urlparse(url)
        path = unquote(parsed.path)
        filename = os.path.basename(path)
        
        if not filename or len(filename) > 100:
            hash_part = hashlib.md5(url.encode()).hexdigest()[:8]
            filename = f"resource_{hash_part}{default_ext}"
        
        filename = re.sub(r'[^\w\-_\.]', '_', filename)
        
        if default_ext and not any(filename.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.ico', '.css', '.js', '.woff', '.woff2', '.ttf']):
            filename += default_ext
        
        return filename
    
    async def process_images(self, page, soup):
        """Download images."""
        for img in soup.find_all('img', src=True):
            src = img.get('src', '').strip()
            if not src or src.startswith('data:'): continue
            
            absolute_url = urljoin(self.url, src)
            filename = self.sanitize_filename(absolute_url, '.jpg')
            save_path = os.path.join(self.dirs['images'], filename)
            
            success = await self.download_resource(page, absolute_url, save_path, 'image')
            
            if success:
                img['src'] = f"assets/images/{filename}"
                if img.has_attr('srcset'): del img['srcset']
                if img.has_attr('data-src'): del img['data-src']
            else:
                # Fallback placeholder?
                # img['src'] = "assets/images/placeholder.svg"
                pass  # Keep original src or broken link? Better broken than fake sometimes, but we promised quality.
                # Let's leave it for now to avoid altering layout too much if we don't have a good placeholder

    async def process_css(self, page, soup):
        """Download CSS."""
        for link in soup.find_all('link', rel="stylesheet", href=True):
            href = link.get('href', '').strip()
            if not href: continue
            
            absolute_url = urljoin(self.url, href)
            filename = self.sanitize_filename(absolute_url, '.css')
            save_path = os.path.join(self.dirs['css'], filename)
            
            if await self.download_resource(page, absolute_url, save_path, 'css'):
                # Process internal URLs
                await self.process_css_urls(page, save_path, absolute_url)
                link['href'] = f"css/{filename}"

    async def process_css_urls(self, page, css_path: str, base_url: str):
        """Process URLs inside CSS files."""
        try:
            async with aiofiles.open(css_path, 'r', encoding='utf-8', errors='ignore') as f:
                css_content = await f.read()
            
            urls = re.findall(r'url\(["\']?([^"\')\s]+)["\']?\)', css_content)
            modified = False
            
            for url_match in urls:
                if url_match.startswith('data:') or url_match.startswith('#'): continue
                
                absolute_url = urljoin(base_url, url_match)
                
                # Determine type
                filename = self.sanitize_filename(absolute_url)
                if any(x in url_match.lower() for x in ['.woff', '.ttf', '.otf']):
                    save_path = os.path.join(self.dirs['fonts'], filename)
                    rel_path = f"../assets/fonts/{filename}"
                    rtype = 'font'
                elif any(x in url_match.lower() for x in ['.jpg', '.png', '.svg']):
                    save_path = os.path.join(self.dirs['images'], filename)
                    rel_path = f"../assets/images/{filename}"
                    rtype = 'image'
                else:
                    continue
                
                if await self.download_resource(page, absolute_url, save_path, rtype):
                    css_content = css_content.replace(url_match, rel_path)
                    modified = True
            
            if modified:
                async with aiofiles.open(css_path, 'w', encoding='utf-8') as f:
                    await f.write(css_content)
        except Exception:
            pass

    async def process_js(self, page, soup):
        """Download JS."""
        trackers = ['google', 'facebook', 'analytics', 'gtag', 'hotjar']
        
        for script in soup.find_all('script', src=True):
            src = script.get('src', '').strip()
            if not src or any(t in src.lower() for t in trackers): continue
            
            absolute_url = urljoin(self.url, src)
            filename = self.sanitize_filename(absolute_url, '.js')
            save_path = os.path.join(self.dirs['js'], filename)
            
            if await self.download_resource(page, absolute_url, save_path, 'js'):
                script['src'] = f"js/{filename}"

    async def process_fonts(self, page, soup):
        for link in soup.find_all('link', rel="preload", href=True):
            if link.get('as') == 'font':
                href = link.get('href', '').strip()
                absolute_url = urljoin(self.url, href)
                filename = self.sanitize_filename(absolute_url, '.woff2')
                save_path = os.path.join(self.dirs['fonts'], filename)
                
                if await self.download_resource(page, absolute_url, save_path, 'font'):
                    link['href'] = f"assets/fonts/{filename}"

    async def process_icons(self, page, soup):
        icon_rels = ['icon', 'shortcut icon', 'apple-touch-icon']
        for link in soup.find_all('link', href=True):
            if any(r in (link.get('rel') or []) for r in icon_rels):
                href = link.get('href', '').strip()
                absolute_url = urljoin(self.url, href)
                filename = self.sanitize_filename(absolute_url, '.ico')
                save_path = os.path.join(self.dirs['icons'], filename)
                if await self.download_resource(page, absolute_url, save_path, 'image'):
                    link['href'] = f"assets/icons/{filename}"

    def clean_inline_styles(self, soup):
        pass # Optional cleanup

    async def generate_reports(self, scorer):
        """Generate reports."""
        if not self.analysis_data: return
        
        # Base Analysis Report
        report_md = generate_analysis_report(self.analysis_data)
        
        # Quality Report
        quality_md = await scorer.generate_report()
        
        # Combine
        full_report = report_md + "\n\n" + quality_md
        
        async with aiofiles.open(os.path.join(self.output_dir, "ANALYSIS.md"), "w", encoding="utf-8") as f:
            await f.write(full_report)
        
        async with aiofiles.open(os.path.join(self.output_dir, "analysis.json"), "w", encoding="utf-8") as f:
            await f.write(json.dumps(self.analysis_data, indent=2, ensure_ascii=False))
        
    def get_analysis(self) -> dict:
        return self.analysis_data
