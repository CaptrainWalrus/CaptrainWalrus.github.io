# GitHub Pages Integration for Auto-Regen Website

## Why GitHub Pages is Perfect

### ✅ **Free Hosting**
- 1GB storage limit (plenty for your website)
- 100GB bandwidth/month (more than enough)
- Custom domain support (bring your own domain)
- SSL certificates included

### ✅ **GitHub Actions Integration**
- Automatic builds on commit
- Built-in deployment to Pages
- No external hosting setup needed

### ✅ **Version Control**
- All website content is version controlled
- Easy rollbacks if something breaks
- Collaborative development if needed

## Repository Setup Options

### Option 1: Single Repository (Recommended)
```
my-dev-journey/
├── session-logs/
│   ├── claude_memory.md
│   ├── project-a/
│   │   └── claude_memory.md
│   └── project-b/
│       └── claude_memory.md
├── src/
│   ├── processing/
│   │   ├── langchain_processor.py
│   │   └── requirements.txt
│   └── templates/
│       └── index.html
├── docs/                    # GitHub Pages serves from here
│   ├── index.html          # Generated website
│   ├── css/
│   └── js/
├── .github/
│   └── workflows/
│       └── build-site.yml
└── README.md
```

### Option 2: Separate Repositories
```
Source Repo: my-claude-sessions (private)
Website Repo: my-dev-website (public - for GitHub Pages)
```

## GitHub Pages Configuration

### 1. Repository Settings
```
Repository → Settings → Pages
Source: Deploy from a branch
Branch: main
Folder: /docs (or / root)
```

### 2. Custom Domain (Optional)
```
Custom domain: yourname.dev
Enforce HTTPS: ✅ (automatic with custom domain)
```

## GitHub Actions Workflow

### Complete Build & Deploy Workflow
```yaml
# .github/workflows/build-site.yml
name: Build and Deploy to GitHub Pages

on:
  push:
    branches: [ main ]
    paths:
      - 'session-logs/**/*.md'
      - 'src/**'
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          pip install -r src/processing/requirements.txt
          
      - name: Process session logs with LangChain
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          LANGCHAIN_API_KEY: ${{ secrets.LANGCHAIN_API_KEY }}
        run: |
          python src/processing/langchain_processor.py
          
      - name: Setup Node.js (if using static site generator)
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          
      - name: Build static site
        run: |
          # Option A: Simple HTML generation
          python src/processing/generate_html.py
          
          # Option B: Use Jekyll/Hugo (uncomment if needed)
          # gem install jekyll bundler
          # bundle install
          # bundle exec jekyll build --destination docs
          
      - name: Upload artifact
        uses: actions/upload-pages-artifact@v2
        with:
          path: ./docs

  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v2
```

## Simple HTML Generation

### Python HTML Generator (`src/processing/generate_html.py`)
```python
import os
import json
from datetime import datetime
from jinja2 import Template

class HTMLGenerator:
    def __init__(self):
        self.template_dir = "src/templates"
        self.output_dir = "docs"
        
    def generate_site(self):
        # Load processed content from LangChain
        with open('src/content/processed_content.json', 'r') as f:
            content_data = json.load(f)
            
        # Load HTML template
        with open(f"{self.template_dir}/index.html", 'r') as f:
            template = Template(f.read())
            
        # Generate HTML
        html_content = template.render(
            title="My Development Journey",
            content=content_data['main_content'],
            insights=content_data['insights'],
            recent_sessions=content_data['recent_sessions'],
            last_update=datetime.now().strftime("%Y-%m-%d %H:%M UTC")
        )
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Write HTML file
        with open(f"{self.output_dir}/index.html", 'w') as f:
            f.write(html_content)
            
        # Copy static assets
        self.copy_static_files()
        
    def copy_static_files(self):
        # Copy CSS, JS, images etc.
        import shutil
        if os.path.exists("src/static"):
            shutil.copytree("src/static", f"{self.output_dir}/static", 
                          dirs_exist_ok=True)

if __name__ == "__main__":
    generator = HTMLGenerator()
    generator.generate_site()
    print("✅ Website generated successfully!")
```

## Enhanced Template with GitHub Pages Features

### Modern Responsive Template (`src/templates/index.html`)
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <meta name="description" content="Auto-generated insights from my development journey">
    
    <!-- GitHub Pages compatible paths -->
    <link rel="stylesheet" href="./static/style.css">
    <link rel="icon" href="./static/favicon.ico">
    
    <!-- Dark mode support -->
    <script>
        if (localStorage.getItem('theme') === 'dark' || 
            (!localStorage.getItem('theme') && 
             window.matchMedia('(prefers-color-scheme: dark)').matches)) {
            document.documentElement.setAttribute('data-theme', 'dark');
        }
    </script>
