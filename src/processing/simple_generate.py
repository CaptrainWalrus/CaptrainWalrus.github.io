#!/usr/bin/env python3
"""
Simple website generator that works without OpenAI API
Creates a basic but functional website from session logs
"""

import os
import json
from datetime import datetime
from pathlib import Path

# Create output directory
output_dir = Path("docs")
output_dir.mkdir(parents=True, exist_ok=True)

# Read session logs
session_log_path = Path("session-logs/claude_memory.md")
content = "No session logs found yet."

if session_log_path.exists():
    with open(session_log_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
# Count some basic stats
lines = content.split('\n')
timestamps = [line for line in lines if line.strip().startswith('## 2025-')]
word_count = len(content.split())

# Create a simple but nice looking HTML page
html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Development Journey | Auto-Generated Insights</title>
    <style>
        :root {{
            --bg-color: #ffffff;
            --text-color: #333333;
            --accent-color: #007acc;
            --border-color: #e0e0e0;
            --card-bg: #f8f9fa;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: var(--text-color);
            background-color: var(--bg-color);
            margin: 0;
            padding: 0;
        }}
        
        header {{
            background: linear-gradient(135deg, var(--accent-color), #4a90e2);
            color: white;
            padding: 3rem 0;
            text-align: center;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 1rem;
        }}
        
        .stats-bar {{
            background: var(--card-bg);
            border-bottom: 1px solid var(--border-color);
            padding: 1rem 0;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 2rem;
            text-align: center;
        }}
        
        .stat-number {{
            font-size: 2rem;
            font-weight: bold;
            color: var(--accent-color);
        }}
        
        .content {{
            padding: 3rem 0;
        }}
        
        .session-entries {{
            background: var(--card-bg);
            padding: 2rem;
            border-radius: 12px;
            margin-top: 2rem;
        }}
        
        .entry {{
            margin-bottom: 1.5rem;
            padding-bottom: 1.5rem;
            border-bottom: 1px solid var(--border-color);
        }}
        
        .entry:last-child {{
            border-bottom: none;
        }}
        
        .timestamp {{
            color: #666;
            font-size: 0.9rem;
        }}
        
        footer {{
            background: var(--card-bg);
            border-top: 1px solid var(--border-color);
            padding: 2rem 0;
            text-align: center;
            color: #666;
            margin-top: 4rem;
        }}
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1>🚀 Development Journey</h1>
            <p>Auto-generated insights from Claude development sessions</p>
        </div>
    </header>
    
    <div class="stats-bar">
        <div class="container">
            <div class="stats-grid">
                <div>
                    <div class="stat-number">{len(timestamps)}</div>
                    <div>Session Entries</div>
                </div>
                <div>
                    <div class="stat-number">{word_count:,}</div>
                    <div>Total Words</div>
                </div>
                <div>
                    <div class="stat-number">{datetime.now().strftime('%Y-%m-%d')}</div>
                    <div>Last Updated</div>
                </div>
            </div>
        </div>
    </div>
    
    <main class="content">
        <div class="container">
            <h2>📖 Recent Development Activity</h2>
            <div class="session-entries">
                <p><em>Full LangChain processing will be enabled once the OpenAI API is configured.</em></p>
                <p>For now, here's a summary of your development journey:</p>
                <ul>
                    <li><strong>Session entries:</strong> {len(timestamps)}</li>
                    <li><strong>Total words written:</strong> {word_count:,}</li>
                    <li><strong>Latest session:</strong> Working on auto-regenerating website with LangChain</li>
                </ul>
                
                <h3>Recent Entries</h3>
                {"".join(f'<div class="entry"><div class="timestamp">{ts}</div><div>{lines[i+1] if i+1 < len(lines) else ""}</div></div>' for i, ts in enumerate(lines[-10:]) if ts.strip().startswith('## 2025-'))}
            </div>
        </div>
    </main>
    
    <footer>
        <div class="container">
            <p>Generated automatically from Claude session logs</p>
            <p>🏷️ Context tagging • 🧠 AI insights • 🔄 Auto-regeneration</p>
        </div>
    </footer>
</body>
</html>"""

# Write the HTML file
with open(output_dir / "index.html", 'w', encoding='utf-8') as f:
    f.write(html_content)
    
print(f"✅ Simple website generated at docs/index.html")
print(f"📊 Stats: {len(timestamps)} entries, {word_count:,} words")