import sys, http.server, threading, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        b = b'<h1>MEEKO TEST OK</h1>'
        self.send_response(200)
        self.send_header('Content-Length', len(b))
        self.end_headers()
        self.wfile.write(b)

try:
    s = http.server.HTTPServer(('127.0.0.1', 7775), H)
    print('Server bound on 7775 OK')
    with open(r'C:\Users\meeko\Desktop\UltimateAI_Master\_server_test.txt', 'w') as f:
        f.write('BOUND\n')
    s.handle_request()
    s.server_close()
    with open(r'C:\Users\meeko\Desktop\UltimateAI_Master\_server_test.txt', 'w') as f:
        f.write('SERVED\n')
    print('Server handled request OK')
except Exception as e:
    print('ERROR:', e)
    with open(r'C:\Users\meeko\Desktop\UltimateAI_Master\_server_test.txt', 'w') as f:
        f.write('ERROR: ' + str(e) + '\n')
