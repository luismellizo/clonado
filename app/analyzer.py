"""
Web Cloner Elite - Technology & SEO Analyzer
Detects frameworks, CMS, analytics, and performs SEO analysis.
"""

import re
import json
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

# Technology detection patterns
TECH_PATTERNS = {
    "frameworks": {
        "React": [
            r'react(?:\.min)?\.js',
            r'react-dom',
            r'__NEXT_DATA__',
            r'data-reactroot',
            r'_reactRootContainer',
            r'__REACT_DEVTOOLS_GLOBAL_HOOK__'
        ],
        "Vue.js": [
            r'vue(?:\.min)?\.js',
            r'v-app',
            r'data-v-[a-f0-9]',
            r'__VUE__',
            r'Vue\.component'
        ],
        "Angular": [
            r'angular(?:\.min)?\.js',
            r'ng-app',
            r'ng-controller',
            r'ng-version',
            r'\.ng-star-inserted'
        ],
        "Next.js": [
            r'__NEXT_DATA__',
            r'_next/static',
            r'next/dist',
            r'NextJS'
        ],
        "Nuxt.js": [
            r'__NUXT__',
            r'_nuxt/',
            r'nuxt-link'
        ],
        "Svelte": [
            r'svelte(?:\.min)?\.js',
            r'__svelte',
            r'svelte-'
        ],
        "Gatsby": [
            r'gatsby-',
            r'___gatsby',
            r'gatsby-browser'
        ],
        "jQuery": [
            r'jquery(?:\.min)?\.js',
            r'jQuery\(',
            r'\$\(document\)'
        ],
        "Alpine.js": [
            r'alpine(?:\.min)?\.js',
            r'x-data',
            r'x-show',
            r'x-bind'
        ]
    },
    "cms": {
        "WordPress": [
            r'wp-content',
            r'wp-includes',
            r'wp-json',
            r'wordpress',
            r'/wp-admin'
        ],
        "Shopify": [
            r'cdn\.shopify\.com',
            r'shopify\.com',
            r'Shopify\.theme',
            r'myshopify\.com'
        ],
        "Wix": [
            r'wix\.com',
            r'wixstatic\.com',
            r'_wix_browser_sess'
        ],
        "Squarespace": [
            r'squarespace\.com',
            r'static\.squarespace',
            r'sqs-'
        ],
        "Webflow": [
            r'webflow\.com',
            r'wf-[a-z]+-',
            r'w-webflow'
        ],
        "Ghost": [
            r'ghost\.org',
            r'ghost-',
            r'/ghost/api'
        ],
        "Drupal": [
            r'drupal\.js',
            r'/sites/default/',
            r'Drupal\.settings'
        ],
        "Joomla": [
            r'/media/jui/',
            r'joomla',
            r'/components/com_'
        ]
    },
    "css_frameworks": {
        "Tailwind CSS": [
            r'tailwindcss',
            r'tailwind\.min\.css',
            r'class="[^"]*(?:flex|grid|bg-|text-|p-|m-|w-|h-)[^"]*"'
        ],
        "Bootstrap": [
            r'bootstrap(?:\.min)?\.(?:css|js)',
            r'class="[^"]*(?:container|row|col-|btn-|navbar)[^"]*"'
        ],
        "Bulma": [
            r'bulma(?:\.min)?\.css',
            r'class="[^"]*(?:is-|has-|columns|column)[^"]*"'
        ],
        "Foundation": [
            r'foundation(?:\.min)?\.(?:css|js)',
            r'class="[^"]*(?:grid-x|cell|button)[^"]*"'
        ],
        "Material UI": [
            r'@material-ui',
            r'MuiButton',
            r'material-ui'
        ]
    },
    "analytics": {
        "Google Analytics": [
            r'google-analytics\.com',
            r'googletagmanager\.com/gtag',
            r'gtag\(',
            r'ga\(',
            r'UA-\d+-\d+'
        ],
        "Google Tag Manager": [
            r'googletagmanager\.com/gtm',
            r'GTM-[A-Z0-9]+',
            r'dataLayer'
        ],
        "Facebook Pixel": [
            r'connect\.facebook\.net',
            r'fbq\(',
            r'facebook\.com/tr'
        ],
        "Hotjar": [
            r'hotjar\.com',
            r'hj\(',
            r'_hjSettings'
        ],
        "Microsoft Clarity": [
            r'clarity\.ms',
            r'clarity\('
        ],
        "Segment": [
            r'segment\.com',
            r'analytics\.identify',
            r'analytics\.track'
        ],
        "Mixpanel": [
            r'mixpanel\.com',
            r'mixpanel\.'
        ],
        "Amplitude": [
            r'amplitude\.com',
            r'amplitude\.'
        ]
    },
    "cdn": {
        "Cloudflare": [
            r'cdnjs\.cloudflare\.com',
            r'cf-ray',
            r'__cf_'
        ],
        "CloudFront": [
            r'cloudfront\.net'
        ],
        "Fastly": [
            r'fastly\.net',
            r'x-fastly'
        ],
        "Akamai": [
            r'akamaized\.net',
            r'akamai\.net'
        ],
        "jsDelivr": [
            r'cdn\.jsdelivr\.net'
        ],
        "unpkg": [
            r'unpkg\.com'
        ],
        "Google CDN": [
            r'googleapis\.com',
            r'gstatic\.com'
        ]
    },
    "libraries": {
        "Lodash": [r'lodash(?:\.min)?\.js'],
        "Moment.js": [r'moment(?:\.min)?\.js'],
        "GSAP": [r'gsap', r'TweenMax', r'TweenLite'],
        "Three.js": [r'three(?:\.min)?\.js'],
        "D3.js": [r'd3(?:\.min)?\.js', r'd3\.select'],
        "Chart.js": [r'chart(?:\.min)?\.js'],
        "Axios": [r'axios(?:\.min)?\.js'],
        "Swiper": [r'swiper(?:\.min)?\.(?:js|css)'],
        "AOS": [r'aos(?:\.min)?\.(?:js|css)'],
        "Lottie": [r'lottie(?:\.min)?\.js', r'lottie-player'],
        "Animate.css": [r'animate(?:\.min)?\.css'],
        "Font Awesome": [r'fontawesome', r'font-awesome', r'fa-'],
        "Google Fonts": [r'fonts\.googleapis\.com', r'fonts\.gstatic\.com']
    },
    "ecommerce": {
        "Stripe": [r'stripe\.com', r'Stripe\('],
        "PayPal": [r'paypal\.com', r'paypalobjects\.com'],
        "WooCommerce": [r'woocommerce', r'wc-'],
        "BigCommerce": [r'bigcommerce\.com'],
        "Magento": [r'magento', r'/mage/']
    },
    "hosting": {
        "Vercel": [r'vercel\.app', r'\.vercel\.'],
        "Netlify": [r'netlify\.app', r'netlify\.com'],
        "GitHub Pages": [r'github\.io'],
        "Heroku": [r'herokuapp\.com'],
        "AWS": [r'amazonaws\.com', r'aws\.amazon\.com'],
        "Firebase": [r'firebaseapp\.com', r'firebase\.googleapis']
    }
}


