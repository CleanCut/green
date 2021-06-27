import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from green.runner import run
from green.loader import GreenTestLoader

to_run = True


class GreenEventHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()

    def on_any_event(self, event):
        global to_run
        to_run = True


def watch(stream, args, testing):
    global to_run
    event_handler = GreenEventHandler()

    observer = Observer()
    observer.schedule(event_handler, '.', recursive=True)
    observer.start()

    last_result = None

    try:
        while True:
            if to_run:
                loader = GreenTestLoader()
                test_suite = loader.loadTargets(
                    args.targets, file_pattern=args.file_pattern)

                last_result = run(test_suite, stream, args, testing)
                to_run = False

            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()

    return last_result
