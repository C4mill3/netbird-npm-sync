from http.server import BaseHTTPRequestHandler, HTTPServer
import datetime
from main import main

class SimpleHandler(BaseHTTPRequestHandler):
    envs = None
    
    current_hour = datetime.datetime.now().hour
    request_count = 0

    def do_GET(self):
        now = datetime.datetime.now()
        if now.hour != self.__class__.current_hour:
            self.__class__.current_hour = now.hour
            self.__class__.request_count = 0
            
            
        if self.__class__.request_count < self.__class__.envs["SOCKET_LIMIT"]:
            self.send_response(200)
            self.end_headers()
            self.__class__.request_count += 1   
            main(self.__class__.envs)
        else:
            self.send_response(429)
            self.end_headers()


def run(envs=None, server_class=HTTPServer, handler_class=SimpleHandler, port=8080):
    handler_class.envs = envs  # Set variable on handler class
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()

if __name__ == '__main__':
    run()