#!/bin/bash

# Exit on error
set -e

# Function to display help
show_help() {
    echo "Transaction Monitoring System Release Script"
    echo ""
    echo "Usage: ./create_release.sh [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help                 Show this help message"
    echo "  -v, --version VERSION      Version number for the release (required)"
    echo "  -m, --message MESSAGE      Release message (optional)"
    echo "  -b, --branch BRANCH        Branch to create release from (default: main)"
    echo "  -t, --tag                  Create a git tag for the release"
    echo "  -c, --changelog            Generate changelog"
    echo "  -d, --docker               Build and tag Docker image"
    echo "  -p, --push                 Push changes to remote repository"
    echo ""
    echo "Examples:"
    echo "  ./create_release.sh -v 1.0.0 -m \"Initial release\" -t -c  Create release 1.0.0 with tag and changelog"
    echo "  ./create_release.sh -v 1.1.0 -b develop -d -p            Create release 1.1.0 from develop branch, build Docker image, and push"
}

# Default values
VERSION=""
MESSAGE=""
BRANCH="main"
TAG=false
CHANGELOG=false
DOCKER=false
PUSH=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            show_help
            exit 0
            ;;
        -v|--version)
            VERSION="$2"
            shift 2
            ;;
        -m|--message)
            MESSAGE="$2"
            shift 2
            ;;
        -b|--branch)
            BRANCH="$2"
            shift 2
            ;;
        -t|--tag)
            TAG=true
            shift
            ;;
        -c|--changelog)
            CHANGELOG=true
            shift
            ;;
        -d|--docker)
            DOCKER=true
            shift
            ;;
        -p|--push)
            PUSH=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Check if version is specified
if [ -z "$VERSION" ]; then
    echo "Error: Version must be specified with -v or --version"
    show_help
    exit 1
fi

# Check if we're on the correct branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" != "$BRANCH" ]; then
    echo "Error: You are on branch $CURRENT_BRANCH, but release should be created from branch $BRANCH"
    echo "Please switch to branch $BRANCH and try again."
    exit 1
fi

# Check if working directory is clean
if [ -n "$(git status --porcelain)" ]; then
    echo "Error: Working directory is not clean. Please commit or stash your changes before creating a release."
    exit 1
fi

# Pull latest changes
echo "Pulling latest changes from $BRANCH..."
git pull origin "$BRANCH"

# Update version in files
echo "Updating version to $VERSION in files..."

# Update version in __init__.py
if [ -f "transaction_monitoring/__init__.py" ]; then
    sed -i "s/__version__ = .*/__version__ = '$VERSION'/" transaction_monitoring/__init__.py
elif [ -f "__init__.py" ]; then
    sed -i "s/__version__ = .*/__version__ = '$VERSION'/" __init__.py
fi

# Update version in package.json if it exists
if [ -f "package.json" ]; then
    sed -i "s/\"version\": \".*\"/\"version\": \"$VERSION\"/" package.json
fi

# Generate changelog
if [ "$CHANGELOG" = true ]; then
    echo "Generating changelog..."
    
    # Create changelog directory if it doesn't exist
    mkdir -p changelog
    
    # Generate changelog
    PREV_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
    if [ -n "$PREV_TAG" ]; then
        echo "# Changelog for version $VERSION" > "changelog/CHANGELOG-$VERSION.md"
        echo "" >> "changelog/CHANGELOG-$VERSION.md"
        echo "## Changes since $PREV_TAG" >> "changelog/CHANGELOG-$VERSION.md"
        echo "" >> "changelog/CHANGELOG-$VERSION.md"
        git log "$PREV_TAG..HEAD" --pretty=format:"* %s (%h)" >> "changelog/CHANGELOG-$VERSION.md"
    else
        echo "# Changelog for version $VERSION" > "changelog/CHANGELOG-$VERSION.md"
        echo "" >> "changelog/CHANGELOG-$VERSION.md"
        echo "## Initial release" >> "changelog/CHANGELOG-$VERSION.md"
        echo "" >> "changelog/CHANGELOG-$VERSION.md"
        git log --pretty=format:"* %s (%h)" >> "changelog/CHANGELOG-$VERSION.md"
    fi
    
    # Add changelog to git
    git add "changelog/CHANGELOG-$VERSION.md"
fi

# Commit changes
echo "Committing version changes..."
git add -u
if [ -n "$MESSAGE" ]; then
    git commit -m "Release $VERSION: $MESSAGE"
else
    git commit -m "Release $VERSION"
fi

# Create tag
if [ "$TAG" = true ]; then
    echo "Creating tag v$VERSION..."
    if [ -n "$MESSAGE" ]; then
        git tag -a "v$VERSION" -m "$MESSAGE"
    else
        git tag -a "v$VERSION" -m "Release $VERSION"
    fi
fi

# Build Docker image
if [ "$DOCKER" = true ]; then
    echo "Building Docker image..."
    docker build -t "transaction-monitoring:$VERSION" .
    docker tag "transaction-monitoring:$VERSION" "transaction-monitoring:latest"
fi

# Push changes
if [ "$PUSH" = true ]; then
    echo "Pushing changes to remote repository..."
    git push origin "$BRANCH"
    
    if [ "$TAG" = true ]; then
        echo "Pushing tag to remote repository..."
        git push origin "v$VERSION"
    fi
    
    if [ "$DOCKER" = true ]; then
        echo "Pushing Docker image to registry..."
        # Uncomment and modify the following lines to push to a Docker registry
        # docker tag "transaction-monitoring:$VERSION" "your-registry/transaction-monitoring:$VERSION"
        # docker tag "transaction-monitoring:$VERSION" "your-registry/transaction-monitoring:latest"
        # docker push "your-registry/transaction-monitoring:$VERSION"
        # docker push "your-registry/transaction-monitoring:latest"
    fi
fi

echo "Release $VERSION created successfully!"