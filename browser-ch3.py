import tkinter
import tkinter.font

# Import additional files for chapter 3
import layout
from url import *
from layout import *

SCROLL_STEP = 100

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
        self.canvas.pack(fill='both', expand=1) 
        self.scroll = 0

    # Event handler
    def scrolldown(self, e):
        self.scroll += SCROLL_STEP
        self.draw()

    def load(self, url):
        body = url.request()
        tokens = lex(body)
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

if __name__ == "__main__":
    import sys

        # The first line is Python’s version of a main function, run only 
        # when executing this script from the command line. The code reads
        # the first argument (sys.argv[1]) from the command line and uses it 
        # as a URL. 
    Browser().load(URL(sys.argv[1]))
    tkinter.mainloop() 
