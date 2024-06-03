import socket
from datetime import datetime
import ssl
import sys

def debug(*args, file=sys.stderr, **kwargs):
    print(*args, file=file, **kwargs)

class RedirectLoopError(Exception): pass

class URL:
    cache = dict()
    cache_path = ""

    def __init__(self, url, redirect=0):
        self.fragment = None
        self.url = url
        self.redirect = redirect
        if (self.redirect >= 10):
            raise RedirectLoopError(Exception("Too many redirects"))
        
        self.scheme, url = url.split("://", 1)
        assert self.scheme in ("http", "https", "file", "about")

        if self.scheme == "http":
            self.port = 80
        elif self.scheme == "https":
            self.port = 443
        elif self.scheme == "file":
            self.port = None
            self.host = None
        #ch7-bookmarks-exercise
        elif self.scheme == "about":
            self.host = None 
            self.port = None 
            self.path = "bookmarks"
            return
            
        if "\\" in url:
            if self.scheme != "file":
                _, url = url.split("\\", 1)
                self.path = "\\" + url
            else:
                self.path = url
        else:
            if self.scheme != "file":
                if "/" not in url:
                    url = url + "/"
                self.host, url = url.split("/", 1)
                self.path = "/" + url
            else:
                self.path = url
        if "#" in self.path:
            self.path, self.fragment = self.path.split("#", 1)

        if (self.scheme == "file"):
            self.host = None
        elif ":" in self.host:
            self.host, port = self.host.split(":", 1)
            self.port = int(port)

    def __str__(self):
        port_part = ":" + str(self.port)
        host = self.host
        path = self.path
        fragment = ""
        if self.scheme == "https" and self.port == 443:
            port_part = ""
        if self.scheme == "http" and self.port == 80:
            port_part = ""
        if not host:
            host = ""
        if not path:
            path = ""
        if self.fragment:
            fragment = "#" + self.fragment
        return self.scheme + "://" + host + port_part + path + fragment
    
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

    def request(self, headers=None):
        if self.scheme == "about" and self.path == "bookmarks":
            return "!bookmarks"
        
        if self.path == "/" and self.fragment:
            self.path = URL.cache_path
            return "relative"

        identifier = ""
        if self.scheme:
            identifier += self.scheme 
        if self.host:
            identifier += self.host 
        if self.port:
            identifier += str(self.port)
        identifier += self.path 

        if identifier in URL.cache:
            body, age, date = URL.cache[identifier]
            
            if (datetime.now() - date).total_seconds() < age:
                return body
        s = socket.socket(
            family = socket.AF_INET,
            type = socket.SOCK_STREAM,
            proto= socket.IPPROTO_TCP,
        )
        s.connect((self.host, self.port))

        if self.scheme == "file":
            f = open(self.path, "r")
            return f.read()

        if self.scheme == "https":
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host)


        request = "GET {} HTTP/1.1\r\n".format(self.path)
        
        h = {"host": self.host, "connection": "close", "user-agent": "493"}


        if headers:
            for k,v in headers.items():
                h[k.lower()] = v 
        for k,v in h.items():
            request += f"{k}: {v}\r\n"

        request += "\r\n"

        s.send(request.encode("utf8"))
        response = s.makefile("r", encoding="utf8", newline="\r\n")

        statusline = response.readline()
        version, status, explanation = statusline.split(" ", 2)

        response_headers = dict()
        while True:
            line = response.readline()
            if line == "\r\n": break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()
        assert "transfer-encoding" not in response_headers 
        assert "content-encoding" not in response_headers

        status = int(status)
        if 300 <= status and status < 400:
            redirect_url = response_headers["location"]
            if redirect_url[0] == "/":
                redirect_url = self.scheme + "://" + self.host + redirect_url
            return URL(redirect_url, self.redirect + 1).request()
        
        put_cache = False
        URL.cache_path = self.path

        if 200 <= status and status < 300 and "cache-control" in response_headers:
            cache_header = response_headers["cache-control"]
            directives = cache_header.split(",")
            if "no-store" not in cache_header:
                age = 0
                for d in directives:
                    if "max-age" in d:
                        age = int(d[8:])
                        put_cache = True

        body = response.read()

        if put_cache:
            URL.cache[identifier] = (body, age, datetime.now())

        s.close()

        return body
    
    def __repr__(self):
        fragment_part = "" if self.fragment == None else ", fragment=" + self.fragment
        return "URL(scheme={}, host={}, port={}, path={!r}{})".format(
            self.scheme, self.host, self.port, self.path, fragment_part)