class WebAnalyzer:
    """Analyzes web pages for technology stack and SEO metrics."""
    
    def __init__(self, html_content: str, url: str):
        self.html = html_content
        self.url = url
        self.soup = BeautifulSoup(html_content, 'html.parser')
        self.domain = urlparse(url).netloc
        
    def analyze(self) -> Dict[str, Any]:
        """Run full analysis and return results."""
        return {
            "url": self.url,
            "domain": self.domain,
            "technologies": self.detect_technologies(),
            "seo": self.analyze_seo(),
            "meta": self.extract_meta(),
            "social": self.extract_social_meta(),
            "structure": self.analyze_structure(),
            "performance_hints": self.get_performance_hints()
        }
    
    def detect_technologies(self) -> Dict[str, List[str]]:
        """Detect all technologies used on the page."""
        detected = {}
        html_lower = self.html.lower()
        
        for category, techs in TECH_PATTERNS.items():
            found = []
            for tech_name, patterns in techs.items():
                for pattern in patterns:
                    if re.search(pattern, self.html, re.IGNORECASE):
                        if tech_name not in found:
                            found.append(tech_name)
                        break
            if found:
                detected[category] = found
                
        return detected
    
    def analyze_seo(self) -> Dict[str, Any]:
        """Perform SEO analysis."""
        title = self.soup.find('title')
        meta_desc = self.soup.find('meta', attrs={'name': 'description'})
        meta_keywords = self.soup.find('meta', attrs={'name': 'keywords'})
        canonical = self.soup.find('link', attrs={'rel': 'canonical'})
        robots = self.soup.find('meta', attrs={'name': 'robots'})
        
        # Heading analysis
        headings = {
            f"h{i}": [h.get_text(strip=True)[:100] for h in self.soup.find_all(f'h{i}')]
            for i in range(1, 7)
        }
        
        # Image analysis
        images = self.soup.find_all('img')
        images_with_alt = sum(1 for img in images if img.get('alt', '').strip())
        images_without_alt = len(images) - images_with_alt
        
        # Link analysis
        links = self.soup.find_all('a', href=True)
        internal_links = []
        external_links = []
        for link in links:
            href = link['href']
            if href.startswith(('http://', 'https://')):
                if self.domain in href:
                    internal_links.append(href)
                else:
                    external_links.append(href)
            elif href.startswith('/'):
                internal_links.append(href)
        
        # Calculate SEO score
        score = self._calculate_seo_score(
            title, meta_desc, headings, images_with_alt, 
            images_without_alt, canonical
        )
        
        return {
            "score": score,
            "title": {
                "content": title.get_text(strip=True) if title else None,
                "length": len(title.get_text(strip=True)) if title else 0,
                "optimal": 50 <= len(title.get_text(strip=True) if title else '') <= 60
            },
            "description": {
                "content": meta_desc['content'] if meta_desc and meta_desc.get('content') else None,
                "length": len(meta_desc.get('content', '')) if meta_desc else 0,
                "optimal": 150 <= len(meta_desc.get('content', '') if meta_desc else '') <= 160
            },
            "keywords": meta_keywords.get('content') if meta_keywords else None,
            "canonical": canonical['href'] if canonical else None,
            "robots": robots.get('content') if robots else None,
            "headings": {
                "h1_count": len(headings['h1']),
                "h1_content": headings['h1'],
                "structure": {k: len(v) for k, v in headings.items()}
            },
            "images": {
                "total": len(images),
                "with_alt": images_with_alt,
                "without_alt": images_without_alt,
                "alt_percentage": round((images_with_alt / len(images) * 100) if images else 100, 1)
            },
            "links": {
                "internal": len(internal_links),
                "external": len(external_links),
                "total": len(links)
            }
        }
    
    def _calculate_seo_score(self, title, meta_desc, headings, img_with_alt, img_without_alt, canonical) -> int:
        """Calculate SEO score from 0-100."""
        score = 0
        
        # Title (20 points)
        if title:
            title_len = len(title.get_text(strip=True))
            if 50 <= title_len <= 60:
                score += 20
            elif 30 <= title_len <= 70:
                score += 15
            elif title_len > 0:
                score += 10
        
        # Meta description (20 points)
        if meta_desc and meta_desc.get('content'):
            desc_len = len(meta_desc['content'])
            if 150 <= desc_len <= 160:
                score += 20
            elif 100 <= desc_len <= 200:
                score += 15
            elif desc_len > 0:
                score += 10
        
        # H1 (15 points)
        h1_count = len(headings['h1'])
        if h1_count == 1:
            score += 15
        elif h1_count > 1:
            score += 8
        
        # Heading structure (10 points)
        if len(headings['h2']) > 0:
            score += 5
        if len(headings['h3']) > 0:
            score += 5
        
        # Images with alt (15 points)
        total_images = img_with_alt + img_without_alt
        if total_images > 0:
            alt_ratio = img_with_alt / total_images
            score += int(alt_ratio * 15)
        else:
            score += 15
        
        # Canonical (10 points)
        if canonical:
            score += 10
        
        # Language attribute (10 points)
        html_tag = self.soup.find('html')
        if html_tag and html_tag.get('lang'):
            score += 10
        
        return min(score, 100)
    
    def extract_meta(self) -> Dict[str, str]:
        """Extract all meta tags."""
        meta_tags = {}
        for meta in self.soup.find_all('meta'):
            name = meta.get('name') or meta.get('property') or meta.get('http-equiv')
            content = meta.get('content')
            if name and content:
                meta_tags[name] = content
        return meta_tags
    
    def extract_social_meta(self) -> Dict[str, Any]:
        """Extract Open Graph and Twitter Card data."""
        og = {}
        twitter = {}
        
        for meta in self.soup.find_all('meta'):
            prop = meta.get('property', '')
            name = meta.get('name', '')
            content = meta.get('content', '')
            
            if prop.startswith('og:'):
                og[prop.replace('og:', '')] = content
            elif name.startswith('twitter:'):
                twitter[name.replace('twitter:', '')] = content
        
        return {
            "open_graph": og,
            "twitter_card": twitter
        }
    
    def analyze_structure(self) -> Dict[str, Any]:
        """Analyze page structure."""
        # Count elements
        scripts = self.soup.find_all('script')
        stylesheets = self.soup.find_all('link', rel='stylesheet')
        inline_styles = self.soup.find_all('style')
        
        # Check for important elements
        has_favicon = bool(self.soup.find('link', rel=lambda x: x and 'icon' in x))
        has_viewport = bool(self.soup.find('meta', attrs={'name': 'viewport'}))
        has_charset = bool(self.soup.find('meta', charset=True) or 
                          self.soup.find('meta', attrs={'http-equiv': 'Content-Type'}))
        
        return {
            "scripts": {
                "external": len([s for s in scripts if s.get('src')]),
                "inline": len([s for s in scripts if not s.get('src')])
            },
            "stylesheets": {
                "external": len(stylesheets),
                "inline": len(inline_styles)
            },
            "has_favicon": has_favicon,
            "has_viewport": has_viewport,
            "has_charset": has_charset,
            "doctype": str(self.soup.contents[0]).startswith('<!DOCTYPE') if self.soup.contents else False
        }
    
    def get_performance_hints(self) -> List[str]:
        """Generate performance improvement hints."""
        hints = []
        
        # Check for render-blocking resources
        blocking_scripts = self.soup.find_all('script', src=True)
        blocking = [s for s in blocking_scripts if not s.get('async') and not s.get('defer')]
        if len(blocking) > 3:
            hints.append(f"⚠️ {len(blocking)} scripts sin async/defer pueden bloquear el renderizado")
        
        # Check for large inline styles
        inline_styles = self.soup.find_all('style')
        for style in inline_styles:
            if len(style.get_text()) > 5000:
                hints.append("⚠️ Estilos inline grandes detectados - considerar archivo CSS externo")
                break
        
        # Check for images without dimensions
        images = self.soup.find_all('img')
        imgs_no_dims = [img for img in images if not img.get('width') or not img.get('height')]
        if len(imgs_no_dims) > 5:
            hints.append(f"⚠️ {len(imgs_no_dims)} imágenes sin dimensiones definidas (causa layout shift)")
        
        # Check for lazy loading
        lazy_images = [img for img in images if img.get('loading') == 'lazy']
        if len(images) > 5 and len(lazy_images) < len(images) * 0.5:
            hints.append("💡 Considera usar loading='lazy' en imágenes below-the-fold")
        
        return hints


