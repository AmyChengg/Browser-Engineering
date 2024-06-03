import math
import tkinter
import tkinter.font
from params import *
from htmlparser import *

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

# Chapter5 core
BLOCK_ELEMENTS = [
    "html", "body", "article", "section", "nav", "aside",
    "h1", "h2", "h3", "h4", "h5", "h6", "hgroup", "header",
    "footer", "address", "p", "hr", "pre", "blockquote",
    "ol", "ul", "menu", "li", "dl", "dt", "dd", "figure",
    "figcaption", "main", "div", "table", "form", "fieldset",
    "legend", "details", "summary"
]

# Backgrounds are rectangles
class DrawText:
    def __init__(self, x1, y1, text, font):
        self.top = y1
        self.left = x1
        self.text = text
        self.font = font
        self.bottom = y1 + font.metrics("linespace")

    # Draw each graphics command
    def execute(self, scroll, canvas):
        canvas.create_text(
            self.left, self.top - scroll,
            text=self.text,
            font=self.font,
            anchor='nw')
    
    def __repr__(self):
        return "DrawText(top={} left={} bottom={} text={} font={})" \
            .format(self.top, self.left, self.bottom, self.text, self.font)
    
class DrawRect:
    def __init__(self, x1, y1, x2, y2, color):
        self.top = y1
        self.left = x1
        self.bottom = y2
        self.right = x2
        self.color = color
    
    def execute(self, scroll, canvas):
        canvas.create_rectangle(
            self.left, self.top - scroll,
            self.right, self.bottom - scroll,
            width=0,
            fill=self.color)
   
    def __repr__(self):
        return "DrawRect(top={} left={} bottom={} right={} color={})".format(
            self.top, self.left, self.bottom, self.right, self.color)

def paint_tree(layout_object, display_list):
    display_list.extend(layout_object.paint())

    for child in layout_object.children:
        paint_tree(child, display_list)

class DocumentLayout:
    def __init__(self, node):
        self.node = node
        self.parent = None
        self.children = []
        
        self.x = None
        self.y = None
        self.width = None
        self.height = None

    def layout(self):
        child = BlockLayout(self.node, self, None)

        self.children.append(child)

        self.width = WIDTH - 2*HSTEP 
        self.x = HSTEP 
        self.y = VSTEP
        child.layout()
        self.height = child.height

        self.display_list = child.display_list

    def paint(self):
        return [] 
    
    def __str__(self):
        return "DocumentLayout()"

