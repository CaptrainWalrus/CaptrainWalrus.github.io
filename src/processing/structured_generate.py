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

def generate_website():
    """Generate the structured website"""
    # Load template
    template_path = Path("src/templates/main.html")
    if template_path.exists():
        with open(template_path, 'r', encoding='utf-8') as f:
            template = Template(f.read())
    else:
        print("❌ Template not found!")
        return
    
    # Parse session logs
    nt_changes, fluid_changes = parse_session_logs()
    
    # Sort by date (most recent first)
    nt_changes = dict(sorted(nt_changes.items(), reverse=True)[:10])  # Last 10 days
    fluid_changes = dict(sorted(fluid_changes.items(), reverse=True)[:10])
    
    # Add some sample data if empty
    if not nt_changes:
        nt_changes = {
            datetime.now().strftime('%Y-%m-%d'): [
                {'type': 'add', 'description': 'Implemented adaptive risk management system'},
                {'type': 'idea', 'description': 'Exploring Gaussian Process integration for uncertainty modeling'},
            ]
        }
    
    if not fluid_changes:
        fluid_changes = {
            datetime.now().strftime('%Y-%m-%d'): [
                {'type': 'add', 'description': 'Created graduated feature matching system'},
                {'type': 'remove', 'description': 'Removed legacy similarity matching code'},
            ]
        }
    
    # Render template
    html_output = template.render(
        last_updated=datetime.now().strftime('%Y-%m-%d %H:%M'),
        nt_summary="Sophisticated algorithmic trading system with NinjaTrader 8 integration. Features include adaptive risk management, ML-based signal filtering, and real-time market analysis.",
        fluid_summary="Revolutionary agentic memory system using graduated feature matching and range-based intelligence. Learns optimal trading parameters from historical patterns.",
        nt_changes=nt_changes,
        fluid_changes=fluid_changes
    )
    
    # Write output
    output_path = Path("index.html")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_output)
    
    print(f"✅ Structured website generated at {output_path}")
    print(f"📊 NT_OrderManager: {len(nt_changes)} days of changes")
    print(f"📊 FluidJournal: {len(fluid_changes)} days of changes")

if __name__ == "__main__":
    generate_website()