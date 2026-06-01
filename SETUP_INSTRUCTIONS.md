# Project Context Setup with direnv

This setup allows you to have dynamic project context in your shell prompt that updates based on `./requirements/current_requirement`.

## Files Created

1. **~/.clauderc** - Updated with prompt integration (already sourced by .bashrc)
2. **~/bin/.envrc.template** - Template for project .envrc files
3. **~/bin/setup-project-context.sh** - Helper script to install .envrc

## How to Use

### For a new project directory:

```bash
# 1. Setup .envrc in your project directory
~/bin/setup-project-context.sh /path/to/project "Project Name"

# 2. Allow direnv to use it
cd /path/to/project
direnv allow

# 3. Create requirements directory and set current requirement
mkdir -p requirements
echo "Feature: Add authentication" > requirements/current_requirement
```

### Example with crew-claude-summary:

```bash
# Setup for crew-claude-summary project
cd /home/ahonnecke/src/home/bin
~/bin/setup-project-context.sh . "crew-claude-summary"
direnv allow

# Create requirements structure
mkdir -p requirements
echo "Fix API timeout issue" > requirements/current_requirement

# Now when you cd here, your prompt will show:
# [crew-claude-summary: Fix API timeout issue] user@host:~/src/home/bin$
```

### Switching between features:

```bash
# Just update the current_requirement file
echo "Add logging functionality" > requirements/current_requirement

# Exit and re-enter directory (or run: direnv reload)
cd .. && cd -

# Prompt now shows:
# [crew-claude-summary: Add logging functionality] user@host:~/src/home/bin$
```

## How It Works

1. When you `cd` into a directory with `.envrc`, direnv runs it
2. The `.envrc` reads `requirements/current_requirement` if it exists
3. Sets `$PROJECT_NAME` environment variable
4. Your prompt (configured in `~/.clauderc`) displays the project context in magenta

## Tips

- Keep `requirements/current_requirement` to a single line (first line is used)
- The prompt prefix shows in **magenta/purple** color
- If no `requirements/current_requirement` exists, just the base project name shows
- You can put any text in `current_requirement` - ticket numbers, feature names, etc.
