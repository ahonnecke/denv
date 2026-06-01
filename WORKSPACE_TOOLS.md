# Workspace Tools

Tools for managing parallel working directories (workspaces) with git.

## Files

- `bin/workspace-summary.py` - Generic workspace status tool
- `bin/ccs` - Wrapper for crewcapableai workspaces
- `bin/crew-claude-summary.py` - Legacy name (kept for compatibility)

## Usage

### Generic Tool

The `workspace-summary.py` script works with any project that has numbered workspaces:

```bash
# Show status of all myproject.* directories
workspace-summary.py myproject

# Find empty workspace
workspace-summary.py myproject --find-empty

# Custom symlink prefix (default: first 2 chars of project name)
workspace-summary.py myproject --symlink-prefix mp
```

**Example projects it works with:**
- `myproject.0`, `myproject.1`, `myproject.2` → creates `mp.*` symlinks
- `webapp.0`, `webapp.1` → creates `we.*` symlinks
- `api.0`, `api.1`, `api.2` → creates `ap.*` symlinks

### Project-Specific Wrapper: `ccs`

The `ccs` command is a wrapper that defaults to `crewcapableai` workspaces:

```bash
# Show status of all crewcapableai.* workspaces
ccs

# Find empty crewcapableai workspace
ccs --find-empty

# Use with shell function to cd to empty workspace
cce  # defined in ~/.clauderc
```

Equivalent to:
```bash
workspace-summary.py crewcapableai --symlink-prefix cc
```

## Features

- **Git Status**: Shows modified, added, deleted, untracked files
- **Requirements Highlighting**: Special attention to `requirements/` directory changes
- **Server Detection**: Shows if a dev server is running (ports 3000, 8000, 8080, 5000, 4200)
- **Auto Symlinks**: Creates `~/src/<prefix>.<taskname>` symlinks based on branch names
- **Clean Detection**: Identifies workspaces with no changes (useful with `--find-empty`)

## Output Example

```
================================================================================
CREWCAPABLEAI - PARALLEL WORKING DIRECTORIES STATUS
================================================================================

📁 crewcapableai.0 (branch: FEATURE/export-to-erp) 🚀 SERVER:PORT-3000 → ~/src/cc.export-to-erp
--------------------------------------------------------------------------------
   Modified: 12 file(s)
      📝 apps/web/app/page.tsx
      📝 packages/core/src/api.ts
      ... and 10 more

📁 crewcapableai.1 (branch: TASK/sh-to-py) → ~/src/cc.sh-to-py
   ✓ Clean working directory

📁 crewcapableai.2 (branch: main)
   ✓ Clean working directory
```

## Creating New Wrappers

To create a wrapper for another project:

```bash
#!/usr/bin/env bash
# ~/bin/myapp-status

# Get script directory (handles symlinks)
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
  DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
SCRIPT_DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"

# Call workspace-summary.py with your project prefix and symlink prefix
exec "$SCRIPT_DIR/workspace-summary.py" myproject --symlink-prefix mp "$@"
```

Make it executable and symlink from `~/bin`:
```bash
chmod +x ~/src/denv/bin/myapp-status
ln -sf ~/src/denv/bin/myapp-status ~/bin/myapp-status
```

## Shell Integration

Add to `~/.bashrc` or `~/.clauderc`:

```bash
# cd to empty crewcapableai workspace
cce() {
    local empty_workspace=$(ccs --find-empty)
    if [ -n "$empty_workspace" ]; then
        cd "$empty_workspace"
    else
        echo "No empty workspace found" >&2
        return 1
    fi
}

# cd to empty workspace for any project
cde() {
    local project="${1:-crewcapableai}"
    local empty_workspace=$(workspace-summary.py "$project" --find-empty)
    if [ -n "$empty_workspace" ]; then
        cd "$empty_workspace"
    else
        echo "No empty $project workspace found" >&2
        return 1
    fi
}
```

Then use:
```bash
cce                    # cd to empty crewcapableai workspace
cde myproject          # cd to empty myproject workspace
```
