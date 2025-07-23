# Cohere LangChain Auto-Regen Website Project

## Project Overview

This project creates a no-code concept for an auto-regenerating website using LangChain that pulls content from Claude session logs and creates meaningful aggregations of development progress and failures.

## Current Session Model
- **Model**: Sonnet 4 (claude-sonnet-4-20250514)
- **Started**: 2025-07-23
- **Focus**: Auto-regen website with commit-based refresh from Claude session logs

## Core Concept

### Auto-Regen Architecture
- **Source**: Claude session logs like @claude_memory.md from various projects
- **Processing**: LangChain-based content aggregation and transformation
- **Output**: Website content that speaks to progress/failures, not just commit summaries
- **Refresh**: Commit-based updates from git repositories hosting session files

### Key Features
1. **Session Aggregation**: Large aggregations of progress or failures across sessions
2. **Intelligent Content**: Context-aware content generation based on session patterns
3. **Auto-Update**: Commit-triggered regeneration when session files change
4. **Multi-Project**: Support for multiple projects with separate session logs

## Project Structure

### Core Components
- **Content Engine**: LangChain pipeline for processing session logs
- **Git Integration**: Webhook/polling system for commit-based updates
- **Website Generator**: Static site generation with dynamic content
- **Domain Hosting**: TBD - will purchase domain for hosting

### Data Flow
```
Git Repo (Session Logs) → LangChain Processor → Content Generation → Website Deployment
```

## Development Standards
- **File Organization**: Keep project files organized and focused
- **Documentation**: Maintain clear documentation for no-code approach
- **Session Tracking**: Project-specific memory system for continuity
- **Git Commit Standards**: NO Claude Code advertising or co-authored-by lines in commits
- **Clean Commits**: Simple, descriptive commit messages without promotional content

## Current Development Status
- ✅ Project structure initialized
- 🔄 Setting up project-specific memory system
- ⏳ LangChain integration research
- ⏳ Architecture design
- ⏳ Domain and hosting planning

## Session Memory System
This project maintains its own memory system separate from other workspace projects to ensure clean session continuity and focused development tracking.

## Notes
- Focus on "progress or failures" aggregations, not commit summaries
- Website should speak to whatever the user is doing across sessions
- No-code approach preferred for initial implementation
- Will need domain purchase and hosting setup
- Auto-generated from Claude session logs • Built with 🤖 and ☕