</head>
<body>
    <header>
        <nav>
            <h1>🚀 Development Journey</h1>
            <button id="theme-toggle" aria-label="Toggle dark mode">🌙</button>
        </nav>
        <p class="subtitle">Auto-generated insights from development sessions</p>
    </header>

    <main>
        <section class="hero">
            <div class="container">
                {{ content.hero_section | safe }}
            </div>
        </section>

        <section class="insights">
            <div class="container">
                <h2>Recent Breakthroughs</h2>
                {% for insight in insights %}
                <article class="insight-card">
                    <time>{{ insight.date }}</time>
                    <h3>{{ insight.title }}</h3>
                    <div class="content">{{ insight.content | safe }}</div>
                    <div class="tags">
                        {% for tag in insight.tags %}
                        <span class="tag">{{ tag }}</span>
                        {% endfor %}
                    </div>
                </article>
                {% endfor %}
            </div>
        </section>

        <section class="activity">
            <div class="container">
                <h2>Development Activity</h2>
                <div class="timeline">
                    {% for session in recent_sessions %}
                    <div class="timeline-item">
                        <div class="timeline-marker"></div>
                        <div class="timeline-content">
                            <time>{{ session.timestamp }}</time>
                            <h4>{{ session.project }}</h4>
                            <p>{{ session.summary }}</p>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </section>
    </main>

    <footer>
        <div class="container">
            <p>Last updated: {{ last_update }}</p>
            <p>Auto-generated from session logs via LangChain</p>
        </div>
    </footer>

    <script src="./static/script.js"></script>
</body>
</html>
```

## CSS Styling (`src/static/style.css`)
```css
/* Modern, responsive design */
:root {
    --bg-color: #ffffff;
    --text-color: #333333;
    --accent-color: #0066cc;
    --border-color: #e0e0e0;
    --card-bg: #f8f9fa;
}

[data-theme="dark"] {
    --bg-color: #1a1a1a;
    --text-color: #e0e0e0;
    --accent-color: #66b3ff;
    --border-color: #333333;
    --card-bg: #2a2a2a;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    line-height: 1.6;
    color: var(--text-color);
    background-color: var(--bg-color);
    transition: background-color 0.3s ease;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 1rem;
}

header {
    background: var(--card-bg);
    border-bottom: 1px solid var(--border-color);
    padding: 2rem 0;
}

nav {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
}

.insight-card {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    transition: transform 0.2s ease;
}

.insight-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.timeline {
    position: relative;
    padding-left: 2rem;
}

.timeline::before {
    content: '';
    position: absolute;
    left: 1rem;
    top: 0;
    bottom: 0;
    width: 2px;
    background: var(--accent-color);
}

.timeline-item {
    position: relative;
    margin-bottom: 2rem;
}

.timeline-marker {
    position: absolute;
    left: -1.5rem;
    top: 0.5rem;
    width: 12px;
    height: 12px;
    background: var(--accent-color);
    border-radius: 50%;
}

@media (max-width: 768px) {
    .container {
        padding: 0 0.5rem;
    }
    
    .insight-card {
        padding: 1rem;
    }
}
```

## Domain Setup with GitHub Pages

### 1. Purchase Domain
```
Popular options:
- Namecheap ($10-15/year)
- Google Domains ($12/year)
- Cloudflare ($8-10/year)
```

### 2. Configure DNS
```
DNS Records:
CNAME www yourname.github.io
A @ 185.199.108.153
A @ 185.199.109.153
A @ 185.199.110.153
A @ 185.199.111.153
```

### 3. GitHub Repository Settings
```
Settings → Pages → Custom domain: yourname.dev
GitHub will automatically generate SSL certificate
```

## Benefits of GitHub Pages Approach

### ✅ **Cost Effective**
- Free hosting (only domain cost ~$10/year)
- No server maintenance
- Built-in CDN and SSL

### ✅ **Simple Deployment**
- Push to commit → automatic deployment
- No complex CI/CD setup needed
- GitHub handles everything

### ✅ **Reliable**
- 99.9% uptime SLA
- Global CDN
- Automatic backups (git history)

## Limitations to Consider

### ⚠️ **GitHub Pages Limits**
- 1GB repository size
- 100GB bandwidth/month
- No server-side processing (static only)
- 10 builds per hour

### ✅ **Solutions**
- LangChain processing happens in GitHub Actions (not at serve time)
- Generated static content is served
- Well within limits for personal blog
- Can upgrade to GitHub Pro if needed

## Getting Started

1. **Create repository** with the structure above
2. **Add your session logs** to `session-logs/` directory  
3. **Configure GitHub Actions** with the workflow
4. **Enable GitHub Pages** in repository settings
5. **Optional: Add custom domain**

Your website will be live at `yourusername.github.io/repository-name` (or your custom domain)!