# Project Context with direnv

Dynamic shell prompt that shows your current project and active requirement/feature.

## Features

- **Dynamic Prompts**: Automatically show project name and current requirement in your shell
- **direnv Integration**: Uses direnv to set context when entering directories
- **Colorful Display**: Orange "Claude:", cyan project name, bright green requirement
- **Easy Switching**: Just update `requirements/.current-requirement` to change context

## Files

- `bin/setup-project-context.sh` - Helper to setup `.envrc` in a project
- `templates/.envrc.template` - Template for project `.envrc` files
- `bin/crew-claude-summary.py` - Git status summary + find empty workspace

## Installation

Files are in `~/src/denv` and symlinked from `~/bin`:
- `~/bin/setup-project-context` → `~/src/denv/bin/setup-project-context.sh`
- `~/bin/crew-claude-summary.py` → `~/src/denv/bin/crew-claude-summary.py`
- `~/bin/ccs` → `~/src/denv/bin/crew-claude-summary.py`

Shell integration is in `~/.clauderc` (sourced by `.bashrc`).

## Usage

### Setup a Project

```bash
# Setup .envrc in your project directory
setup-project-context /path/to/project "Project Name"

# Allow direnv to use it
cd /path/to/project
direnv allow

# Create requirements structure
mkdir -p requirements
echo "Feature: Add authentication" > requirements/.current-requirement
```

### Your Prompt Will Show

```
Claude: projectname Feature: Add authentication $
```

With colors:
- **Claude:** in orange
- **projectname** in cyan
- **Feature: Add authentication** in bright green

### Switch Features

```bash
# Just update the file
echo "2025-11-21-new-feature" > requirements/.current-requirement

# Exit and re-enter directory (or: direnv reload)
cd .. && cd -
```

### Find Empty Workspace

```bash
# Find first workspace with clean git status
crew-claude-summary.py --find-empty

# Or use the helper function (defined in ~/.clauderc)
cce  # "cd to crew empty"
```

## How It Works

1. When you `cd` into a directory, direnv loads `.envrc`
2. `.envrc` reads `requirements/.current-requirement` if it exists
3. Sets `$PROJECT_NAME` environment variable
4. Your prompt function (`__project_context` in `~/.clauderc`) displays it with colors
5. The `.envrc` template is automatically deployed by `setup-project-context`

## Template Structure

The `.envrc` template looks like:

```bash
PROJECT_BASE_NAME="{{PROJECT_BASE_NAME}}"

if [ -f "requirements/.current-requirement" ]; then
    CURRENT_REQ=$(cat requirements/.current-requirement | head -n1 | tr -d '\n\r')
    export PROJECT_NAME="${PROJECT_BASE_NAME}: ${CURRENT_REQ}"
else
    export PROJECT_NAME="${PROJECT_BASE_NAME}"
fi
```

## Shell Integration

In `~/.clauderc`:

```bash
# Helper function to cd to an empty workspace
cce() {
    local empty_workspace=$(crew-claude-summary.py --find-empty)
    if [ -n "$empty_workspace" ]; then
        cd "$empty_workspace"
    else
        echo "No empty workspace found" >&2
        return 1
    fi
}

# Project context prompt with colors
__project_context() {
    if [ -n "$PROJECT_NAME" ]; then
        if [[ "$PROJECT_NAME" == *": "* ]]; then
            BASE="${PROJECT_NAME%%: *}"
            REQ="${PROJECT_NAME#*: }"
            printf '\001\033[38;5;208m\002Claude:\001\033[00m\002 \001\033[38;5;51m\002%s\001\033[00m\002 \001\033[1;38;5;46m\002%s\001\033[00m\002 ' "$BASE" "$REQ"
        else
            printf '\001\033[38;5;208m\002Claude:\001\033[00m\002 \001\033[38;5;51m\002%s\001\033[00m\002 ' "$PROJECT_NAME"
        fi
    fi
}

PS1='$(__project_context)\$ '
```

## Tips

- Keep `requirements/.current-requirement` to a single line (first line is used)
- Can contain any text: ticket numbers, feature names, dates, etc.
- Example: `2025-11-20-1251-erp-export`
- The file is hidden (starts with `.`) so it won't clutter directory listings
