from http.server import HTTPServer
from scan import ScanHandler
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

def start_server(port=8000, host=''):
    server_address = (host, port)
    httpd = HTTPServer(server_address, ScanHandler)
    print(f"Scan server running on http://{host or 'localhost'}:{port}")
    httpd.serve_forever()

if __name__ == "__main__":
    start_server() 