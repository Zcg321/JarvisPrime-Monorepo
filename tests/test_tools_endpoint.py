import json
import threading
from http.server import HTTPServer
import urllib.request

from src.serve.server_stub import H, TOOL_INFO


def test_http_tools_endpoint():
    server = HTTPServer(("127.0.0.1", 0), H)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/tools") as resp:
            data = json.loads(resp.read().decode())
        assert data["tools"]["surgecell"] == TOOL_INFO["surgecell"]
    finally:
        server.shutdown()
        thread.join()
