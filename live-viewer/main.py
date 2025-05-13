import base64
import json
import os
from threading import Thread

import requests
from flask import Flask, send_from_directory
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from websocket_server import WebsocketServer

from py2graph import py2graph

# Configuration
PLANTUML_SERVER_URL = "http://localhost:8080/svg"  # Local PlantUML server URL
WEBSOCKET_PORT = 8765
HTTP_SERVER_PORT = 8000

# Flask app to serve index.html and diagrams
app = Flask(__name__)


@app.route("/")
def index():
    """Serve the index.html file."""
    return send_from_directory('.', 'index.html')


from zlib import compress
maketrans = bytes.maketrans
import string

plantuml_alphabet = string.digits + string.ascii_uppercase + string.ascii_lowercase + '-_'
base64_alphabet = string.ascii_uppercase + string.ascii_lowercase + string.digits + '+/'
b64_to_plantuml = maketrans(base64_alphabet.encode('utf-8'), plantuml_alphabet.encode('utf-8'))

def deflate_and_encode(plantuml_text):
    """zlib compress the plantuml text and encode it for the plantuml server.
    """
    zlibbed_str = compress(plantuml_text.encode('utf-8'))
    compressed_string = zlibbed_str[2:-4]
    return base64.b64encode(compressed_string).translate(b64_to_plantuml).decode('utf-8')


class PythonFileHandler(FileSystemEventHandler):
    def __init__(self, websocket_server, observer):
        self.websocket_server = websocket_server
        self.websocket_server.set_fn_message_received(self.message_received)
        self.websocket_server.set_fn_new_client(self.on_client_connect)

        self.observer = observer
        self.lastPackageUML = ''
        self.package_path = ''
        self.package_name = ''

    def update_observer_path(self, new_path):
        """Update the observer to watch a new directory."""
        # Stop the current observer
        self.observer.unschedule_all()
        # Update the package path and name
        self.package_path = new_path
        self.package_name = os.path.basename(new_path)
        # Reschedule the observer to watch the new directory
        self.observer.schedule(self, path=new_path, recursive=True)
        print(f"Observer now watching: {new_path}")

    def message_received(self, client, server, message):
        """Handle messages received from WebSocket clients."""
        try:
            data = json.loads(message)
            if data.get("action") == "updatePath":
                new_path = data.get("path")
                if os.path.exists(new_path) and os.path.isdir(new_path):
                    self.package_path = new_path
                    self.package_name = self.package_path.split("/")[-1]
                    print(f"Updated WATCH_DIRECTORY to: {self.package_path}")
                    self.process_package_directory()
                    self.update_observer_path(self.package_path)
                    server.send_message(client, "Path updated successfully")
                else:
                    server.send_message(client, "Invalid path")
            else:
                print("Unknown action received:", data)
        except Exception as e:
            print("Error handling WebSocket message:", e)

    def on_client_connect(self, client, server):
        self.send_puml_data()

    def send_puml_data(self):
        puml_content = self.lastPackageUML
        try:
            encoded_puml = deflate_and_encode(puml_content)
            url = f"{PLANTUML_SERVER_URL}/{encoded_puml}"
            response = requests.get(url)

            if response.status_code == 200:
                image_data = base64.b64encode(response.content).decode('utf-8')
                self.websocket_server.send_message_to_all(
                    f"data:image/svg+xml;base64,{image_data}"
                )
                print("Diagram sent to clients via WebSocket")
            else:
                print(f"Failed to generate diagram for {self.package_name}: {response.status_code}")
        except Exception as e:
            print(f"Error sending to PlantUML server: {e}")

    def process_package_directory(self):
        """Process the Python file with py2graph and send the PUML string to the PlantUML server."""
        print(f"Processing updated package")

        # Generate the PUML string using py2graph
        puml_content = py2graph.py2graph(self.package_path, self.package_name)
        print(puml_content)
        self.lastPackageUML = puml_content
        print(f"Generated PUML content for {self.package_path}")

        self.send_puml_data()

    def on_modified(self, event):
        """Handle modified Python files."""
        if not event.is_directory and event.src_path.endswith('.py'):
            self.process_package_directory()

    def on_created(self, event):
        """Handle newly created Python files."""
        if not event.is_directory and event.src_path.endswith('.py'):
            self.process_package_directory()


def start_file_watcher(websocket_server):
    observer = Observer()
    handler = PythonFileHandler(websocket_server, observer)
    observer.start()
    try:
        observer.join()
    except KeyboardInterrupt:
        print("Stopping observer...")
        observer.stop()
    observer.join()


if __name__ == "__main__":
    # Start Flask server in a separate thread
    Thread(target=lambda: app.run(host="0.0.0.0", port=HTTP_SERVER_PORT), daemon=True).start()

    # Start WebSocket server
    websocket_server = WebsocketServer(port=WEBSOCKET_PORT)
    print(f"WebSocket server started on port {WEBSOCKET_PORT}")

    Thread(target=websocket_server.run_forever, daemon=True).start()

    # Start file watcher
    start_file_watcher(websocket_server)
