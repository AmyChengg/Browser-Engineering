import tkinter.font
from htmlparser import *
import sys

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18

def set_parameters(**params):
    global WIDTH, HEIGHT, HSTEP, VSTEP, SCROLL_STEP
    if "WIDTH" in params:
        WIDTH = params["WIDTH"]
    if "HEIGHT" in params:
        HEIGHT = params["HEIGHT"]
    if "HSTEP" in params:
        HSTEP = params["HSTEP"]
    if "VSTEP" in params:
        VSTEP = params["VSTEP"]
    if "SCROLL_STEP" in params:
        SCROLL_STEP = params["SCROLL_STEP"]

class Tag:
    def __init__(self, tag):
        self.tag = tag
    def __repr__(self):
        return "Tag('{}')".format(self.tag)

class DrawText:
    def __init__(self, x1, y1, text, font, color):
        self.top = y1
        self.left = x1
        self.bottom = y1 + font.metrics("linespace")
        self.text = text
        self.font = font
        self.color = color

    def execute(self, scroll, canvas):
        canvas.create_text(
            self.left,
            self.top - scroll,
            text=self.text,
            font=self.font,
            anchor="nw",
            fill=self.color,
        )

    def __repr__(self):
        return "DrawText(top={} left={} bottom={} text={} font={})".format(
            self.top, self.left, self.bottom, self.text, self.font
        )


class DrawRect:
    def __init__(self, x1, y1, x2, y2, color):
        self.top = y1
        self.left = x1
        self.bottom = y2
        self.right = x2
        self.color = color

    def execute(self, scroll, canvas):
        canvas.create_rectangle(
            self.left,
            self.top - scroll,
            self.right,
            self.bottom - scroll,
            width=0,
            fill=self.color,
        )

    def __repr__(self):
        return "DrawRect(top={} left={} bottom={} right={} color={})".format(
            self.top, self.left, self.bottom, self.right, self.color)

def paint_tree(layout_object, display_list):
    display_list.extend(layout_object.paint())

    for child in layout_object.children:
        paint_tree(child, display_list)


FONTS = {}
def get_font(size, weight, slant, family="Times"):
    key = (size, weight, slant, family)
    if key not in FONTS:
        font = tkinter.font.Font(
            size=size, weight=weight, slant=slant, family=family
        )
        label = tkinter.Label(font=font)
        FONTS[key] = (font, label)
    return FONTS[key][0]


BLOCK_ELEMENTS = [
    "html", "body", "article", "section", "nav", "aside",
    "h1", "h2", "h3", "h4", "h5", "h6", "hgroup", "header",
    "footer", "address", "p", "hr", "pre", "blockquote",
    "ol", "ul", "menu", "li", "dl", "dt", "dd", "figure",
    "figcaption", "main", "div", "table", "form", "fieldset",
    "legend", "details", "summary"
]

class DocumentLayout:
    def __init__(self, node):
        self.node = node
        self.parent = None
        self.children = []

        self.x = None
        self.y = None
        self.width = None
        self.height = None

    def __repr__(self):
        return "DocumentLayout()"

    def layout(self):
        child = BlockLayout(self.node, self, None)
        self.children.append(child)

        self.width = WIDTH - 2 * HSTEP
        self.x = HSTEP
        self.y = VSTEP

        child.layout()
        self.height = child.height

        self.display_list = child.display_list

    def paint(self):
        return []


