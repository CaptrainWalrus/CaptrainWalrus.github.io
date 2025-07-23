# GitHub + LangChain Auto-Regen Workflow

## Architecture Overview

```
GitHub Repo (claude_memory.md) → GitHub Actions → LangChain Processing → Website Update
```

## Repository Structure

### Source Repository (Your Session Logs)
```
my-claude-sessions/
├── claude_memory.md          # Main session log
├── project-a/
│   └── claude_memory.md      # Project-specific logs
├── project-b/
│   └── claude_memory.md
└── .github/
    └── workflows/
        └── trigger-regen.yml  # Webhook to website repo
```

### Website Repository (Generated Content)
```
my-dev-website/
├── src/
│   ├── content/              # Generated content
│   ├── templates/            # Website templates
│   └── processing/
│       ├── langchain_processor.py
│       ├── requirements.txt
│       └── config.yml
├── docs/                     # Generated website (GitHub Pages)
├── .github/
│   └── workflows/
│       └── regen-content.yml # LangChain processing
└── README.md
```

## Workflow Steps

### 1. Trigger Event (Session Repo)
**When you commit to `claude_memory.md`:**

```yaml
# .github/workflows/trigger-regen.yml
name: Trigger Website Regeneration
on:
  push:
    paths:
      - '**/*claude_memory.md'
      - '**/CLAUDE.md'

jobs:
  trigger:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger website rebuild
        uses: peter-evans/repository-dispatch@v2
        with:
          token: ${{ secrets.TRIGGER_TOKEN }}
          repository: yourusername/my-dev-website
          event-type: content-update
          client-payload: |
            {
              "source_repo": "${{ github.repository }}",
              "commit_sha": "${{ github.sha }}",
              "changed_files": "${{ github.event.head_commit.modified }}"
            }
```

### 2. Content Processing (Website Repo)
**LangChain processes the session logs:**

```yaml
# .github/workflows/regen-content.yml
name: Regenerate Website Content
on:
  repository_dispatch:
    types: [content-update]
  workflow_dispatch:

jobs:
  regenerate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          pip install -r src/processing/requirements.txt
          
      - name: Fetch latest session logs
        run: |
          # Clone or fetch from session repos
          git clone https://github.com/${{ github.event.client_payload.source_repo }} session-logs
          
      - name: Process with LangChain
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          LANGCHAIN_API_KEY: ${{ secrets.LANGCHAIN_API_KEY }}
        run: |
          python src/processing/langchain_processor.py
          
      - name: Build website
        run: |
          # Generate static site (Jekyll/Hugo/etc)
          npm run build
          
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./docs
```

## LangChain Processing Script

### Core Processor (`langchain_processor.py`)
```python
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
import json
from datetime import datetime

class SessionLogProcessor:
    def __init__(self):
        self.llm = OpenAI(temperature=0.3)
        self.setup_chains()
    
    def setup_chains(self):
        # Chain for extracting insights
        insight_template = PromptTemplate(
            input_variables=["session_content"],
            template="""
            Analyze this Claude development session log and extract key insights:
            
            {session_content}
            
            Provide:
            1. Major breakthroughs or achievements
            2. Key problems encountered and solutions
            3. Learning patterns and development velocity
            4. Overall progress themes
            
            Format as structured markdown for website content.
            """
        )
        self.insight_chain = LLMChain(llm=self.llm, prompt=insight_template)
        
        # Chain for generating summaries
        summary_template = PromptTemplate(
            input_variables=["insights"],
            template="""
            Create a compelling website section from these development insights:
            
            {insights}
            
            Write engaging content that shows:
            - What's being built and why
            - Development momentum and obstacles
            - Key learnings and pattern recognition
            - Current focus and next steps
            
            Use a narrative style that speaks to the development journey.
            """
        )
        self.summary_chain = LLMChain(llm=self.llm, prompt=summary_template)
    
    def process_session_logs(self):
        # Read all claude_memory.md files
        session_files = self.find_session_files()
        
        all_content = []
        for file_path in session_files:
            content = self.read_file(file_path)
            insights = self.insight_chain.run(session_content=content)
            all_content.append({
                'file': file_path,
                'insights': insights,
                'timestamp': datetime.now().isoformat()
            })
        
        # Generate website content
        combined_insights = "\n\n".join([c['insights'] for c in all_content])
        website_content = self.summary_chain.run(insights=combined_insights)
        
        # Save generated content
        self.save_website_content(website_content, all_content)
    
    def find_session_files(self):
        session_files = []
        for root, dirs, files in os.walk('session-logs'):
            for file in files:
                if file == 'claude_memory.md' or file == 'CLAUDE.md':
                    session_files.append(os.path.join(root, file))
        return session_files
    
    def save_website_content(self, content, metadata):
        # Save main content
        with open('src/content/index.md', 'w') as f:
            f.write(content)
        
        # Save metadata for templates
        with open('src/content/metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)

if __name__ == "__main__":
    processor = SessionLogProcessor()
    processor.process_session_logs()
```

