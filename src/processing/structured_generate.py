#!/usr/bin/env python3
"""
Structured website generator that creates the two-column layout
for NT_OrderManager and FluidJournal projects
"""

import os
import json
import re
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from jinja2 import Template

def load_processed_content():
    """Load content from incremental processor cache"""
    content_file = Path("src/content/incremental_content.json")
    
    if content_file.exists():
        try:
            with open(content_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('nt_changes', {}), data.get('fluid_changes', {})
        except:
            pass
    
    # Fallback to manual parsing if no cache
    return parse_session_logs()

def parse_session_logs():
    """Parse session logs and extract project-specific changes"""
    session_log_path = Path("session-logs/claude_memory.md")
    
    nt_changes = defaultdict(list)
    fluid_changes = defaultdict(list)
    
    if not session_log_path.exists():
        return nt_changes, fluid_changes
    
    with open(session_log_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse entries by date and project
    lines = content.split('\n')
    current_date = None
    current_project = None
    
    for i, line in enumerate(lines):
        # Extract date from timestamp
        if line.startswith('## 20'):
            date_match = re.match(r'## (\d{4}-\d{2}-\d{2})', line)
            if date_match:
                current_date = date_match.group(1)
                
                # Check for project tags in the line
                if '[NinjaTrader]' in line or 'NT' in line or 'order-manager' in line.lower():
                    current_project = 'nt'
                elif '[FluidJournal]' in line or 'agentic' in line.lower() or 'storage' in line.lower():
                    current_project = 'fluid'
                elif '[Cohere]' in line:
                    current_project = 'cohere'
                else:
                    # Try to determine from content
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].lower()
                        if any(term in next_line for term in ['ninjatrader', 'trading', 'strategy', 'signal']):
                            current_project = 'nt'
                        elif any(term in next_line for term in ['memory', 'agent', 'storage', 'lancedb', 'risk']):
                            current_project = 'fluid'
        
        # Extract the actual change description
        elif current_date and current_project and line.strip() and not line.startswith('#'):
            # Determine change type based on keywords
            change_type = 'idea'
            if any(word in line.lower() for word in ['added', 'implemented', 'created', 'new']):
                change_type = 'add'
            elif any(word in line.lower() for word in ['removed', 'deleted', 'fixed bug', 'cleaned up']):
                change_type = 'remove'
            elif any(word in line.lower() for word in ['idea', 'concept', 'thinking', 'insight']):
                change_type = 'idea'
            
            # Clean up the description
            description = line.strip()
            if description.endswith('.'):
                description = description[:-1]
            
            change = {
                'type': change_type,
                'description': description[:200]  # Limit length
            }
            
            if current_project == 'nt':
                nt_changes[current_date].append(change)
            elif current_project == 'fluid':
                fluid_changes[current_date].append(change)
    
    return dict(nt_changes), dict(fluid_changes)

def organize_by_priority(changes):
    """Organize changes by priority: plans -> features -> changes -> fixes"""
    organized = {
        'plans': [],
        'features': [],
        'changes': [],
        'fixes': []
    }
    
    for date, entries in changes.items():
        for entry in entries:
            entry_type = entry.get('type', 'change')
            priority = entry.get('priority', 'medium')
            
            # Add date and priority to entry
            entry['date'] = date
            entry['priority'] = priority
            
            # Categorize by type
            if entry_type == 'plan':
                organized['plans'].append(entry)
            elif entry_type == 'feature':
                organized['features'].append(entry)
            elif entry_type == 'fix':
                organized['fixes'].append(entry)
            else:
                organized['changes'].append(entry)
    
    # Sort each category by priority (high -> medium -> low) then by date (recent first)
    for category in organized:
        organized[category].sort(key=lambda x: (
            {'high': 0, 'medium': 1, 'low': 2}.get(x.get('priority', 'medium'), 1),
            x.get('date', ''), 
        ), reverse=True)
    
    return organized

def generate_html_with_scrollbars(nt_organized, fluid_organized):
    """Generate HTML with scrollable sections organized by priority"""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>I just want to build | Development Journey</title>
    <style>
        :root {{
            --bg-color: #0d1117;
            --header-bg: #161b22;
            --card-bg: #161b22;
            --text-color: #c9d1d9;
            --accent-color: #58a6ff;
            --border-color: #30363d;
            --nt-color: #f0883e;
            --fluid-color: #4ecdc4;
            --success-color: #3fb950;
            --danger-color: #f85149;
            --plan-color: #a855f7;
            --feature-color: #3fb950;
            --change-color: #58a6ff;
            --fix-color: #f85149;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif;
            background: var(--bg-color);
            color: var(--text-color);
            line-height: 1.6;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }}
        
        /* Fixed Header */
        header {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: var(--header-bg);
            border-bottom: 1px solid var(--border-color);
            z-index: 1000;
            padding: 1rem 0;
        }}
        
        .header-content {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 2rem;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
        }}
        
        .avatar {{
            width: 48px;
            height: 48px;
            border-radius: 50%;
            border: 2px solid var(--accent-color);
        }}
        
        .last-updated {{
            position: absolute;
            right: 2rem;
            font-size: 0.875rem;
            color: #8b949e;
        }}
        
        /* Banner */
        .banner {{
            margin-top: 80px;
            background: linear-gradient(135deg, #1e3a5f 0%, #1a2332 100%);
            padding: 3rem 0;
            text-align: center;
            border-bottom: 1px solid var(--border-color);
        }}
        
        .banner h1 {{
            font-size: 3rem;
            font-weight: 600;
            color: white;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }}
        
        /* Main Content */
        main {{
            flex: 1;
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
            width: 100%;
        }}
        
        .columns {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
            margin-bottom: 3rem;
        }}
        
        .project-pane {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            height: 80vh;
        }}
        
        .project-header {{
            padding: 1.5rem;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            gap: 1rem;
            flex-shrink: 0;
        }}
        
        .project-header h2 {{
            font-size: 1.5rem;
            font-weight: 600;
        }}
        
        .project-header.nt {{
            background: linear-gradient(135deg, rgba(240, 136, 62, 0.1) 0%, transparent 100%);
            border-bottom-color: rgba(240, 136, 62, 0.3);
        }}
        
        .project-header.fluid {{
            background: linear-gradient(135deg, rgba(78, 205, 196, 0.1) 0%, transparent 100%);
            border-bottom-color: rgba(78, 205, 196, 0.3);
        }}
        
        .project-icon {{
            width: 32px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 8px;
            font-weight: bold;
        }}
        
        .nt .project-icon {{
            background: var(--nt-color);
            color: white;
        }}
        
        .fluid .project-icon {{
            background: var(--fluid-color);
            color: white;
        }}
        
        .project-content {{
            padding: 1.5rem;
            flex: 1;
            overflow-y: auto;
            scrollbar-width: thin;
            scrollbar-color: var(--accent-color) var(--card-bg);
        }}
        
        .project-content::-webkit-scrollbar {{
            width: 8px;
        }}
        
        .project-content::-webkit-scrollbar-track {{
            background: var(--card-bg);
        }}
        
        .project-content::-webkit-scrollbar-thumb {{
            background: var(--accent-color);
            border-radius: 4px;
        }}
        
        .project-summary {{
            margin-bottom: 2rem;
            padding: 1rem;
            background: rgba(88, 166, 255, 0.05);
            border-left: 3px solid var(--accent-color);
            border-radius: 4px;
        }}
        
        .project-summary h3 {{
            font-size: 1.1rem;
            margin-bottom: 0.5rem;
            color: var(--accent-color);
        }}
        
        .category-section {{
            margin-bottom: 2rem;
        }}
        
        .category-header {{
            font-weight: 600;
            margin-bottom: 1rem;
            padding: 0.75rem;
            border-radius: 8px;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        
        .category-header.plans {{
            background: rgba(168, 85, 247, 0.1);
            color: var(--plan-color);
            border: 1px solid rgba(168, 85, 247, 0.3);
        }}
        
        .category-header.features {{
            background: rgba(63, 185, 80, 0.1);
            color: var(--feature-color);
            border: 1px solid rgba(63, 185, 80, 0.3);
        }}
        
        .category-header.changes {{
            background: rgba(88, 166, 255, 0.1);
            color: var(--change-color);
            border: 1px solid rgba(88, 166, 255, 0.3);
        }}
        
        .category-header.fixes {{
            background: rgba(248, 81, 73, 0.1);
            color: var(--fix-color);
            border: 1px solid rgba(248, 81, 73, 0.3);
        }}
        
        .change-list {{
            list-style: none;
            padding-left: 0;
        }}
        
        .change-item {{
            padding: 0.75rem;
            margin-bottom: 0.5rem;
            border-radius: 6px;
            border-left: 3px solid;
            background: rgba(255, 255, 255, 0.02);
            position: relative;
        }}
        
        .change-item.plan {{
            border-left-color: var(--plan-color);
        }}
        
        .change-item.feature {{
            border-left-color: var(--feature-color);
        }}
        
        .change-item.change {{
            border-left-color: var(--change-color);
        }}
        
        .change-item.fix {{
            border-left-color: var(--fix-color);
        }}
        
        .priority-badge {{
            position: absolute;
            top: 0.5rem;
            right: 0.5rem;
            font-size: 0.7rem;
            padding: 0.2rem 0.4rem;
            border-radius: 10px;
            font-weight: bold;
        }}
        
        .priority-high {{
            background: #dc2626;
            color: white;
        }}
        
        .priority-medium {{
            background: #f59e0b;
            color: white;
        }}
        
        .priority-low {{
            background: #6b7280;
            color: white;
        }}
        
        .change-date {{
            font-size: 0.8rem;
            color: #8b949e;
            margin-bottom: 0.25rem;
        }}
        
        .change-description {{
            font-weight: 500;
            margin-bottom: 0.5rem;
        }}
        
        .change-detail {{
            font-size: 0.875rem;
            color: #8b949e;
            margin-bottom: 0.25rem;
        }}
        
        .change-impact {{
            font-size: 0.875rem;
            color: var(--accent-color);
            font-style: italic;
        }}
        
        /* Tech Stack Footer */
        footer {{
            background: var(--header-bg);
            border-top: 1px solid var(--border-color);
            padding: 3rem 0;
            margin-top: auto;
        }}
        
        .footer-content {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 2rem;
        }}
        
        .tech-stack {{
            margin-bottom: 2rem;
        }}
        
        .tech-stack h3 {{
            font-size: 1.25rem;
            margin-bottom: 1.5rem;
            color: var(--accent-color);
        }}
        
        .tech-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
        }}
        
        .tech-item {{
            background: var(--bg-color);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1rem;
            transition: border-color 0.2s;
        }}
        
        .tech-item:hover {{
            border-color: var(--accent-color);
        }}
        
        .tech-name {{
            font-weight: 600;
            color: var(--accent-color);
            margin-bottom: 0.25rem;
        }}
        
        .tech-justification {{
            font-size: 0.875rem;
            color: #8b949e;
        }}
        
        .footer-bottom {{
            text-align: center;
            padding-top: 2rem;
            border-top: 1px solid var(--border-color);
            color: #8b949e;
            font-size: 0.875rem;
        }}
        
        /* Responsive */
        @media (max-width: 968px) {{
            .columns {{
                grid-template-columns: 1fr;
            }}
            
            .project-pane {{
                height: 60vh;
            }}
            
            .banner h1 {{
                font-size: 2rem;
            }}
            
            .header-content {{
                padding: 0 1rem;
            }}
            
            .last-updated {{
                display: none;
            }}
        }}
    </style>
