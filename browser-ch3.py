# need to set up python environment in terminal to test code:
# cse493x-24sp-amyc1 python3 browser.py https://example.org
# python3 browser.py https://browser.engineering/examples/xiyouji.html

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

# import set_parameter

# Import additional files for chapter 3
import layout
from url import *
from layout import *

# WIDTH, HEIGHT = 800, 600
# HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100
# emojiglobal = {}

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
        # self.window.bind("<Configure>", self.resize)

        # exercise emoji
        # emojiglobal['1F600'] = tkinter.PhotoImage(file='openmoji/1F600.png')

    #event handler
    def scrolldown(self, e):
        self.scroll += SCROLL_STEP
        self.draw()

    def load(self, url):
        body = url.request()
        tokens = lex(body)
        # tokens = Layout.lex(body)
        self.display_list = Layout(tokens).display_list
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

            # chapter 2 exercise emoji
            # if c == '\N{GRINNING FACE}':
            #     emo = emojiglobal['1F600']
            #     self.canvas.create_image(screen_x, screen_y, image=emo)
            # else:
            #     self.canvas.create_text(screen_x, screen_y, text=c)
        
        #draw scrollbar here if the text is longer than the window
        # if len(self.display_list) * layout.VSTEP > layout.HEIGHT:
        #     self.draw_scrollbar()

    # chapter2 exercise emoji
    # def handle_emoji(self, screen_x, screen_y, c):
    #     image_path = f"openmoji/{str.upper(hex(ord(c))[2:])}.png"
    #     photo = tkinter.PhotoImage(fill=image_path)
    #     self.canvas.create_image(screen_x, screen_y, image=photo)

    # Exercise-resizing, handles resize events
    # Loading that URL results in the text with each letter on a new y value.
    #The `x` value is always one, but `y` increments, since the canvas is of width one.
    # def resize (self, e):
    #     global WIDTH, HEIGHT
    #     layout.WIDTH = e.width
    #     layout.HEIGHT = e.height
    #     self.display_list = layout(self.body)
    #     self.draw()

    # chapter2 exercise-scrollbar
    # def draw_scrollbar(self):
    #     global WIDTH, SCROLL_STEP
    #     x1 = layout.WIDTH - 8
    #     y1 = self.scroll / 2
    #     x2 = layout.WIDTH
    #     y2 = y1 + (SCROLL_STEP * 2)
    #     width = 0
    #     fill = 'blue'
    #     # At the right edge of the screen, draw a blue, rectangular scrollbar that outputs x1=792 y1=0 x2=800 y2=50 width=0 fill='blue
    #     self.canvas.create_rectangle(x1=x1, y1=y1, x2=x2, y2=y2, width=width, fill=fill)

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