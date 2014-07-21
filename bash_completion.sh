_green_completion() 
{
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts="$(green --options)"
 
    case "${prev}" in
        *)
        ;;
    esac

    case "${cur}" in
        -*) 
            COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
            return 0
            ;;
    esac

    COMPREPLY=( $(compgen -W "$(green --completions ${cur})" -- ${cur}) )
}
complete -F _green_completion green
