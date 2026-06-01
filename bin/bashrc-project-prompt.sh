#!/usr/bin/env bash
# Add this to your ~/.bashrc to show PROJECT_NAME in prompt
# Source: ~/bin/bashrc-project-prompt.sh

# Function to get project context for prompt
__project_context() {
    if [ -n "$PROJECT_NAME" ]; then
        echo "[$PROJECT_NAME] "
    fi
}

# Update PS1 to include project context
# Place this AFTER your existing PS1 configuration

if [ "$color_prompt" = yes ]; then
    PS1='\[\033[01;35m\]$(__project_context)\[\033[00m\]${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '
else
    PS1='$(__project_context)${debian_chroot:+($debian_chroot)}\u@\h:\w\$ '
fi

# If this is an xterm set the title to include project
case "$TERM" in
xterm*|rxvt*)
    PS1="\[\e]0;${debian_chroot:+($debian_chroot)}\u@\h: \w\a\]$PS1"
    ;;
*)
    ;;
esac
