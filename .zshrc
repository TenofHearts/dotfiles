# User configuration and path setup
# Get current user info for robust path handling
USER_HOME="${HOME:-/home/$USER}"
USER_NAME="${USER:-$(whoami)}"

# Validate user home directory exists
if [[ ! -d "$USER_HOME" ]]; then
    echo "Warning: User home directory $USER_HOME does not exist"
fi

# Set up the prompt

autoload -Uz promptinit
promptinit
prompt adam1

setopt histignorealldups sharehistory

# Use emacs keybindings even if our EDITOR is set to vi
bindkey -e

# Keep 1000 lines of history within the shell and save it to ~/.zsh_history:
HISTSIZE=1000
SAVEHIST=1000
HISTFILE=~/.zsh_history

# Use modern completion system
autoload -Uz compinit
compinit

zstyle ':completion:*' auto-description 'specify: %d'
zstyle ':completion:*' completer _expand _complete _correct _approximate
zstyle ':completion:*' format 'Completing %d'
zstyle ':completion:*' group-name ''
zstyle ':completion:*' menu select=2
eval "$(dircolors -b)"
zstyle ':completion:*:default' list-colors ${(s.:.)LS_COLORS}
zstyle ':completion:*' list-colors ''
zstyle ':completion:*' list-prompt %SAt %p: Hit TAB for more, or the character to insert%s
zstyle ':completion:*' matcher-list '' 'm:{a-z}={A-Z}' 'm:{a-zA-Z}={A-Za-z}' 'r:|[._-]=* r:|=* l:|=*'
zstyle ':completion:*' menu select=long
zstyle ':completion:*' select-prompt %SScrolling active: current selection at %p%s
zstyle ':completion:*' use-compctl false
zstyle ':completion:*' verbose true

zstyle ':completion:*:*:kill:*:processes' list-colors '=(#b) #([0-9]#)*=0=01;31'
zstyle ':completion:*:kill:*' command 'ps -u $USER -o pid,%cpu,tty,cputime,cmd'

# some more ls aliases
alias ll='ls -lAh --color=auto'
alias la='ls -Al'
alias l='ls -CF'
alias cls='clear'

# some aliases added by me
alias ga='git add'
alias gc='git commit'
alias gca='git commit -a'
alias gpu='git push'
alias gpl='git pull'
alias glg='git log --graph --decorate'

# Add miniconda to PATH if it exists
MINICONDA_PATH="$USER_HOME/miniconda3/bin"
if [[ -d "$MINICONDA_PATH" ]]; then
    export PATH=$PATH:$MINICONDA_PATH
fi

export NEMU_HOME="$USER_HOME/Programing/PA/ics2024/nemu"
export AM_HOME="$USER_HOME/Programing/PA/ics2024/abstract-machine"
export PATH="/usr/lib/ccache:$PATH"

export NAVY_HOME="$USER_HOME/Programing/PA/ics2024/navy-apps"

alias cact='conda activate'
alias cdac='conda deactivate'

# Add local bin to PATH if it exists
LOCAL_BIN_PATH="$USER_HOME/.local/bin"
if [[ -d "$LOCAL_BIN_PATH" ]]; then
    export PATH=$PATH:$LOCAL_BIN_PATH
fi

eval "$(oh-my-posh init zsh --config $USER_HOME/dotfiles/my_theme.omp.json)"

# >>> conda initialize >>>
# !! Contents within this block are managed by 'conda init' !!
__conda_setup="$( "$USER_HOME/miniconda3/bin/conda" shell.zsh hook 2> /dev/null )"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "$USER_HOME/miniconda3/etc/profile.d/conda.sh" ]; then
        . "$USER_HOME/miniconda3/etc/profile.d/conda.sh"
    else
        export PATH="$USER_HOME/miniconda3/bin:$PATH"
    fi
fi
unset __conda_setup
# <<< conda initialize <<<

# Load autojump if available
AUTOJUMP_SCRIPT="$USER_HOME/.autojump/etc/profile.d/autojump.sh"
[[ -s "$AUTOJUMP_SCRIPT" ]] && source "$AUTOJUMP_SCRIPT"

autoload -U compinit && compinit -u

# Load zsh plugins if available
ZSH_AUTOSUGGESTIONS="$USER_HOME/.zsh/zsh-autosuggestions/zsh-autosuggestions.zsh"
ZSH_HIGHLIGHTING="$USER_HOME/.zsh/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh"

[[ -f "$ZSH_AUTOSUGGESTIONS" ]] && source "$ZSH_AUTOSUGGESTIONS"
[[ -f "$ZSH_HIGHLIGHTING" ]] && source "$ZSH_HIGHLIGHTING"

ZSH_HIGHLIGHT_STYLES[builtin]='fg=114'
ZSH_HIGHLIGHT_STYLES[command]='fg=114'
ZSH_HIGHLIGHT_STYLES[path]='fg=182'
ZSH_HIGHLIGHT_STYLES[alias]='fg=114'
ZSH_HIGHLIGHT_STYLES[function]='fg=067'
ZSH_HIGHLIGHT_STYLES[precommand]='fg=035, bold'

# setopt autocd
# setopt correct

# export PATH="$USER_HOME/.elan/bin:$PATH"

# alias sprox='$USER_HOME/dotfiles/set_proxy.sh'

# Display welcome message if fortune and cowsay are available
if command -v fortune > /dev/null && command -v cowsay > /dev/null; then
		# export COWPATH="$USER_HOME/dotfiles/.cowsay:$COWPATH"
		COWSAY_FILE="$USER_HOME/dotfiles/.cowsay/stegosaurus_and_cat.cow"
		if command -v lolcat > /dev/null; then
				[[ -f "$COWSAY_FILE" ]] && fortune | cowsay -f "$COWSAY_FILE" | lolcat
		else
    		[[ -f "$COWSAY_FILE" ]] && fortune | cowsay -f "$COWSAY_FILE"
		fi
fi

if [ -x /usr/local/cuda-12.9/bin/nvcc ] && [[ ":$PATH:" != *":/usr/local/cuda-12.9/bin:"* ]]; then
    # echo "✅ CUDA env not yet set, now exporting..."
    export PATH=/usr/local/cuda-12.9/bin:$PATH
    export LD_LIBRARY_PATH=/usr/local/cuda-12.9/lib64:$LD_LIBRARY_PATH
    export CUDA_HOME=/usr/local/cuda-12.9
fi

UV_HOME="$USER_HOME/.local/bin"
if [[ -d "$UV_HOME" ]]; then
    export PATH="$UV_HOME:$PATH"
    eval "$(uv generate-shell-completion zsh)"
    eval "$(uvx --generate-shell-completion zsh)"
    function uvac() {
        if [[ -d ".venv" ]]; then
            source .venv/bin/activate
        else
            echo "\033[0;31mNo .venv directory found in the current path.\033[0m"
        fi
    }
fi

export GEM_HOME="$USER_HOME/.gem"
export PATH="$USER_HOME/.gem/bin:$PATH"

# export web ports
export http_proxy=http://127.0.0.1:7897
export https_proxy=http://127.0.0.1:7897
export all_proxy=http://127.0.0.1:7897
