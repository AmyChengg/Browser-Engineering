import socket
import ssl

from datetime import datetime

# parsing the URL, chapter 1
class URL:
    # To print chapter1 exercise
    def __repr__(self):
        return "URL(scheme={}, host={}, port={}, path={!r})".format(
            self.scheme, self.host, self.port, self.path)
    
    cache = dict()

    def __init__(self, url, redirect=0) -> None:
        self.scheme, url = url.split("://", 1)

        # Exercise-redirect
        self.redirect = redirect
        if (self.redirect >= 10):
            raise RedirectLoopError(Exception("Too many redirects"))
        
        # Chapter 1 exercise-file-urls
        assert self.scheme in ("http", "https", "file") # check that browser supports http and https

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
    
    def request(self, headers={}):
        texts = ""
        if self.scheme:
            texts += self.scheme
        if self.host:
            texts += self.host 
        if self.port:
            texts += str(self.port)
        texts += self.path 

        # Exercise caching
        if texts in URL.cache:
            body, age, date = URL.cache[texts]
            
            if (datetime.now() - date).total_seconds() < age:
                return body
        
        s = socket.socket(
            family = socket.AF_INET,
            type   = socket.SOCK_STREAM,
            proto  = socket.IPPROTO_TCP,
        )
        s.connect((self.host, self.port))

        if self.scheme == "file":
            f = open(self.path, "r")
            return f.read()

        if self.scheme == "https":
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host)

        # exercise HTTP/1.1

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

        # exercise redirects
        status = int(status)
        if 300 <= status and status < 400:
            redirect_url = response_headers["location"]
            if redirect_url[0] == "/":
                redirect_url = self.scheme + "://" + self.host + redirect_url
  
            return URL(redirect_url, self.redirect + 1).request()
       
        # exercise caching
        put_cache = False

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
            URL.cache[texts] = (body, age, datetime.now())

        s.close()

        return body

# Exercise chapter 1 Redirects
class RedirectLoopError(Exception): pass