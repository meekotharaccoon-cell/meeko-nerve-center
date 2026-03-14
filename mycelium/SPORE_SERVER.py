import http.server
import socketserver
import socket

def broadcast():
    PORT = 8080
    Handler = http.server.SimpleHTTPRequestHandler
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    print(f"📡 BROADCAST ACTIVE: Access the Swarm at http://{local_ip}:{PORT}")
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()

if __name__ == "__main__":
    broadcast()
