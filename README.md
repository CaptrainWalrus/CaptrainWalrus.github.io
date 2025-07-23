# Development Journey Auto-Regen Website

This repository automatically generates a website from Claude session logs using LangChain.

## 🚀 Live Site
https://captrainwalrus.github.io/dev-journey

## How It Works

1. **Session logs** are stored in `session-logs/` directory
2. **GitHub Actions** trigger on commits to session files
3. **LangChain** processes the logs to extract insights
4. **Website** regenerates automatically with new content
5. **GitHub Pages** serves the updated site

## Repository Structure

```
dev-journey/
├── session-logs/
│   ├── claude_memory.md          # Main session log
│   └── projects/
│       ├── trading-system/
│       │   └── claude_memory.md
│       └── cohere/
│           └── claude_memory.md
├── src/
│   ├── processing/
│   │   ├── langchain_processor.py
│   │   ├── generate_html.py
│   │   └── requirements.txt
│   ├── templates/
│   │   └── index.html
│   └── static/
│       ├── style.css
│       └── script.js
├── docs/                         # Generated website (GitHub Pages)
├── .github/
│   └── workflows/
│       └── build-site.yml
└── README.md
```

## Setup Instructions

### 1. Add Your Session Logs
Copy your existing `claude_memory.md` files to the `session-logs/` directory.

### 2. Configure Secrets
In your repository settings, add these secrets:
- `OPENAI_API_KEY`: Your OpenAI API key
- `LANGCHAIN_API_KEY`: Your LangChain API key (optional for free tier)

### 3. Enable GitHub Pages
- Go to Settings → Pages
- Source: Deploy from a branch
- Branch: main
- Folder: /docs

### 4. Trigger First Build
Commit any change to a file in `session-logs/` to trigger the first build.

## Manual Build
To test locally:
```bash
pip install -r src/processing/requirements.txt
python src/processing/langchain_processor.py
python src/processing/generate_html.py
```

## Custom Domain (Optional)
To use a custom domain:
1. Add `CNAME` file to repository root
2. Configure DNS settings
3. Enable custom domain in GitHub Pages settings