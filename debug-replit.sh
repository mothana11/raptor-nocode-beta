#!/usr/bin/env bash

echo "🔍 Debugging Replit Setup..."
echo "Current directory: $(pwd)"
echo "Files in current directory:"
ls -la

echo ""
echo "📄 .replit file contents:"
cat .replit

echo ""
echo "📄 start-replit.sh file contents:"
cat start-replit.sh

echo ""
echo "✅ Replit setup verification complete" 