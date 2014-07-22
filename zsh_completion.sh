_green_completion() {
    local word completions
    word="$1"
    completions="$(green --completions "${word}")"
    reply=( "${(ps:\n:)completions}" )
}

compctl -K _green_completion green
