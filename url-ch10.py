import socket
import ssl
import urllib
import urllib.parse
from server import *

COOKIE_JAR = {}

class URL:
    def __repr__(self):
        return "URL(scheme={}, host={}, port={}, path={!r})".format(
            self.scheme, self.host, self.port, self.path)
    
    def __str__(self):
        port_part = ":" + str(self.port)
        if self.scheme == "https" and self.port == 443:
            port_part = ""
        if self.scheme == "http" and self.port == 80:
            port_part = ""
        return self.scheme + "://" + self.host + port_part + self.path
    
    cache = dict()

    def __init__(self, url, redirect=0) -> None:
        self.scheme, url = url.split("://", 1)

        self.redirect = redirect
        if (self.redirect >= 10):
            raise RedirectLoopError(Exception("Too many redirects"))
        
        assert self.scheme in ("http", "https", "file")

        if self.scheme == "http":
            self.port = 80
        elif self.scheme == "https":
            self.port = 443
        elif self.scheme == "file":
            self.port = None
            self.host = None

        if "\\" in url:
            if self.scheme != "file":
                _, url = url.split("\\", 1)
                self.path = "\\" + url
            else:
                self.path = url

        if self.scheme != "file":
            if "/" not in url:
                url = url + "/"
            self.host, url = url.split("/", 1)
            self.path = "/" + url
        else:
            self.path = url

        if self.scheme == "file":
            self.port = None
            self.host = None
            self.path = url
        elif ":" in self.host:
            self.host, port = self.host.split(":", 1)
            self.port = int(port)
    
    def request(self, referrer, payload=None):
        s = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP,
        )
        s.connect((self.host, self.port))

    
        if self.scheme == "https":
            ctx = ssl.create_default_context()
            #ch10-certificate-errors
            try:
                s = ctx.wrap_socket(s, server_hostname=self.host)
            except Exception:
                return {"invalid-certificate": True}, "<!doctype html> Secure Connection Failed"
    
        method = "POST" if payload else "GET"
        request = "{} {} HTTP/1.0\r\n".format(method, self.path)
        request += "Host: {}\r\n".format(self.host)
        if self.host in COOKIE_JAR:
            cookie, params = COOKIE_JAR[self.host]
            allow_cookie = True
            if referrer and params.get("samesite", "none") == "lax":
                if method != "GET":
                    allow_cookie = self.host == referrer.host
            if allow_cookie:
                request += "Cookie: {}\r\n".format(cookie)
        if payload:
            content_length = len(payload.encode("utf8"))
            request += "Content-Length: {}\r\n".format(content_length)
        request += "\r\n"
        if payload: request += payload
        s.send(request.encode("utf8"))
        response = s.makefile("r", encoding="utf8", newline="\r\n")
    
        statusline = response.readline()
        version, status, explanation = statusline.split(" ", 2)
    
        response_headers = {}
        while True:
            line = response.readline()
            if line == "\r\n": break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()
    
        if "set-cookie" in response_headers:
            cookie = response_headers["set-cookie"]
            cookie, params = self.get_cookie(cookie)
            # params = {}
        
        assert "transfer-encoding" not in response_headers
        assert "content-encoding" not in response_headers
    
        content = response.read()
        s.close()
    
        return response_headers, content
    
    # ch10 script access exercise
    def get_cookie(self, cookie):
        params = {}
        if ";" in cookie:
            cookie, rest = cookie.split(";", 1)
            for param in rest.split(";"):
                if '=' in param:
                    param, value = param.split("=", 1)
                else:
                    value = "true"
                params[param.strip().casefold()] = value.casefold()
        COOKIE_JAR[self.host] = (cookie, params)
        return cookie, params

    def resolve(self, url):
        if "://" in url: return URL(url)
        if not url.startswith("/"):
            dir, _ = self.path.rsplit("/", 1)
            while url.startswith("../"):
                _, url = url.split("/", 1)
                if "/" in dir:
                    dir, _ = dir.rsplit("/", 1)
            url = dir + "/" + url
        if url.startswith("//"):
            return URL(self.scheme + ":" + url)
        else:
            return URL(self.scheme + "://" + self.host + \
                       ":" + str(self.port) + url)
    
    def origin(self):
        return self.scheme + "://" + self.host + ":" + str(self.port)

def tree_to_list(tree, list):
    list.append(tree)
    for child in tree.children:
        tree_to_list(child, list)
    return list
    
# Exercise chapter 1 Redirects
class RedirectLoopError(Exception): pass
