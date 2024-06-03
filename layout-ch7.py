import tkinter
import tkinter.font
from params import *
from htmlparser import *
from htmlparser import Text, Element
from draw_commands import *
from browser import *

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100 

def set_parameters(**params):
    global WIDTH, HEIGHT, HSTEP, VSTEP, SCROLL_STEP
    if "WIDTH" in params: WIDTH = params["WIDTH"]
    if "HEIGHT" in params: HEIGHT = params["HEIGHT"]
    if "HSTEP" in params: HSTEP = params["HSTEP"]
    if "VSTEP" in params: VSTEP = params["VSTEP"]
    if "SCROLL_STEP" in params: SCROLL_STEP = params["SCROLL_STEP"]

def paint_tree(layout_object, display_list):
    display_list.extend(layout_object.paint())

    for child in layout_object.children:
        paint_tree(child, display_list)

class DocumentLayout:
    def __init__(self, node):
        self.node = node
        self.parent = None
        self.previous = None
        self.children = []

        self.x = None
        self.y = None
        self.width = None
        self.height = None

    def layout(self):
        child = BlockLayout(self.node, self, None)
        self.children.append(child)
        
        self.width = WIDTH - 2 * HSTEP
        self.x = HSTEP
        self.y = VSTEP

        child.layout()
 
        self.height = child.height + 2 * VSTEP

    def paint(self):
        return []
    
    def __repr__(self):
        return "DocumentLayout()"
    
BLOCK_ELEMENTS = [
    "html", "body", "article", "section", "nav", "aside",
    "h1", "h2", "h3", "h4", "h5", "h6", "hgroup", "header",
    "footer", "address", "p", "hr", "pre", "blockquote",
    "ol", "ul", "menu", "li", "dl", "dt", "dd", "figure",
    "figcaption", "main", "div", "table", "form", "fieldset",
    "legend", "details", "summary"
]

class BlockLayout:
    def __init__(self, tree, parent, previous):
        self.tree = tree
        self.parent = parent
        self.previous = previous
        self.children = []

        self.x = None
        self.y = None
        self.width = None
        self.height = None
    
    def layout_mode(self):
        if isinstance(self.tree, Text):
            return "inline"
        elif any([isinstance(child, Element) and \
                  child.tag in BLOCK_ELEMENTS
                  for child in self.tree.children]):
            return "block"
        elif self.tree.children:
            return "inline"
        else:
            return "block"

    def layout(self):
        self.x = self.parent.x
        self.width = self.parent.width

        if self.previous:
            self.y = self.previous.y + self.previous.height
        else:
            self.y = self.parent.y
            
        mode = self.layout_mode()
        if mode == "block":
            previous = None
            for child in self.tree.children:
                block = BlockLayout(child, self, previous)
                self.children.append(block)
                previous = block
        else:
            self.new_line()
            self.recurse(self.tree)            

        for child in self.children:
            child.layout()

        self.height = sum([ child.height for child in self.children ])

    def recurse(self, tree):
        if isinstance(tree, Text):
            for word in tree.text.split():
                self.word(tree, word)
        else:
            if tree.tag == "br":
                self.new_line()
            for child in tree.children:
                self.recurse(child)

    def word(self, tree, word):
        weight = tree.style["font-weight"]
        style = tree.style["font-style"]
        if style == "normal": style = "roman"
        size = int(float(tree.style["font-size"][:-2]) * .75)
        font = get_font(size, weight, style)
        
        w = font.measure(word)

        if self.cursor_x + w >= self.width:
            self.new_line()
        
        line = self.children[-1]
        previous_word = line.children[-1] if line.children else None
        text = TextLayout(tree, word, line, previous_word)
        line.children.append(text)    
        self.cursor_x += w + font.measure(" ")
    
    def flush(self):
        if not self.line: return
        metrics = [font.metrics() for x, word, font, superscript, color in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])

        baseline = self.cursor_y + 1.25 * max_ascent

        font = self.line[-1][2]
        line_length = self.cursor_x - font.measure(" ") - HSTEP
        padding = ((WIDTH - line_length) // 2) - HSTEP

        for rel_x, word, font, superscript, color in self.line:
            x = self.x + rel_x
            y = self.y + baseline - font.metrics("ascent")
            self.display_list.append((x, y, word, font, color))

        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = baseline + 1.25 * max_descent

        self.cursor_x = 0
        self.line = []

    def paint(self):
        cmds = []
        bgcolor = self.tree.style.get("background-color", "transparent")
        if bgcolor != "transparent":
            rect = DrawRect(self.self_rect(), bgcolor)
            cmds.append(rect)
        return cmds
    
    def new_line(self):
        self.cursor_x = 0
        last_line = self.children[-1] if self.children else None
        new_line = LineLayout(self.tree, self, last_line)
        self.children.append(new_line)

    def self_rect(self):
        return Rect(self.x, self.y,
            self.x + self.width, self.y + self.height)
    
    def __repr__(self):
        return "BlockLayout(x={}, y={}, width={}, height={})".format(
            self.x, self.y, self.width, self.height)

FONTS = {}
    
# def get_font(size, weight, slant):
#     key = (size, weight, slant)
#     if key not in FONTS:
#         font = tkinter.font.Font(size=size, weight=weight, slant=slant)
#         label = tkinter.Label(font=font)
#         FONTS[key] = (font, label)
#     return FONTS[key][0]

def get_font(size, weight, slant, family="Times"):
    key = (size, weight, slant, family)
    if key not in FONTS:
        font = tkinter.font.Font(
            size=size, weight=weight, slant=slant, family=family
        )
        label = tkinter.Label(font=font)
        FONTS[key] = (font, label)
    return FONTS[key][0]
        
def load(url):
    body = url.request()
    HTMLParser(body).parse()

class LineLayout:
    def __init__(self, node, parent, previous):
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children = []
    
    def layout(self):
        self.x = self.parent.x
        self.width = self.parent.width

        if self.previous:
            self.y = self.previous.y + self.previous.height
        else:
            self.y = self.parent.y

        for child in self.children:
            child.layout()

        if not self.children:
            self.height = 0
            return

        metrics = [word.font.metrics() for word in self.children]
        max_ascent = max([metric["ascent"] for metric in metrics])

        baseline = self.y + 1.25 * max_ascent

        for word in self.children:
            word.y = baseline - word.font.metrics("ascent")

        max_descent = max([metric["descent"] for metric in metrics])

        self.height = 1.25 * (max_ascent + max_descent)

    def paint(self):
        return []

    def __repr__(self):
        return "LineLayout(x={}, y={}, width={}, height={})".format(
            self.x, self.y, self.width, self.height)

class TextLayout:
    def __init__(self, node, word, parent, previous):
        self.node = node
        self.word = word
        self.parent = parent
        self.previous = previous

        self.children = []
    
    def layout(self):
        weight = self.node.style["font-weight"]
        style = self.node.style["font-style"]
        if style == "normal": style = "roman"
        size = int(float(self.node.style["font-size"][:-2]) * 0.75)
        self.font = get_font(size, weight, style)
    
        self.width = self.font.measure(self.word)

        if self.previous:
            space = self.previous.font.measure(" ")
            self.x = self.previous.x + space + self.previous.width
        else:
            self.x = self.parent.x

        self.height = self.font.metrics("linespace")
    
    def paint(self):
        # color = self.node.style["color"]
        color = self.node.style.get("color", "black")
        return[DrawText(self.x, self.y, self.word, self.font, color)]

    def __repr__(self):
        return ("TextLayout(x={}, y={}, width={}, height={}, word={})").format(
            self.x, self.y, self.width, self.height, self.word)
