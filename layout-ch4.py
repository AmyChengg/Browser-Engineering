# Chapter 3
import math
import tkinter
import tkinter.font
from params import *
from htmlparser import *

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100

# Chapter3-exercise-centered-text
def set_parameters(**params):
    global WIDTH, HEIGHT, HSTEP, VSTEP, SCROLL_STEP
    if "WIDTH" in params: WIDTH = params["WIDTH"]
    if "HEIGHT" in params: HEIGHT = params["HEIGHT"]
    if "HSTEP" in params: HSTEP = params["HSTEP"]
    if "VSTEP" in params: VSTEP = params["VSTEP"]
    if "SCROLL_STEP" in params: SCROLL_STEP = params["SCROLL_STEP"]

# Helper classes for chapter 3
# class Text:
#     def __init__(self, text):
#         self.text = text
#     def __repr__(self):
#         return "Text('{}')".format(self.text)

class Tag:
    def __init__(self, tag):
        self.tag = tag
    def __repr__(self):
        return "Tag('{}')".format(self.tag)

FONTS = {}
# Caching logic
def get_font(size, weight, slant):
    key = (size, weight, slant)
    if key not in FONTS:
        font = tkinter.font.Font(size=size, weight=weight,
            slant=slant)
        label = tkinter.Label(font=font)
        FONTS[key] = (font, label)
    return FONTS[key][0]

class Layout:
    def __init__(self, node_tree):
        self.display_list = []
        self.cursor_x = hstep()
        self.cursor_y = vstep()
        # self.cursor_x = HSTEP
        # self.cursor_y = VSTEP
        self.weight = "normal"
        self.style = "roman"
        self.size = 16
        self.center = False # Chapter3-exercise-centered-text
        self.sup = False #superscripts exercise
        self.in_abbr = False # small-caps exercise
        self.sup_y = math.inf

        self.line = []

        self.recurse(node_tree)

        self.flush()

    # Chapter4 core
    def recurse(self, tree): # Walk the node tree
        if isinstance(tree, Text):
            for word in tree.text.split():
                self.word(word)
        else:
            self.open_tag(tree.tag)
            for child in tree.children:
                self.recurse(child)
            self.close_tag(tree.tag)
    
     # Chapter 4 core
    def open_tag(self, tag):
        if tag == "i":
            self.style = "italic"
        elif tag == "b":
            self.weight = "bold"
        elif tag == "small":
            self.size -= 2
        elif tag == "big":
            self.size += 4
        elif tag == "br": # Line break
            self.flush()
        elif tag == "br":
            self.flush()
        elif tag.startswith("h1"):
            if "title" in tag:
                self.flush()
                self.center = True
    
    def close_tag(self, tag):
        if tag == "/i": # Closing tag
            self.style = "roman"
        elif tag == "/b":
            self.weight = "normal"
        elif tag == "/small":
            self.size += 2
        elif tag == "/big":
            self.size -= 4
        elif tag == "/p": # Closing paragraph
            self.flush()
            self.cursor_y += vstep()
        elif tag == "/h1":
            self.flush()
            self.center = False

    def word(self, word):
        font = get_font(self.size, self.weight, self.style)
            
        w = font.measure(word)

        if self.cursor_x + w >= WIDTH-HSTEP:
            self.flush()
        
        self.line.append((self.cursor_x, word, font))
        self.cursor_x += w + font.measure(" ")
    
    def flush(self):
        if not self.line: return
        # Computing where that line should be depends on the tallest word on the line
        metrics = [font.metrics() for x, word, font in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])

        baseline = self.cursor_y + 1.25 * max_ascent 
        # Place each word relative to that line and add it to the display list
        for x, word, font in self.line:
            y = baseline - font.metrics("ascent") 
            self.display_list.append((x, y, word, font))
        
        # y must move far enough down below baseline to account for the deepest descender
        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = baseline + 1.25 * max_descent

        # Update the Layout’s x, y, and line fields. x and line
        self.cursor_x = HSTEP # HSTEP as margin value
        self.line =[]
    
# Gather text into Text and Tag objects
def lex(body):
    out = []
    buffer = "" # Temp to hold our string we're building up
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