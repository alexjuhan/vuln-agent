from http.server import HTTPServer
from scan import ScanHandler

def start_server(port=8000, host=''):
    server_address = (host, port)
    httpd = HTTPServer(server_address, ScanHandler)
    print(f"Scan server running on http://{host or 'localhost'}:{port}")
    httpd.serve_forever()

if __name__ == "__main__":
    start_server() 