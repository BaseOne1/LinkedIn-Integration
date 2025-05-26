import yaml
import time
import os
import subprocess
import hashlib
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class PromptHandler(FileSystemEventHandler):
    def __init__(self):
        self.prompt_path = os.path.abspath("prompt.yaml")
        self.last_hash = self.get_file_hash()
        self.debounce_seconds = 1.0
        self.last_trigger_time = 0

    def get_file_hash(self):
        try:
            with open(self.prompt_path, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""

    def on_modified(self, event):
        if os.path.abspath(event.src_path) != self.prompt_path:
            return

        now = time.time()
        if now - self.last_trigger_time < self.debounce_seconds:
            return

        current_hash = self.get_file_hash()
        if current_hash == self.last_hash:
            return  # No actual change in content

        self.last_hash = current_hash
        self.last_trigger_time = now
        self.process_prompt()

    def process_prompt(self):
        print("Detected changes to prompt.yaml, processing...")

        try:
            with open(self.prompt_path, 'r') as f:
                data = yaml.safe_load(f)

            image_prompt = data.get("generate_image", {}).get("prompt", "")
            if image_prompt:
                with open("last_prompt.txt", "w") as pf:
                    pf.write(image_prompt.strip())

                print("Prompt updated in last_prompt.txt")
                print("Running generator.py to generate images...")

                subprocess.run(["python", os.path.join(os.path.dirname(__file__), "generator.py")], check=True)

                print("Generation complete. Watching for more changes...")

            else:
                print("No image prompt found in prompt.yaml.")
        except Exception as e:
            print(f"Error processing prompt.yaml: {e}")

if __name__ == "__main__":
    print("Watching for changes in prompt.yaml...")
    event_handler = PromptHandler()
    observer = Observer()
    observer.schedule(event_handler, path=".", recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
