# need to set up python environment in terminal to test code:
# cse493x-24sp-amyc1 python3 browser.py https://example.org
# python3 browser.py https://browser.engineering/examples/xiyouji.html
# python3 tests/run.py chapter

#test on terminal: python3 tests/run.py
# pull updated tests: git submodule update --remote

# !/usr/bin/env python3
# python 3.12 virtual env: usr/bin/local/env python3

# Request on terminal:
# HTTP/1.0 200 OK
# Age: 236949
# Cache-Control: max-age=604800

# import socket
# import ssl 
import tkinter
import tkinter.font

# Import additional files for chapter 3 and 4
import layout
from url import *
from layout import *
from params import set_parameters
from htmlparser import *

class Browser:
    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas (
            self.window,
            width=layout.WIDTH,
            height=layout.HEIGHT,
        )
        
        self.window.bind("<Down>", self.scrolldown) # Allows user to scroll with down arrow key
        # Exercise-resizing chapter2-3
        self.body = ""
        self.canvas.pack(fill='both', expand=1) #self.canvas.pack()
        self.scroll = 0

    #event handler
    def scrolldown(self, e):
        self.scroll += SCROLL_STEP
        self.draw()


    # Chapter 4 core
    def load(self, url):
        body = url.request()
        self.nodes = HTMLParser(body).parse()
        self.display_list = Layout(self.nodes).display_list

        self.draw()

    # Draw needs to loop through it and draw each character
    def draw(self):
        self.canvas.delete("all") # Erase old texts when scrolling

        for page_x, page_y, word, font in self.display_list:
            screen_x = page_x
            screen_y = page_y - self.scroll
            if page_y > self.scroll + layout.HEIGHT: continue
            if self.scroll > layout.VSTEP + page_y: continue

            self.canvas.create_text(screen_x, screen_y, text = word, font=font, anchor='nw')

# Function in layout.py
def lex(body):
    out = []
    buffer = ""
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
            if buffer: out.append(Text(buffer))
            buffer = ""
        elif c == ">":
            in_tag = False
            out.append(Tag(buffer))
            buffer = ""
        else:
            buffer += c
    if not in_tag and buffer:
        out.append(Text(buffer))
    return out

# Add the following code to run load from the command line:

if __name__ == "__main__":
    import sys

        # The first line is Python’s version of a main function, run only 
        # when executing this script from the command line. The code reads
        # the first argument (sys.argv[1]) from the command line and uses it 
        # as a URL. 
    Browser().load(URL(sys.argv[1]))
    tkinter.mainloop() 