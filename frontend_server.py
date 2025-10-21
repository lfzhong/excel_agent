#!/usr/bin/env python3
"""
Simple HTTP server to serve the Excel Agent frontend.
Serves static files from the frontend directory.
"""

import http.server
import socketserver
import os
from pathlib import Path
import webbrowser
import threading
import time

class FrontendHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="frontend", **kwargs)

    def end_headers(self):
        # Add CORS headers for all responses
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_GET(self):
        # Serve index.html for root path
        if self.path == '/' or self.path == '/index.html':
            self.path = '/index.html'
        return super().do_GET()

def run_frontend_server(port=3000):
    """Run the frontend server on specified port"""
    try:
        with socketserver.TCPServer(("", port), FrontendHTTPRequestHandler) as httpd:
            print(f"🚀 Frontend server running at http://localhost:{port}")
            print("📁 Serving files from frontend/ directory")
            print("💡 Open your browser and navigate to the URL above")
            print("Press Ctrl+C to stop the server")
            print("-" * 50)
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Frontend server stopped")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ Port {port} is already in use. Try a different port.")
        else:
            print(f"❌ Error starting server: {e}")

def open_browser_after_delay(url, delay=2):
    """Open browser after a short delay to allow server to start"""
    time.sleep(delay)
    try:
        webbrowser.open(url)
        print(f"🌐 Browser opened at {url}")
    except Exception as e:
        print(f"Could not open browser automatically: {e}")

if __name__ == "__main__":
    import sys

    port = 3000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("❌ Invalid port number")
            sys.exit(1)

    # Check if frontend directory exists
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("❌ frontend/ directory not found!")
        print("💡 Make sure you're running this from the project root")
        sys.exit(1)

    # Start browser opener in background
    browser_thread = threading.Thread(
        target=open_browser_after_delay,
        args=(f"http://localhost:{port}",)
    )
    browser_thread.daemon = True
    browser_thread.start()

    # Start the server
    run_frontend_server(port)
