# ProtoFlow prototype server — written once by /protoflow-prototype, then preserved.
# Run:  python serve.py [port]   → http://localhost:8000  (works from any folder)
# Plain `python -m http.server` can serve .js as text/plain on Windows (MIME types come
# from the registry), and browsers then refuse to load the ES modules. This pins the types.
import http.server
import os
import sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
os.chdir(os.path.dirname(os.path.abspath(__file__)))   # serve this folder, wherever the command is run from


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".js": "text/javascript",
        ".mjs": "text/javascript",
        ".wasm": "application/wasm",
        ".css": "text/css",
        ".html": "text/html",
        ".sql": "text/plain; charset=utf-8",
        ".json": "application/json",
    }

    def do_GET(self):
        # SPA fallback: path-based routes (/<feature>/<SCR-id>) have no file on disk —
        # serve index.html so router.js can parse location.pathname client-side.
        fs_path = self.translate_path(self.path)
        if not os.path.isdir(fs_path) and not os.path.isfile(fs_path):
            self.path = "/index.html"
        super().do_GET()

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")  # re-scaffolded files show up on reload
        super().end_headers()


if __name__ == "__main__":
    print(f"ProtoFlow prototype on http://localhost:{PORT}  (Ctrl+C to stop)")
    http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
