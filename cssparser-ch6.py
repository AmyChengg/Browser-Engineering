# Chapter 6 base code
import tkinter
import tkinter.font
from htmlparser import *

INHERITED_PROPERTIES = {
    "font-size": "16px",
    "font-family": "Times",
    "font-style": "normal",
    "font-weight": "normal",
    "color": "black",
}

class TagSelector:
    def __init__(self, tag):
        self.tag = tag
        self.priority = 1

    def matches(self, node):
        return isinstance(node, Element) and node.tag == self.tag

    def __repr__(self):
        return "TagSelector(tag={}, priority={})".format(
            self.tag, self.priority
        )

class DescendantSelector:
    def __init__(self, ancestor, descendant):
        self.ancestor = ancestor
        self.descendant = descendant
        self.priority = ancestor.priority + descendant.priority

    def matches(self, node):
        if not self.descendant.matches(node):
            return False
        while node.parent:
            if self.ancestor.matches(node.parent):
                return True
            node = node.parent
        return False

    def __repr__(self):
        return (
            "DescendantSelector(ancestor={}, descendant={}, priority={})"
        ).format(self.ancestor, self.descendant, self.priority)
    
# Ch6 class selectors exercise
class ClassSelector:
    def __init__(self, classname, priority=10):
        self.classname = classname
        self.priority = priority

    def matches(self, node):
        return (
            isinstance(node, Element)
            and "class" in node.attributes
            and self.classname in node.attributes["class"].split(" ")
        )

    def __repr__(self):
        return "ClassSelector(classname={}, priority={})".format(
            self.classname, self.priority
        )


class CSSParser:
    def __init__(self, s):
        self.s = s
        self.i = 0

    def whitespace(self):
        while self.i < len(self.s) and self.s[self.i].isspace():
            self.i += 1

    def word(self):
        start = self.i
        while self.i < len(self.s):
            if self.s[self.i].isalnum() or self.s[self.i] in "#-.%":
                self.i += 1
            else:
                break
        if not (self.i > start):
            raise Exception("Parsing error")
        return self.s[start : self.i]

    def literal(self, literal):
        if not (self.i < len(self.s) and self.s[self.i] == literal):
            raise Exception("Parsing error")
        self.i += 1

    def pair(self):
        prop = self.word()
        self.whitespace()
        self.literal(":")
        self.whitespace()
        if prop.casefold() == "font":
            val = ""
            while True:
                try:
                    w = self.word()
                    self.whitespace()
                except Exception:
                    break
                val += w + " "
            val = val[:-1]
        else:
            val = self.word()
        return prop.casefold(), val

    def body(self):
        pairs = dict()
        while self.i < len(self.s) and self.s[self.i] != "}":
            try:
                prop, value = self.pair()
                if prop.casefold() == "font":
                    values = value.split(" ")
                    if len(values) == 1:
                        pairs["font-family"] = values[0]
                    elif len(values) == 2:
                        pairs["font-size"] = values[0]
                        pairs["font-family"] = values[1]
                    elif len(values) == 3:
                        first_key = (
                            "font-style"
                            if values[0] == "italic"
                            else "font-weight"
                        )
                        pairs[first_key] = values[0]
                        pairs["font-size"] = values[1]
                        pairs["font-family"] = values[2]
                    else:
                        pairs["font-style"] = values[0]
                        pairs["font-weight"] = values[1]
                        pairs["font-size"] = values[2]
                        pairs["font-family"] = " ".join(values[3:])
                else:
                    pairs[prop.casefold()] = value

                self.whitespace()
                self.literal(";")
                self.whitespace()

            except Exception:
                why = self.ignore_until([";", "}"])
                if why == ";":
                    self.literal(";")
                    self.whitespace()
                else:
                    break
        return pairs

    def ignore_until(self, chars):
        while self.i < len(self.s) and self.s[self.i] != "}":
            char = self.s[self.i]
            if char in chars:
                return char
            else:
                self.i += 1
        return None

    def selector(self):
        def parse_selector():
            word = self.word()
            return (
                TagSelector(word.casefold())
                if not word.startswith(".")
                else ClassSelector(word[1:])
            )

        out = parse_selector()
        self.whitespace()
        while self.i < len(self.s) and self.s[self.i] != "{":
            descendant = parse_selector()
            out = DescendantSelector(out, descendant)
            self.whitespace()
        return out

    def parse(self):
        rules = []
        while self.i < len(self.s):
            try:
                self.whitespace()
                selector = self.selector()
                self.literal("{")
                self.whitespace()
                body = self.body()
                self.literal("}")
                rules.append((selector, body))
            except Exception:
                why = self.ignore_until(["}"])
                if why == "}":
                    self.literal("}")
                    self.whitespace()
                else:
                    break
        return rules


def style(node, rules):
    node.style = dict()
    for prop, default_value in INHERITED_PROPERTIES.items():
        if node.parent:
            node.style[prop] = node.parent.style[prop]
        else:
            node.style[prop] = default_value

    for selector, body in rules:
        if not selector.matches(node):
            continue
        for prop, value in body.items():
            node.style[prop] = value

    if isinstance(node, Element) and "style" in node.attributes:
        pairs = CSSParser(node.attributes["style"]).body()
        for prop, value in pairs.items():
            node.style[prop] = value

    if node.style["font-size"].endswith("%"):
        if node.parent:
            parent_font_size = node.parent.style["font-size"]
        else:
            parent_font_size = INHERITED_PROPERTIES["font-size"]
        node_pct = float(node.style["font-size"][:-1]) / 100
        parent_px = float(parent_font_size[:-2])
        node.style["font-size"] = f"{parent_px * node_pct}px"

    def processDimension(attr, node):
        if attr in node.style and node.style[attr].endswith("px"):
            value = float(node.style[attr][:-2])
            if value < 0:
                value = "auto"
            node.style[attr] = value

    processDimension("width", node)
    processDimension("height", node)

    for child in node.children:
        style(child, rules)


def cascade_priority(rule):
    selector, body = rule
    return selector.priority
