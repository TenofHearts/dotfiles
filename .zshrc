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

export PATH=$PATH:/home/ten_of_hearts/miniconda3/bin/

export NEMU_HOME=/home/ten_of_hearts/Programing/PA/ics2024/nemu
export AM_HOME=/home/ten_of_hearts/Programing/PA/ics2024/abstract-machine
export PATH="/usr/lib/ccache:$PATH"

export NAVY_HOME=/home/ten_of_hearts/Programing/PA/ics2024/navy-apps

alias cact='conda activate'
alias cdac='conda deactivate'

export PATH=$PATH:/home/ten_of_hearts/.local/bin

eval "$(oh-my-posh init zsh --config ~/dotfiles/my_theme.omp.json)"

# >>> conda initialize >>>
# !! Contents within this block are managed by 'conda init' !!
__conda_setup="$('/home/ten_of_hearts/miniconda3/bin/conda' 'shell.zsh' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "/home/ten_of_hearts/miniconda3/etc/profile.d/conda.sh" ]; then
        . "/home/ten_of_hearts/miniconda3/etc/profile.d/conda.sh"
    else
        export PATH="/home/ten_of_hearts/miniconda3/bin:$PATH"
    fi
fi
unset __conda_setup
# <<< conda initialize <<<

[[ -s /home/ten_of_hearts/.autojump/etc/profile.d/autojump.sh ]] && source /home/ten_of_hearts/.autojump/etc/profile.d/autojump.sh

autoload -U compinit && compinit -u

source ~/.zsh/zsh-autosuggestions/zsh-autosuggestions.zsh
source /home/ten_of_hearts/.zsh/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh

ZSH_HIGHLIGHT_STYLES[builtin]='fg=114'
ZSH_HIGHLIGHT_STYLES[command]='fg=114'
ZSH_HIGHLIGHT_STYLES[path]='fg=182'
ZSH_HIGHLIGHT_STYLES[alias]='fg=114'
ZSH_HIGHLIGHT_STYLES[function]='fg=067'
ZSH_HIGHLIGHT_STYLES[precommand]='fg=035, bold'

# setopt autocd
# setopt correct
