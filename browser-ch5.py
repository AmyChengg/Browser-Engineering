import tkinter
import tkinter.font
import layout
from url import *
from layout import *
from params import set_parameters
from htmlparser import *

class Browser:
    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window,
            width=WIDTH,
            height=HEIGHT,
        )

        self.canvas.pack(expand=True, fill="both")

        self.scroll = 0
        self.body = ""

        self.window.bind("<Down>", self.scrolldown)
        self.window.bind("<Up>", self.scrollup)
        self.window.bind("<Configure>", self.resize)


    def scrolldown(self, e):
        max_y = max(self.document.height + 2 * VSTEP - HEIGHT, 0)
        self.scroll = min(self.scroll + SCROLL_STEP, max_y)
        self.draw()
    
    def scrollup(self, e):
        self.scroll -= SCROLL_STEP
        self.draw()

    def load(self, url):
        body = url.request()
        self.nodes = HTMLParser(body).parse()
        self.document = DocumentLayout(self.nodes)
        self.document.layout()
        self.display_list = []
        paint_tree(self.document, self.display_list)
        self.draw()

    def draw(self):
        self.canvas.delete("all")

        for cmd in self.display_list:
            if cmd.top > self.scroll + HEIGHT: continue
            if cmd.bottom < self.scroll: continue
            cmd.execute(self.scroll, self.canvas)
                                         
        if len(self.display_list) * VSTEP > HEIGHT:
            self.draw_scrollbar()

    
    def draw_scrollbar(self):
        x1 = WIDTH - 8
        x2 = WIDTH

        y1 = self.scroll / 2
        y2 = y1 + (SCROLL_STEP * 2)
    
        self.canvas.create_rectangle(x1, y1, x2, y2, fill="blue", width=0)

    def resize(self, e):
        self.canvas.config(width=WIDTH, height=HEIGHT)
        self.display_list = DocumentLayout(self.body)
        self.draw()

if __name__ == "__main__":
    import sys
    Browser().load(URL(sys.argv[1]))
    tkinter.mainloop()
    body = URL(sys.argv[1]).request()
    root_node = HTMLParser(body).parse()
