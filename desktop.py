import os
import sys
import threading
import webview
import time
from app import app, db

PORT = 54321
ROOT_URL = f'http://127.0.0.1:{PORT}'

def start_flask():
    """Starts the Flask server in a separate thread."""
    app.run(host='127.0.0.1', port=PORT, debug=False, use_reloader=False)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    # start flask in daemon thread
    t = threading.Thread(target=start_flask)
    t.daemon = True
    t.start()

    time.sleep(1)

    # create native window
    webview.create_window(
        title="Quorum", 
        url=ROOT_URL, 
        width=1200, 
        height=800, 
        resizable=True
    )

    # start GUI loop
    webview.start()