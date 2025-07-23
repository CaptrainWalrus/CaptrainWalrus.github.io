#!/usr/bin/env python3
"""
HTML generator for development journey website
Takes processed LangChain content and generates static website
"""

import os
import json
from datetime import datetime
from pathlib import Path
from jinja2 import Template
import shutil

class HTMLGenerator:
    def __init__(self):
        """Initialize the HTML generator"""
        self.content_dir = Path("src/content")
        self.template_dir = Path("src/templates")
        self.static_dir = Path("src/static")
        self.output_dir = Path(".")
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def load_processed_content(self) -> dict:
        """Load the processed content from LangChain processor"""
        content_file = self.content_dir / "processed_content.json"
        
        if not content_file.exists():
            print("⚠️ No processed content found, creating placeholder")
            return self.create_placeholder_content()
        
        try:
            with open(content_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading content: {e}")
            return self.create_placeholder_content()
    
    def create_placeholder_content(self) -> dict:
        """Create placeholder content when processing fails"""
        return {
            'generated_at': datetime.now().isoformat(),
            'narrative_content': """# Development Journey

Welcome to my development journey! This website automatically updates from my Claude session logs.

## Current Status
Setting up the auto-generation system. Session logs will be processed here soon!

## What This Site Does
- Monitors my Claude development session logs
- Uses LangChain to extract meaningful insights
- Automatically regenerates content on every commit
- Shows development patterns and progress over time

Check back soon for live development insights!
            """,
            'projects': [
                {
                    'project_name': 'Auto-Regen Website',
                    'last_modified': datetime.now().isoformat(),
                    'word_count': 100,
                    'insights': {
                        'breakthrough': 'Setting up LangChain integration',
                        'problem_solved': 'GitHub Pages deployment configured',
                        'learning_pattern': 'Building automated content generation',
                        'momentum': 'Initial setup phase'
                    }
                }
            ],
            'total_projects': 1,
            'total_words': 100
        }
    
    def load_template(self) -> Template:
        """Load the HTML template"""
        template_file = self.template_dir / "index.html"
        
        if not template_file.exists():
            print("⚠️ No template found, creating basic template")
            return Template(self.create_basic_template())
        
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                return Template(f.read())
        except Exception as e:
            print(f"Error loading template: {e}")
            return Template(self.create_basic_template())
    
    def create_basic_template(self) -> str:
        """Create a basic HTML template if none exists"""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Development Journey</title>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
            color: #333;
        }
        .header { border-bottom: 2px solid #007acc; margin-bottom: 2rem; padding-bottom: 1rem; }
        .project { margin: 2rem 0; padding: 1.5rem; background: #f8f9fa; border-radius: 8px; }
        .insight { margin: 1rem 0; }
        .meta { color: #666; font-size: 0.9em; }
        .stats { background: #e3f2fd; padding: 1rem; border-radius: 8px; margin: 2rem 0; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Development Journey</h1>
        <p>Auto-generated insights from development sessions</p>
    </div>
    
    <div class="content">
        {{ content | safe }}
    </div>
    
    <div class="stats">
        <h3>📊 Stats</h3>
        <p><strong>Total Projects:</strong> {{ total_projects }}</p>
        <p><strong>Total Words:</strong> {{ total_words:,}}</p>
        <p><strong>Last Updated:</strong> {{ last_updated }}</p>
    </div>
    
    <div class="projects">
        <h2>🔨 Active Projects</h2>
        {% for project in projects %}
        <div class="project">
            <h3>{{ project.project_name }}</h3>
            {% if project.insights.breakthrough %}
            <div class="insight">
                <strong>💡 Breakthrough:</strong> {{ project.insights.breakthrough }}
            </div>
            {% endif %}
            {% if project.insights.problem_solved %}
            <div class="insight">
                <strong>🔧 Problem Solved:</strong> {{ project.insights.problem_solved }}
            </div>
            {% endif %}
            {% if project.insights.momentum %}
            <div class="insight">
                <strong>⚡ Current Status:</strong> {{ project.insights.momentum }}
            </div>
            {% endif %}
            <div class="meta">
                Last updated: {{ project.last_modified[:10] }} | {{ project.word_count:,}} words
            </div>
        </div>
        {% endfor %}
    </div>
    
    <footer style="margin-top: 3rem; padding-top: 2rem; border-top: 1px solid #ddd; color: #666;">
        <p>Generated automatically from Claude session logs using LangChain</p>
    </footer>
</body>
</html>"""
    
    def markdown_to_html(self, markdown_text: str) -> str:
        """Convert markdown to HTML (basic implementation)"""
        try:
            import markdown
            return markdown.markdown(markdown_text, extensions=['extra'])
        except ImportError:
            # Fallback: basic markdown conversion
            html = markdown_text
            html = html.replace('\n# ', '\n<h1>').replace('</h1>\n', '</h1>\n')
            html = html.replace('\n## ', '\n<h2>').replace('</h2>\n', '</h2>\n')
            html = html.replace('\n### ', '\n<h3>').replace('</h3>\n', '</h3>\n')
            html = html.replace('**', '<strong>').replace('</strong>', '</strong>')
            html = html.replace('\n\n', '</p><p>')
            html = f"<p>{html}</p>"
            return html
    
    def copy_static_files(self):
        """Copy static files (CSS, JS, images) to output directory"""
        if self.static_dir.exists():
            output_static = self.output_dir / "static"
            if output_static.exists():
                shutil.rmtree(output_static)
            shutil.copytree(self.static_dir, output_static)
            print("📁 Copied static files")
        else:
            print("⚠️ No static files directory found")
    
    def generate_site(self):
        """Generate the complete website"""
        print("🏗️ Generating website...")
        
        # Load processed content
        content_data = self.load_processed_content()
        
        # Load template
        template = self.load_template()
        
        # Convert markdown content to HTML
        html_content = self.markdown_to_html(content_data['narrative_content'])
        
        # Calculate global context statistics
        global_contexts = {}
        context_count = 0
        for project in content_data['projects']:
            if 'context_summary' in project:
                for context, count in project['context_summary'].items():
                    global_contexts[context] = global_contexts.get(context, 0) + count
                    context_count += count
        
        # Prepare template variables
        template_vars = {
            'content': html_content,
            'projects': content_data['projects'],
            'total_projects': content_data['total_projects'],
            'total_words': content_data['total_words'],
            'last_updated': datetime.fromisoformat(content_data['generated_at']).strftime('%Y-%m-%d'),
            'global_contexts': global_contexts,
            'context_count': len(global_contexts),
            'narrative_content': html_content
        }
        
        # Render template
        html_output = template.render(**template_vars)
        
        # Write HTML file
        output_file = self.output_dir / "index.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_output)
        
        # Copy static files
        self.copy_static_files()
        
        print(f"✅ Website generated successfully at {output_file}")
        print(f"🌐 Will be live at: https://captrainwalrus.github.io/dev-journey")

if __name__ == "__main__":
    try:
        generator = HTMLGenerator()
        generator.generate_site()
    except Exception as e:
        print(f"❌ Error generating website: {e}")
        # Create a basic index.html as fallback
        output_dir = Path(".")
        
        # If error, run the simple generator instead
        print("⚠️ Running simple generator as fallback...")
        import subprocess
        import sys
        subprocess.run([sys.executable, "src/processing/simple_generate.py"])