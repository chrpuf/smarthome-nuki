#!/usr/bin/env python3

#import requests
import json

from http.server import BaseHTTPRequestHandler,HTTPServer

ADDR = "192.168.0.2"
PORT = 8080

class RequestHandler(BaseHTTPRequestHandler):        
    def do_POST(self):
        self.data_string = self.rfile.read(int(self.headers['Content-Length'])).decode('utf-8')
        self.send_response(200, "OK")
        self.end_headers()
        data = json.loads(self.data_string)
        print(data)
        print(data['stateName'])
        #self.wfile.write("serverdata")

httpd = HTTPServer((ADDR, PORT), RequestHandler)
httpd.serve_forever()