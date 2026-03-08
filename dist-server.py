#!/usr/bin/env python3
"""
Simple HTTP server for serving static files
"""
import http.server
import socketserver
import os
import sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8888

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# The dist folder is in the same directory as this script
SERVE_DIR = os.path.join(SCRIPT_DIR, 'dist')

if not os.path.exists(SERVE_DIR):
    print(f"Error: {SERVE_DIR} does not exist")
    sys.exit(1)

os.chdir(SERVE_DIR)

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()
    
    def do_GET(self):
        # API proxy - redirect to backend
        if self.path.startswith('/api/') or self.path.startswith('/ws/'):
            self.send_response(502)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"error": "API not available"}')
            return
        
        # SPA fallback - serve index.html for non-file paths
        if self.path != '/' and not os.path.exists(self.path.lstrip('/')) and '.' not in self.path:
            self.path = '/index.html'
        
        # Default to index.html
        if self.path == '/':
            self.path = '/index.html'
        
        return super().do_GET()

with socketserver.TCPServer(("0.0.0.0", PORT), MyHTTPRequestHandler) as httpd:
    print(f"Serving {SERVE_DIR} at http://0.0.0.0:{PORT}")
    httpd.serve_forever()
