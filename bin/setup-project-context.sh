#!/usr/bin/env bash
# Setup script to install .envrc with project context support
# Usage: setup-project-context.sh <target-directory> <project-base-name>

set -e

if [ $# -lt 2 ]; then
    echo "Usage: $0 <target-directory> <project-base-name>"
    echo "Example: $0 /home/user/src/myproject 'My Project'"
    exit 1
fi

TARGET_DIR="$1"
PROJECT_BASE_NAME="$2"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -d "$TARGET_DIR" ]; then
    echo "Error: Directory $TARGET_DIR does not exist"
    exit 1
fi

if [ ! -f "$SCRIPT_DIR/.envrc.template" ]; then
    echo "Error: Template file $SCRIPT_DIR/.envrc.template not found"
    exit 1
fi

# Create .envrc from template
sed "s/{{PROJECT_BASE_NAME}}/$PROJECT_BASE_NAME/g" "$SCRIPT_DIR/.envrc.template" > "$TARGET_DIR/.envrc"

echo "Created $TARGET_DIR/.envrc"
echo "Now run: cd $TARGET_DIR && direnv allow"
