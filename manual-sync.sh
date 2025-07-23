#!/bin/bash
#
# Manual sync script for session logs
# Run this anytime to sync session logs to Cohere directory
#

echo "🔄 Manual Session Log Sync"
echo "=========================="

# Run the same sync logic as the pre-commit hook
/mnt/c/workspace/Cohere/git-hooks/pre-commit

echo ""
echo "📊 Sync Status:"
echo "   Last sync: $(cat /mnt/c/workspace/Cohere/session-logs/.sync_timestamp 2>/dev/null || echo 'Never')"
echo "   Files in session-logs:"

# List synced files
find /mnt/c/workspace/Cohere/session-logs -name "*.md" -type f | while read file; do
    relative_path=${file#/mnt/c/workspace/Cohere/session-logs/}
    file_size=$(wc -l < "$file" 2>/dev/null || echo "0")
    echo "     - $relative_path ($file_size lines)"
done

echo ""
echo "✅ Manual sync complete!"
echo "💡 Tip: This happens automatically on git commits"