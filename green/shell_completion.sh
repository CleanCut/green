# zsh version
if [ -n "$ZSH_VERSION" ]; then
    _green_completion() {
        local word completions
        word="$1"
        case "${word}" in
            -*)
                completions="$(green --options)"
                ;;
            *)
                completions="$(green --completions "${word}")"
                ;;
        esac
        reply=( "${(ps:\n:)completions}" )
    }

    compctl -K _green_completion green

# bash version
elif [ -n "$BASH_VERSION" ]; then
    _green_completion() {
        local word opts
        COMPREPLY=()
        word="${COMP_WORDS[COMP_CWORD]}"
        opts="$(green --options)"
        case "${word}" in
            -*) 
                COMPREPLY=( $(compgen -W "${opts}" -- ${word}) )
                return 0
                ;;
        esac
        COMPREPLY=( $(compgen -W "$(green --completions ${word} | tr '\n' ' ')" -- ${word}) )
    }
    complete -F _green_completion green
fi