def generate_analysis_report(analysis: Dict[str, Any]) -> str:
    """Generate a markdown report from analysis data."""
    
    report = f"""# 🔍 Web Analysis Report

**URL:** {analysis['url']}  
**Domain:** {analysis['domain']}  
**Generated:** Auto-generated by Web Cloner Elite

---

## 📊 SEO Score: {analysis['seo']['score']}/100

### Title Tag
- **Content:** {analysis['seo']['title']['content'] or 'Not found ❌'}
- **Length:** {analysis['seo']['title']['length']} characters {'✅' if analysis['seo']['title']['optimal'] else '⚠️'}

### Meta Description
- **Content:** {analysis['seo']['description']['content'] or 'Not found ❌'}
- **Length:** {analysis['seo']['description']['length']} characters {'✅' if analysis['seo']['description']['optimal'] else '⚠️'}

### Heading Structure
| Tag | Count |
|-----|-------|
"""
    
    for tag, count in analysis['seo']['headings']['structure'].items():
        report += f"| {tag.upper()} | {count} |\n"
    
    report += f"""
### Images
- **Total:** {analysis['seo']['images']['total']}
- **With Alt Text:** {analysis['seo']['images']['with_alt']} ✅
- **Without Alt Text:** {analysis['seo']['images']['without_alt']} {'❌' if analysis['seo']['images']['without_alt'] > 0 else ''}
- **Alt Coverage:** {analysis['seo']['images']['alt_percentage']}%

### Links
- **Internal:** {analysis['seo']['links']['internal']}
- **External:** {analysis['seo']['links']['external']}

---

## 🛠️ Technology Stack

"""
    
    tech = analysis['technologies']
    category_icons = {
        'frameworks': '⚛️ Frameworks',
        'cms': '📝 CMS',
        'css_frameworks': '🎨 CSS Frameworks',
        'analytics': '📈 Analytics',
        'cdn': '🌐 CDN',
        'libraries': '📚 Libraries',
        'ecommerce': '🛒 E-commerce',
        'hosting': '☁️ Hosting'
    }
    
    for category, items in tech.items():
        icon = category_icons.get(category, category.title())
        report += f"### {icon}\n"
        for item in items:
            report += f"- {item}\n"
        report += "\n"
    
    if not tech:
        report += "_No se detectaron tecnologías específicas_\n\n"
    
    # Social Meta
    report += """---

## 🔗 Social Media Meta

### Open Graph
"""
    
    og = analysis['social']['open_graph']
    if og:
        for key, value in og.items():
            report += f"- **{key}:** {value[:100]}{'...' if len(value) > 100 else ''}\n"
    else:
        report += "_No Open Graph tags found_\n"
    
    report += "\n### Twitter Card\n"
    twitter = analysis['social']['twitter_card']
    if twitter:
        for key, value in twitter.items():
            report += f"- **{key}:** {value[:100]}{'...' if len(value) > 100 else ''}\n"
    else:
        report += "_No Twitter Card tags found_\n"
    
    # Performance hints
    if analysis['performance_hints']:
        report += "\n---\n\n## ⚡ Performance Hints\n\n"
        for hint in analysis['performance_hints']:
            report += f"- {hint}\n"
    
    report += """
---

## 📁 File Structure

```
output/
├── index.html          # Main HTML file
├── ANALYSIS.md         # This report
├── analysis.json       # Machine-readable data
├── assets/
│   ├── images/         # Downloaded images
│   ├── fonts/          # Web fonts
│   └── icons/          # Favicon and icons
├── css/                # Stylesheets
└── js/                 # JavaScript files
```

---

_Generated by **Web Cloner Elite** - The professional web cloning tool_
"""
    
    return report
