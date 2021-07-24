import os
import sys

def watch(original_argv, processed_args):
    if dependenciesMissing():
        return 1

    argv_watch_removed = list(filter(lambda arg: arg != '-w', original_argv))
    new_green_argv = ' '.join(argv_watch_removed)

    # Add the console "clear" command before re-running green.
    new_green_argv = 'clear; ' + new_green_argv


    run_watchmedo_shell_command(new_green_argv, processed_args)

    # Having issues with stray output
    # run_watchmedo_auto_restart(argv_watch_removed)


def dependenciesMissing():
    try:
        import watchdog
    except ImportError:
        print("Error: 'watchdog' library could not be detected. Please install the watchdog library to use the code watching feature.")
        return True

    return False


def run_watchmedo_shell_command(new_green_argv, processed_args):
    watchmedo_args = [
        'watchmedo',
        'shell-command',
        '--patterns="*.py"',
        '--ignore-directories',
        '--recursive',
        f'--command="{new_green_argv}"',
        '--drop',
        *processed_args.targets
    ]

    # This didn't output to the screen... Not sure why.
    # os.execvp(watchmedo_args[0], watchmedo_args)

    os.system(new_green_argv)
    os.system(' '.join(watchmedo_args))



def run_watchmedo_auto_restart(argv_watch_removed):
    watchmedo_auto_restart_args = [
        'watchmedo',
        'auto-restart',
        '--patterns="*.py"',
        '--ignore-directories',
        '--recursive',
        '--',
        *argv_watch_removed,
    ]

    os.system(' '.join(watchmedo_auto_restart_args))
