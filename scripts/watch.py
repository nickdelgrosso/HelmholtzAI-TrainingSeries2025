import subprocess
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class RunOnChangeHandler(FileSystemEventHandler):
    def on_any_event(self, event):
        # Ignore directory metadata changes
        if event.is_directory:
            return
        print(f"Change detected: {event.src_path}")
        subprocess.run(["python", "scripts/notebooks_to_site.py"], check=False)


if __name__ == "__main__":
    path_to_watch = "./notebooks"
    event_handler = RunOnChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path=path_to_watch, recursive=True)
    observer.start()
    print(f"Watching {path_to_watch}...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