## Website Templates

### Main Page Template
```html
<!-- src/templates/index.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Development Journey</title>
    <style>
        /* Clean, modern styling */
        body { font-family: 'Inter', sans-serif; line-height: 1.6; }
        .progress-section { margin: 2rem 0; }
        .timestamp { color: #666; font-size: 0.9em; }
    </style>
</head>
<body>
    <header>
        <h1>Development Journey</h1>
        <p>Auto-generated insights from development sessions</p>
    </header>
    
    <main>
        <div id="content">
            <!-- LangChain generated content inserted here -->
            {{ generated_content }}
        </div>
        
        <div class="metadata">
            <h3>Recent Activity</h3>
            <!-- Loop through recent sessions -->
            {% for session in recent_sessions %}
            <div class="session-item">
                <span class="timestamp">{{ session.timestamp }}</span>
                <span class="project">{{ session.project }}</span>
            </div>
            {% endfor %}
        </div>
    </main>
    
    <footer>
        <p>Last updated: {{ last_update }}</p>
    </footer>
</body>
</html>
```

## Benefits of This Approach

### 1. **Automatic Updates**
- Every commit to session logs triggers website regeneration
- No manual intervention required
- Always reflects latest development state

### 2. **LangChain Intelligence**
- Extracts meaningful insights from raw session logs
- Generates engaging narrative content
- Identifies patterns across multiple projects

### 3. **GitHub Integration**
- Uses GitHub's free tier (Actions + Pages)
- Version controlled content and processing
- Easy to modify and extend

### 4. **Scalable Architecture**
- Supports multiple session log repositories
- Easy to add new projects
- Modular processing pipeline

## Setup Steps

### 1. Create Repositories
```bash
# Session logs repo
gh repo create my-claude-sessions --private
cd my-claude-sessions
echo "# Claude Session Logs" > README.md
mkdir .github/workflows
# Add workflow files

# Website repo
gh repo create my-dev-website --public
cd my-dev-website
mkdir -p src/{content,templates,processing}
mkdir .github/workflows
# Add processing code
```

### 2. Configure Secrets
```bash
# In website repo settings
OPENAI_API_KEY=your_openai_key
LANGCHAIN_API_KEY=your_langchain_key
TRIGGER_TOKEN=github_personal_access_token
```

### 3. Enable GitHub Pages
- Go to website repo settings
- Enable Pages from `/docs` folder
- Your site will be at `yourusername.github.io/my-dev-website`

## Result

Every time you commit to `claude_memory.md`, your website automatically:
1. **Fetches** the latest session logs
2. **Processes** them with LangChain
3. **Generates** new website content
4. **Deploys** to your custom domain

The website shows intelligent aggregations of your development journey, not just commit logs!