class BlockLayout:
    def __init__(self, node, parent, previous, more_nodes=[]):
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children = []

        self.x = None
        self.y = None
        self.width = None
        self.height = None
        self.line = []

        self.display_list = []
        self.more_nodes = more_nodes

    def __repr__(self):
        return "BlockLayout(x={}, y={}, width={}, height={})".format(
            self.x, self.y, self.width, self.height)
    
    def layout_mode(self):
        if isinstance(self.node, Text):
            return "inline"
        elif any([isinstance(child, Element) and \
                  child.tag in BLOCK_ELEMENTS
                  for child in self.node.children]):
            return "block"
        elif self.node.children:
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
        
        if isinstance(self.node, Element) and self.node.tag == "li":
            self.x += 2*HSTEP
            self.width -= 2*HSTEP

            
        mode = self.layout_mode()
        if mode == "block":
            previous = None
            siblings = []
            for child in self.node.children:
                if isinstance(child, Element): 
                    if child.tag == 'head':
                        continue

                if isinstance(child, Text) or child.tag not in BLOCK_ELEMENTS:
                    siblings.append(child)
                    continue
            
                if len(siblings) > 0:
                    next = BlockLayout(siblings[0], self, previous, more_nodes=siblings[1:])
                    self.children.append(next)
                    previous = next
                    siblings = [] # Resets
                
                block = BlockLayout(child, self, previous)
                self.children.append(block)
                previous = block
            if len(siblings) > 0:
                next = BlockLayout(siblings[0], self, previous, more_nodes=siblings[1:])
                self.children.append(next)
                previous = next
        else:
            self.cursor_x = 0
            self.cursor_y = 0
            self.weight = "normal"
            self.style = "roman"
            self.size = 16

            self.center = False
            self.superscript = False
            self.abbr = False

            self.line = []

            self.recurse(self.node)
            for w in self.more_nodes:
                self.recurse(w)
            self.flush()

        for child in self.children:
            child.layout()

        if mode == "block":
            self.height = sum([ 
                child.height for child in self.children ])
        else:
            self.height = self.cursor_y

    def paint(self):
        cmds = []

        if isinstance(self.node, Element) and self.node.tag == "pre":
            x2 = self.x + self.width
            y2 = self.y + self.height
            rect = DrawRect(self.x, self.y, x2, y2, "gray")
            cmds.append(rect)

        if isinstance(self.node, Element) and self.node.tag == "li":
            y1 = (self.size / 2) + self.y
            # y2 = self.y + (self.size / 2) + 2
            y2 = y1 + 4
            x1 = self.x - HSTEP - 2
            x2 = x1 + 4
            rect = DrawRect(x1, y1, x2, y2, "black")
            cmds.append(rect)

        if isinstance(self.node, Element) and self.node.tag == "nav" and self.node.attributes.get("class") == "links":
            x2 = self.x + self.width
            y2 = self.y + self.height
            rectangle = DrawRect(self.x, self.y, x2, y2, "lightgray")
            cmds.append(rectangle)

        if self.layout_mode() == "inline":
            for x, y, word, font in self.display_list:
                cmds.append(DrawText(x, y, word, font))
        
        return cmds

    def recurse(self, tree):
        if isinstance(tree, Text):
            for word in tree.text.split():
                self.word(word)
        else:
            self.open_tag(tree.tag)
            for child in tree.children:
                self.recurse(child)
            self.close_tag(tree.tag)
        
    def open_tag(self, tag):
        if tag == "i":
            self.style == "italic"
        elif tag == "b":
            self.weight = "bold"
        elif tag == "small":
            self.size -= 2
        elif tag == "big":
            self.size += 4
        elif tag == "br":
            self.flush()
        elif tag == "list":
            self.flush()

    def close_tag(self, tag):
        if tag == "i":
            self.style == "roman"
        elif tag == "b":
            self.weight == "normal"
        elif tag == "small":
            self.size += 2
        elif tag == "big":
            self.size -= 4
        elif tag == "p":
            self.flush()
            self.cursor_y += VSTEP
        elif tag == "list":
            self.flush()

    def word(self, word):
        font = get_font(self.size, self.weight, self.style)

        if self.abbr:
            for char in word:
                if char.islower():
                    font = get_font(self.size // 2, "bold", self.style)
                    word = word.upper()
                else:
                    font = get_font(self.size, self.weight, self.style)
        
        w = font.measure(word)

        if self.cursor_x + w >= self.width:
            self.flush()
        self.line.append((self.cursor_x, word, font, self.superscript))
        self.cursor_x += w + font.measure(" ")
        
    def flush(self):
        if not self.line: return
        metrics = [font.metrics() for x, word, font, superscript in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])

        baseline = self.cursor_y + 1.25 * max_ascent

        font = self.line[-1][2]
        line_length = self.cursor_x - font.measure(" ") - HSTEP
        padding = ((WIDTH - line_length) // 2) - HSTEP

        for rel_x, word, font, superscript in self.line:
            x = self.x + rel_x
            y = self.y + baseline - font.metrics("ascent")
            if (self.center):
                x += padding
            if (superscript):
                y = baseline - max_ascent
            self.display_list.append((x, y, word, font))

        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = baseline + 1.25 * max_descent

        self.cursor_x = 0
        self.line = []

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