</head>
<body>
    <header>
        <div class="header-content">
            <img src="https://avatars.githubusercontent.com/u/2623736?s=400&u=e7f8d6597d1d222a1f038ed316af1e439c3a57b4&v=4" 
                 alt="CaptrainWalrus" class="avatar">
            <div class="last-updated">Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
        </div>
    </header>
    
    <div class="banner">
        <h1>I just want to build</h1>
    </div>
    
    <main>
        <div class="columns">
            <!-- NT_OrderManager Column -->
            <div class="project-pane">
                <div class="project-header nt">
                    <div class="project-icon">NT</div>
                    <h2>NT_OrderManager</h2>
                </div>
                <div class="project-content">
                    <div class="project-summary">
                        <h3>Project Overview</h3>
                        <p>Sophisticated algorithmic trading system with NinjaTrader 8 integration. Features include adaptive risk management, ML-based signal filtering, and real-time market analysis.</p>
                    </div>
                    
                    {generate_category_section("plans", "🚀 New/Big Plans", nt_organized['plans'])}
                    {generate_category_section("features", "✨ Features", nt_organized['features'])}
                    {generate_category_section("changes", "🔧 Changes", nt_organized['changes'])}
                    {generate_category_section("fixes", "🐛 Fixes & Bugs", nt_organized['fixes'])}
                </div>
            </div>
            
            <!-- FluidJournal Column -->
            <div class="project-pane">
                <div class="project-header fluid">
                    <div class="project-icon">FJ</div>
                    <h2>FluidJournal</h2>
                </div>
                <div class="project-content">
                    <div class="project-summary">
                        <h3>Project Overview</h3>
                        <p>Revolutionary agentic memory system using graduated feature matching and range-based intelligence. Learns optimal trading parameters from historical patterns.</p>
                    </div>
                    
                    {generate_category_section("plans", "🚀 New/Big Plans", fluid_organized['plans'])}
                    {generate_category_section("features", "✨ Features", fluid_organized['features'])}
                    {generate_category_section("changes", "🔧 Changes", fluid_organized['changes'])}
                    {generate_category_section("fixes", "🐛 Fixes & Bugs", fluid_organized['fixes'])}
                </div>
            </div>
        </div>
    </main>
    
    <footer>
        <div class="footer-content">
            <div class="tech-stack">
                <h3>Tech Stack Choices</h3>
                <div class="tech-grid">
                    <div class="tech-item">
                        <div class="tech-name">LanceDB</div>
                        <div class="tech-justification">Vector database for ML feature storage with excellent performance and simple API</div>
                    </div>
                    <div class="tech-item">
                        <div class="tech-name">NinjaTrader 8</div>
                        <div class="tech-justification">Professional trading platform with robust C# API for algorithmic trading</div>
                    </div>
                    <div class="tech-item">
                        <div class="tech-name">Node.js + Express</div>
                        <div class="tech-justification">Fast microservices architecture for real-time market data processing</div>
                    </div>
                    <div class="tech-item">
                        <div class="tech-name">Gaussian Processes</div>
                        <div class="tech-justification">Uncertainty quantification for risk management decisions</div>
                    </div>
                    <div class="tech-item">
                        <div class="tech-name">GitHub Actions</div>
                        <div class="tech-justification">Automated CI/CD for website regeneration on session log updates</div>
                    </div>
                    <div class="tech-item">
                        <div class="tech-name">LangChain + OpenAI</div>
                        <div class="tech-justification">Intelligent content aggregation from development session logs</div>
                    </div>
                </div>
            </div>
            
            <div class="footer-bottom">
                <p>&nbsp;</p>
            </div>
        </div>
    </footer>
