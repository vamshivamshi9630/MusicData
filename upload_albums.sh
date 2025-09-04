#!/bin/bash

# Ensure script stops on error
set -e

# Ask for commit message
read -p "Enter commit message: " commit_message

# Step 1: Run the Python script to regenerate songs.json
echo "🎼 Running Python script to update songs.json..."
python generate_songs_json.py

# Step 2: Stage all changes (new folders, mp3s, updated json, etc.)
echo "📁 Staging all changes..."
git add .

# Step 3: Commit
echo "✅ Committing with message: $commit_message"
git commit -m "$commit_message"

# Step 4: Push to remote
echo "🚀 Pushing to GitHub..."
git push origin main

echo "🎉 Done! Albums uploaded and songs.json updated."
