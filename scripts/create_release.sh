#!/bin/bash

# GitVisionCLI Release Script
# Creates a release tag and pushes to GitHub

set -e

VERSION="2.0.0"
TAG_NAME="v${VERSION}"
RELEASE_MESSAGE="Release v${VERSION} - Comprehensive bug fixes and improvements

Major fixes:
- Fixed :set-ai command routing
- Fixed git command routing  
- Comprehensive ANSI code stripping
- Fixed line operations in editor
- Improved panel synchronization
- Enhanced word number support

See CHANGELOG.md and RELEASE_NOTES_v2.0.0.md for full details."

echo "🚀 Creating release tag v${VERSION}..."
echo ""

# Check if we're on main branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "⚠️  Warning: You're not on main branch. Current branch: $CURRENT_BRANCH"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if there are uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "⚠️  Warning: You have uncommitted changes."
    echo "Please commit or stash them before creating a release tag."
    git status --short
    exit 1
fi

# Check if tag already exists
if git rev-parse "$TAG_NAME" >/dev/null 2>&1; then
    echo "❌ Tag $TAG_NAME already exists!"
    echo "To delete and recreate: git tag -d $TAG_NAME && git push origin :refs/tags/$TAG_NAME"
    exit 1
fi

# Create annotated tag
echo "📝 Creating annotated tag..."
git tag -a "$TAG_NAME" -m "$RELEASE_MESSAGE"

echo ""
echo "✅ Tag created successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Review the tag: git show $TAG_NAME"
echo "2. Push tag to GitHub: git push origin $TAG_NAME"
echo "3. Push commits: git push origin main"
echo ""
echo "Or run both at once:"
echo "   git push origin main && git push origin $TAG_NAME"
echo ""
read -p "Push tag and commits to GitHub now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📤 Pushing to GitHub..."
    git push origin main
    git push origin "$TAG_NAME"
    echo ""
    echo "✅ Release tag pushed to GitHub!"
    echo ""
    echo "🎉 Release v${VERSION} is now live!"
    echo ""
    echo "Next: Create a release on GitHub with the tag $TAG_NAME"
    echo "Use RELEASE_NOTES_v2.0.0.md as the release description."
else
    echo "Tag created locally. Push manually when ready."
fi

