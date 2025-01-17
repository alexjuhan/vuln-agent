from http.server import BaseHTTPRequestHandler
import json
import sys
from pathlib import Path

class ScanHandler(BaseHTTPRequestHandler):
    SCAN_ENDPOINT = '/api/v1/scan'

    def do_POST(self):
        if self.path == self.SCAN_ENDPOINT:
            self._handle_scan_request()
        else:
            self._send_not_found()

    def _handle_scan_request(self):
        try:
            request_data = self._parse_request_body()
            repository_url = self._validate_request(request_data)
            
            # Update the import to use the correct path
            sys.path.append(str(Path(__file__).parent.parent))
            from workflow.workflow import security_scan_workflow
            from tempfile import mkdtemp
            
            # Create a temporary directory for cloning
            local_path = mkdtemp()
            
            # Start the workflow asynchronously
            # Note: In a production environment, you might want to use a proper task queue
            import threading
            thread = threading.Thread(
                target=security_scan_workflow,
                args=(repository_url, local_path)
            )
            thread.start()
            
            self._send_success_response(repository_url)
        except json.JSONDecodeError:
            self._send_error_response(400, "Invalid JSON in request body")
        except ValueError as e:
            self._send_error_response(400, str(e))
        except Exception as e:
            self._send_error_response(500, f"Internal server error: {str(e)}")

    def _parse_request_body(self):
        content_length = int(self.headers['Content-Length'])
        raw_data = self.rfile.read(content_length)
        return json.loads(raw_data.decode('utf-8'))

    def _validate_request(self, data):
        if 'github_repo' not in data:
            raise ValueError("Missing 'github_repo' in request body")
        return data['github_repo']

    def _send_success_response(self, repository_url):
        response_data = {
            "status": "success",
            "message": f"Scan initiated for repository: {repository_url}"
        }
        self._send_json_response(200, response_data)

    def _send_json_response(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def _send_error_response(self, status_code, message):
        error_data = {
            "status": "error",
            "message": message
        }
        self._send_json_response(status_code, error_data)

    def _send_not_found(self):
        self._send_error_response(404, "Endpoint not found")
