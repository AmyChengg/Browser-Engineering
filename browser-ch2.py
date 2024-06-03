# HTTP/1.0 200 OK
# Age: 236949
# Cache-Control: max-age=604800

import socket
import ssl 
import tkinter

from datetime import datetime

# parsing the URL, chapter 1
class URL:
    # To print the exercise
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

        # Special case
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

def show(body):
    text = ""
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            text += c
    print(text)
    
# Chapter 2

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100
emojiglobal = {}

# For the chapter-2-base-tests
def set_parameters(**params):
    global WIDTH, HEIGHT, HSTEP, VSTEP, SCROLL_STEP
    if "WIDTH" in params: WIDTH = params["WIDTH"]
    if "HEIGHT" in params: HEIGHT = params["HEIGHT"]
    if "HSTEP" in params: HSTEP = params["HSTEP"]
    if "VSTEP" in params: VSTEP = params["VSTEP"]
    if "SCROLL_STEP" in params: SCROLL_STEP = params["SCROLL_STEP"]

class Browser:

    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas (
            self.window,
            width=WIDTH,
            height=HEIGHT,
        )
        
        self.scroll = 0
        self.window.bind("<Down>", self.scrolldown) # allows user to scroll with down arrow key
        self.body = ""
        self.canvas.pack(fill='both', expand=1)
        self.window.bind("<Configure>", self.resize)

        # exercise emoji
        emojiglobal['1F600'] = tkinter.PhotoImage(file='openmoji/1F600.png')
    
    # Exercise-resizing, handles resize events
    # Loading that URL results in the text with each letter on a new y value.
    #The `x` value is always one, but `y` increments, since the canvas is of width one.
    def resize (self, e):
        global WIDTH, HEIGHT
        WIDTH = e.width
        HEIGHT = e.height
        self.display_list = layout(self.body)
        self.draw()

    #event handler
    def scrolldown(self, e):
        self.scroll += SCROLL_STEP
        self.draw()

    def load(self, url):
        body = url.request()
        text = lex(body)
        self.display_list = layout(text)
        self.draw()

        self.body = text # resize exercise

    # draw needs to loop through it and draw each character. Since draw does need access to the canvas
    # The page coordinate y then has screen coordinate y - self.scroll
    def draw(self):
        self.canvas.delete("all") # erase old texts when scrolling

        max_y = 0
        for page_x, page_y, c in self.display_list:
            max_y = max(max_y, page_y) # test

            screen_x = page_x
            screen_y = page_y - self.scroll
            if page_y > self.scroll + HEIGHT: continue
            if self.scroll > VSTEP + page_y: continue

            # exercise emoji
            if c == '\N{GRINNING FACE}':
                emo = emojiglobal['1F600']
                self.canvas.create_image(screen_x, screen_y, image=emo)
            else:
                self.canvas.create_text(screen_x, screen_y, text=c)
        
        #draw scrollbar here if the text is longer than the window
        if len(self.display_list) * VSTEP > HEIGHT:
            self.draw_scrollbar()

    
    # exercise emoji
    def handle_emoji(self, screen_x, screen_y, c):
        image_path = f"openmoji/{str.upper(hex(ord(c))[2:])}.png"
        photo = tkinter.PhotoImage(fill=image_path)
        self.canvas.create_image(screen_x, screen_y, image=photo)

    # exercise-scrollbar
    def draw_scrollbar(self):
        global WIDTH, SCROLL_STEP
        x1 = WIDTH - 8
        y1 = self.scroll / 2
        x2 = WIDTH
        y2 = y1 + (SCROLL_STEP * 2)
        width = 0
        fill = 'blue'
        # At the right edge of the screen, draw a blue, rectangular scrollbar that outputs x1=792 y1=0 x2=800 y2=50 width=0 fill='blue
        self.canvas.create_rectangle(x1=x1, y1=y1, x2=x2, y2=y2, width=width, fill=fill)

def layout(text):
    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP
    for c in text:
        # exercise line-breaks
        if c in "\n":
            # Increment y by more than VSTEP
            cursor_y += 2 * VSTEP
            cursor_x = HSTEP
        else:
            display_list.append((cursor_x, cursor_y, c))
            cursor_x += HSTEP
        
            # wrap the text once we reach the edge of the screen:
            if cursor_x >= WIDTH-HSTEP:
                cursor_y += VSTEP
                cursor_x = HSTEP
    return display_list
    
# display HTML text
def lex(body):
    text = ""
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            text += c
    return text

# Add the following code to run load from the command line:

if __name__ == "__main__":
    import sys

        # The first line is Python’s version of a main function, run only 
        # when executing this script from the command line. The code reads
        # the first argument (sys.argv[1]) from the command line and uses it 
        # as a URL. 
    Browser().load(URL(sys.argv[1]))
    tkinter.mainloop() 
