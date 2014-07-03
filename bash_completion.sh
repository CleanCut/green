_green_completion() 
{
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    shortopts="$(green --short-options)"
    longopts="$(green --long-options)"
    allopts="${shortopts} ${longopts}"
 
    case "${prev}" in
        *)
        ;;
    esac

    case "${cur}" in
        --*)
            COMPREPLY=( $(compgen -W "${longopts}" -- ${cur}) )
            return 0
            ;;
        -*) 
            COMPREPLY=( $(compgen -W "${allopts}" -- ${cur}) )
            return 0
            ;;
    esac

    COMPREPLY=( $(compgen -W "$(green --completions ${cur})" -- ${cur}) )
}
complete -F _green_completion green
