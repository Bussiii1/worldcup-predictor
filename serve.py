#!/usr/bin/env python3
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
port = int(os.environ.get("PORT", 8765))
import http.server
handler = http.server.SimpleHTTPRequestHandler
httpd = http.server.HTTPServer(("", port), handler)
print(f"Serving on http://localhost:{port}")
httpd.serve_forever()
