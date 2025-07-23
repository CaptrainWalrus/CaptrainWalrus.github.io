#!/bin/bash
#
# Install Git hooks for automatic session log syncing
#

echo "🔧 Installing Git hooks for session log syncing..."

# Function to install hook in a repository
install_hook() {
    local repo_dir="$1"
    local repo_name="$2"
    
    if [ -d "$repo_dir/.git" ]; then
        echo "📁 Installing hook in $repo_name..."
        
        # Copy pre-commit hook
        cp "/mnt/c/workspace/Cohere/git-hooks/pre-commit" "$repo_dir/.git/hooks/pre-commit"
        chmod +x "$repo_dir/.git/hooks/pre-commit"
        
        echo "  ✅ Hook installed: $repo_dir/.git/hooks/pre-commit"
    else
        echo "  ⚠️ Not a git repository: $repo_dir"
    fi
}

# Install in main workspace (if it's a git repo)
install_hook "/mnt/c/workspace" "Main Workspace"

# Install in Cohere directory
install_hook "/mnt/c/workspace/Cohere" "Cohere Project"

# Install in FluidJournal (if it exists and is a git repo)
install_hook "/mnt/c/workspace/FluidJournal" "FluidJournal"

# Install in any other project directories that are git repos
for dir in /mnt/c/workspace/*/; do
    if [ -d "$dir/.git" ] && [[ "$dir" != *"Cohere"* ]]; then
        project_name=$(basename "$dir")
        install_hook "$dir" "$project_name"
    fi
done

echo ""
echo "✅ Git hooks installation complete!"
echo ""
echo "📋 What this does:"
echo "   - Before every 'git commit', session logs are automatically synced"
echo "   - claude_memory.md files are copied to Cohere/session-logs/"
echo "   - Project-specific logs go to session-logs/projects/"
echo "   - Changes are automatically staged in Cohere repository"
echo ""
echo "🚀 Usage:"
echo "   Just commit normally: git commit -m \"your message\""
echo "   Session logs will sync automatically!"
echo ""
echo "🔄 Manual sync:"
echo "   Run: /mnt/c/workspace/Cohere/git-hooks/pre-commit"