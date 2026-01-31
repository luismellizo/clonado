"""
Quality Assurance Module
Analyzes downloaded templates for quality and generates certification reports.
"""
import os
import aiofiles
import logging

logger = logging.getLogger(__name__)

class QualityScorer:
    """Evaluates the quality of a cloned site."""
    
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.score = {
            'overall': 0,
            'images': {'score': 0, 'issues': []},
            'css': {'score': 0, 'issues': []},
            'html': {'score': 0, 'issues': []},
        }
    
    async def analyze_quality(self) -> dict:
        """Run full quality analysis."""
        await self.check_images()
        await self.check_css()
        await self.check_html()
        self.calculate_overall_score()
        return self.score
    
    async def check_images(self):
        """Analyze image assets."""
        images_dir = os.path.join(self.output_dir, 'assets', 'images')
        
        if not os.path.exists(images_dir):
            self.score['images']['score'] = 100 # No images is technically valid
            self.score['images']['stats'] = {'total': 0, 'broken': 0, 'oversized': 0, 'total_size_mb': 0}
            return
        
        total = 0
        broken = 0
        oversized = 0
        current_size = 0
        
        for f in os.listdir(images_dir):
            path = os.path.join(images_dir, f)
            if not os.path.isfile(path): continue
            
            total += 1
            size = os.path.getsize(path)
            current_size += size
            
            if size > 1_500_000: # > 1.5MB
                oversized += 1
                self.score['images']['issues'].append(f"Heavy image: {f} ({size/1024/1024:.1f}MB)")
                
            # Basic integrity check
            if size < 100: # Suspiciously small
                broken += 1
                self.score['images']['issues'].append(f"Corrupt/Empty image: {f}")
        
        # Scoring
        if total == 0:
            score = 100
        else:
            penalty = (broken * 20) + (oversized * 5)
            score = max(0, 100 - (penalty / total * 10)) # Normalize penalty
            
        self.score['images']['score'] = int(score)
        self.score['images']['stats'] = {
            'total': total,
            'broken': broken,
            'oversized': oversized,
            'total_size_mb': round(current_size / 1024 / 1024, 2)
        }

    async def check_css(self):
        """Analyze CSS assets."""
        css_dir = os.path.join(self.output_dir, 'css')
        
        if not os.path.exists(css_dir):
            self.score['css']['score'] = 100
            self.score['css']['stats'] = {'total': 0, 'broken': 0}
            return
            
        total = 0
        broken = 0
        
        for f in os.listdir(css_dir):
            if not f.endswith('.css'): continue
            path = os.path.join(css_dir, f)
            total += 1
            
            async with aiofiles.open(path, 'r', errors='ignore') as file:
                content = await file.read()
                if '<html' in content.lower():
                    broken += 1
                    self.score['css']['issues'].append(f"Invalid CSS (contains HTML): {f}")
                    
        if total == 0:
            score = 100
        else:
            score = max(0, 100 - (broken / total * 100))
            
        self.score['css']['score'] = int(score)
        self.score['css']['stats'] = {'total': total, 'broken': broken}

    async def check_html(self):
        """Analyze index.html."""
        html_path = os.path.join(self.output_dir, 'index.html')
        if not os.path.exists(html_path):
            self.score['html']['score'] = 0
            self.score['html']['issues'].append("Missing index.html")
            return
            
        async with aiofiles.open(html_path, 'r', errors='ignore') as f:
            content = await f.read()
            
        issues = []
        score = 100
        
        # Check for broken links left
        # (Naive check: empty src/href)
        broken_refs = content.count('src=""') + content.count('href=""')
        if broken_refs > 0:
            issues.append(f"{broken_refs} empty resource references")
            score -= min(20, broken_refs * 2)
            
        # Check for tracers
        tracers = ['google-analytics', 'fbq(', 'gtag(']
        found_tracers = sum(1 for t in tracers if t in content)
        if found_tracers > 0:
            issues.append(f"{found_tracers} tracking scripts detected")
            score -= found_tracers * 5
            
        self.score['html']['score'] = max(0, int(score))
        self.score['html']['issues'] = issues

    def calculate_overall_score(self):
        """Weighted average."""
        weights = {'html': 0.4, 'css': 0.3, 'images': 0.3}
        total = sum(self.score[k]['score'] * w for k, w in weights.items())
        self.score['overall'] = int(total)

    async def generate_report(self) -> str:
        """Generate markdown report."""
        s = self.score
        
        report = f"""# ✅ Quality Certification Report

## 🏆 Overall Quality Score: {s['overall']}/100

### Breakdown
- **HTML Structure**: {s['html']['score']}/100
- **Stylesheets**: {s['css']['score']}/100
- **Images & Assets**: {s['images']['score']}/100

### 🔍 Detailed Inspection

**HTML Issues**:
{self._format_issues(s['html']['issues'])}

**CSS Stats**:
- Total Files: {s['css']['stats'].get('total', 0)}
- Broken Files: {s['css']['stats'].get('broken', 0)}
{self._format_issues(s['css']['issues'])}

**Image Optimization**:
- Total Images: {s['images']['stats'].get('total', 0)}
- Total Size: {s['images']['stats'].get('total_size_mb', 0)} MB
{self._format_issues(s['images']['issues'])}

---
*Certified by Web Cloner Elite Quality Engine*
"""
        return report

    def _format_issues(self, issues):
        if not issues:
            return "_No significant issues found. ✅_"
        return "\n".join([f"- ⚠️ {i}" for i in issues])
