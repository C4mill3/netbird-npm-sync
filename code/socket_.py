from http.server import BaseHTTPRequestHandler, HTTPServer
import datetime
from main import main
import threading

class SimpleHandler(BaseHTTPRequestHandler):
    config = None
    last_request_time = None
    lock = threading.Lock()

    def do_GET(self):
        now = datetime.datetime.now()
        with self.__class__.lock:
            #limit to 1 request per minute, bc if more it's useless
            if self.__class__.last_request_time is None or (now - self.__class__.last_request_time).total_seconds() >= 60:
                self.__class__.last_request_time = now
                self.send_response(200)
                self.end_headers()
                main(self.__class__.config)
            else:
                self.send_response(429)
                self.end_headers()


def run(config : dict, server_class=HTTPServer, handler_class=SimpleHandler):
    handler_class.config = config  # Set variable on handler class
    server_address = ('', config['socket']['port'])
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()

if __name__ == '__main__':
    run()