import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from src.serve import alerts


class Handler(BaseHTTPRequestHandler):
    received = []

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        data = self.rfile.read(length)
        Handler.received.append(json.loads(data))
        self.send_response(200)
        self.end_headers()


def test_alert_webhook(tmp_path, monkeypatch):
    server = HTTPServer(('127.0.0.1', 0), Handler)
    t = threading.Thread(target=server.serve_forever)
    t.daemon = True
    t.start()
    url = f"http://127.0.0.1:{server.server_address[1]}"
    monkeypatch.setattr(alerts, 'ALERT_PATH', tmp_path / 'alerts.jsonl')
    monkeypatch.setattr(alerts, 'WEBHOOKS', [{
        'url': url,
        'severities': ['ERROR'],
        'types': ['slo']
    }])
    alerts.log_event('slo', 'breach', severity='ERROR')
    server.shutdown()
    t.join()
    assert Handler.received and Handler.received[0]['type'] == 'slo'