class BlockLayout:
    def __init__(self, node_tree, parent, previous):
        self.node = node_tree
        self.parent = parent
        self.previous = previous
        self.children = []
        self.display_list = []
        self.cursor_x = HSTEP
        self.cursor_y = VSTEP
        self.weight = "normal"
        self.style = "roman"
        self.size = 16
        self.center = False
        self.in_abbr = False
        self.sup = False
        self.width = 0
        self.height = 0

        self.line = []

    def __repr__(self):
        return "BlockLayout(x={}, y={}, width={}, height={})".format(
            self.x, self.y, self.width, self.height)
    
    def layout_mode(self):
        if isinstance(self.node, Text):
            return "inline"
        elif any(
            [
                isinstance(child, Element) and child.tag in BLOCK_ELEMENTS
                for child in self.node.children]):
            return "block"
        elif self.node.children:
            return "inline"
        else:
            return "block"

    def layout(self):
        self.x = self.parent.x
        self.width = (
            self.width + self.parent.width
            if self.node.style.get("width", "auto") == "auto"
            else self.node.style["width"]
        )

        if self.previous:
            self.y = self.previous.y + self.previous.height
        else:
            self.y = self.parent.y

        if isinstance(self.node, Element) and self.node.tag == "li":
            self.x += 2 * HSTEP
            self.width -= 2 * HSTEP

        mode = self.layout_mode()
        if mode == "block":
            previous = None
            siblings = []

            for child in self.node.children:
                if isinstance(child, Element) and child.tag == "head":
                    continue

                if isinstance(child, Text) or child.tag not in BLOCK_ELEMENTS:
                    siblings.append(child)
                    continue

                if len(siblings) > 0:
                    next = BlockLayout(
                        siblings[0], self, previous, more_nodes=siblings[1:]
                    )
                    self.children.append(next)
                    previous = next
                    siblings = []

                next = BlockLayout(child, self, previous)
                self.children.append(next)
                previous = next

            if len(siblings) > 0:
                next = BlockLayout(
                    siblings[0], self, previous, more_nodes=siblings[1:]
                )
                self.children.append(next)
                previous = next
        else:
            self.cursor_x = 0
            self.cursor_y = 0
            self.weight = "normal"
            self.style = "roman"
            self.size = 16
            self.center = False
            self.in_abbr = False
            self.sup = False

            self.line = []
            self.recurse(self.node)
            self.flush()

        for child in self.children:
            child.layout()

        if self.node.style.get("height", "auto") == "auto":
            if mode == "block":
                print(self.children, file=sys.stderr)
                self.height = sum(child.height for child in self.children)
            else:
                self.height = self.cursor_y
        else:
            self.height = self.node.style["height"]

    def paint(self):
        cmds = []
        if isinstance(self.node, Element) and self.node.tag == "pre":
            x2 = self.x + self.width
            y2 = self.y + self.height
            rect = DrawRect(self.x, self.y, x2, y2, "gray")
            cmds.append(rect)

        if isinstance(self.node, Element) and self.node.tag == "li":
            y1 = self.y + self.size / 2
            y2 = y1 + 4
            x1 = self.x - HSTEP - 2
            x2 = x1 + 4
            cmds.append(DrawRect(x1, y1, x2, y2, "black"))

        if (
            isinstance(self.node, Element)
            and self.node.tag == "nav"
            and self.node.attributes.get("class") == "links"
        ):
            x2 = self.x + self.width
            y2 = self.y + self.height

            rect = DrawRect(self.x, self.y, x2, y2, color="lightgray")
            cmds.append(rect)

        bgcolor = self.node.style.get("background-color", "transparent")
        if bgcolor != "transparent":
            x2, y2 = self.x + self.width, self.y + self.height
            rect = DrawRect(self.x, self.y, x2, y2, bgcolor)
            cmds.append(rect)

        if self.layout_mode() == "inline":
            for x, y, word, font, color in self.display_list:
                cmds.append(DrawText(x, y, word, font, color))

        return cmds

    def recurse(self, node):
        if isinstance(node, Text):
            for word in node.text.split():
                self.word(node, word)
        else:
            if node.tag == "br":
                self.flush()
            for child in node.children:
                self.recurse(child)

    def open_tag(self, tag):
        if tag == "i":
            self.style = "italic"
        elif tag == "b":
            self.weight = "bold"
        elif tag == "small":
            self.size -= 2
        elif tag == "big":
            self.size += 4
        elif tag == "br":
            self.flush()
        elif tag.startswith("h1"):
            if "title" in tag:
                self.flush()
                self.center = True

    def close_tag(self, tag):
        if tag == "/i":
            self.style = "roman"
        elif tag == "/b":
            self.weight = "normal"
        elif tag == "/small":
            self.size += 2
        elif tag == "/big":
            self.size -= 4
        elif tag == "/p":
            self.flush()
            self.cursor_y += VSTEP
        elif tag == "/h1":
            self.flush()
            self.center = False

    def word(self, node, word):
        weight = node.style["font-weight"]
        style = node.style["font-style"]
        family = node.style["font-family"]
        if style == "normal":
            style = "roman"
        size = int(float(node.style["font-size"][:-2]) * 0.75)
        font = get_font(size, weight, style, family)
        color = node.style["color"]

        w = font.measure(word)

        if self.cursor_x + w >= self.width:
            self.flush()
        self.line.append((self.cursor_x, word, font, color))
        self.cursor_x += w + font.measure(" ")
    
    def flush(self):
        if not self.line:
            return
        metrics = [font.metrics() for x, word, font, color in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])
        baseline = self.cursor_y + 1.25 * max_ascent

        font = self.line[-1][2]
        line_length = self.cursor_x - font.measure(" ") - HSTEP

        if self.center:
            padding = (WIDTH - line_length) / 2 - HSTEP
        else:
            padding = 0

        for rel_x, word, font, color in self.line:
            x = self.x + rel_x
            y = self.y + baseline - font.metrics("ascent")

            if self.sup:
                y = self.sup_y

            self.display_list.append((x + padding, y, word, font, color))
        
        self.line = []
        max_descent = max(metric["descent"] for metric in metrics)
        self.cursor_y = baseline + 1.25 * max_descent
        self.cursor_x = 0
    
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