</body>
</html>"""

def generate_category_section(category_type, title, items):
    """Generate HTML for a category section"""
    if not items:
        return ""
    
    items_html = ""
    for item in items:
        priority_class = f"priority-{item.get('priority', 'medium')}"
        priority_text = item.get('priority', 'medium').upper()
        
        technical_detail = ""
        if item.get('technical_detail'):
            technical_detail = f'<div class="change-detail">🔧 {item["technical_detail"]}</div>'
        
        impact = ""
        if item.get('impact'):
            impact = f'<div class="change-impact">💡 {item["impact"]}</div>'
        
        items_html += f'''
            <li class="change-item {category_type}">
                <div class="priority-badge {priority_class}">{priority_text}</div>
                <div class="change-date">{item.get('date', '')}</div>
                <div class="change-description">{item.get('description', '')}</div>
                {technical_detail}
                {impact}
            </li>
        '''
    
    return f'''
        <div class="category-section">
            <div class="category-header {category_type}">
                <span>{title}</span>
                <span style="margin-left: auto; background: rgba(255,255,255,0.1); padding: 0.2rem 0.5rem; border-radius: 10px; font-size: 0.8rem;">
                    {len(items)}
                </span>
            </div>
            <ul class="change-list">
                {items_html}
            </ul>
        </div>
    '''

def generate_website():
    """Generate the structured website"""
    # Load processed content (from cache or parse)
    nt_changes, fluid_changes = load_processed_content()
    
    # Don't limit - process entire log
    nt_changes = dict(sorted(nt_changes.items(), reverse=True))
    fluid_changes = dict(sorted(fluid_changes.items(), reverse=True))
    
    # Organize by priority
    nt_organized = organize_by_priority(nt_changes)
    fluid_organized = organize_by_priority(fluid_changes)
    
    # Generate HTML directly (no template needed)
    html_output = generate_html_with_scrollbars(nt_organized, fluid_organized)
    
    # Write output
    output_path = Path("index.html")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_output)
    
    print(f"✅ Structured website generated at {output_path}")
    total_nt = sum(len(cat) for cat in nt_organized.values())
    total_fluid = sum(len(cat) for cat in fluid_organized.values())
    print(f"📊 NT_OrderManager: {total_nt} total entries")
    print(f"📊 FluidJournal: {total_fluid} total entries")

if __name__ == "__main__":
    generate_website()