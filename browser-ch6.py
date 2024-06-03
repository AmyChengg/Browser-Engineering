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
import sys
import tkinter
import tkinter.font
from url import *
from layout import *
from params import set_parameters
from htmlparser import *
from cssparser import *

browser_styles = open("browser.css")
DEFAULT_STYLE_SHEET = CSSParser(browser_styles.read()).parse()

class Browser:
    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window,
            width=WIDTH,
            height=HEIGHT,
            bg="white",
        )

        self.canvas.pack(expand=True, fill="both")

        self.scroll = 0
        self.body = ""

        self.window.bind("<Down>", self.scrolldown)
        self.window.bind("<Configure>", self.resize)


    def scrolldown(self, e):
        max_y = max(self.document.height + 2 * VSTEP - HEIGHT, 0)
        self.scroll = min(self.scroll + SCROLL_STEP, max_y)
        self.draw()

    def load(self, url):
        body = url.request()
        self.nodes = HTMLParser(body).parse()
        rules = DEFAULT_STYLE_SHEET.copy()
        style(self.nodes, sorted(rules, key=cascade_priority))
        self.document = DocumentLayout(self.nodes)
        self.document.layout()
        self.display_list = []
        paint_tree(self.document, self.display_list)
        self.draw()
        # Grab the URL of each linked style sheet, tests fail with this so removed it
        links = [node.attributes["href"]
            for node in tree_to_list(self.nodes, [])
            if isinstance(node, Element)
            and node.tag == "link"
            and node.attributes.get("rel") == "stylesheet"
            and "href" in node.attributes]
        for link in links:
            try:
                body = url.resolve(link).request()
            except:
                continue
            rules.extend(CSSParser(body).parse())

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

def tree_to_list(tree, list):
    list.append(tree)
    for child in tree.children:
        tree_to_list(child, list)
    return list

if __name__ == "__main__":
    import sys
    Browser().load(URL(sys.argv[1]))
    tkinter.mainloop()
    body = URL(sys.argv[1]).request()
    root_node = HTMLParser(body).parse()
