# Chapter 4
from browser import *
from url import *
from layout import *

class Text:
    def __init__(self, text, parent):
        self.text = text
        self.children = []
        self.parent = parent
    def __repr__(self): # Print tree
        return repr(self.text)

class Element:
    def __init__(self, tag, attributes, parent):
        self.tag = tag
        self.attributes = attributes
        self.children = []
        self.parent = parent
    def __repr__(self):
        attrs = [" " + k + "=\"" + v + "\"" for k, v  in self.attributes.items()]
        attr_str = ""
        for attr in attrs:
            attr_str += attr
        return "<" + self.tag + attr_str + ">"

# Chapter 4 core
class HTMLParser:
    def __init__(self, body):
        self.body = body
        self.unfinished = []  # unfinished list storing the tree starts empty

    def get_attributes(self, text):
        # Chapter4-exercise-quoted attributes
        if "'" in text and '"' not in text:
            text = text.replace("'", '"')

        if " " not in text:
            return text, dict()

        in_quote = None
        in_key = True
        in_value = False
        attributes = dict()
        tag, attrs = text.split(" ", 1)
        key, value = "", ""
        for c in attrs:
            if c == " " and not in_quote:
                attributes[key.casefold()] = value
                key, value = "", ""
                in_key = True
                in_value = False
            elif in_key and key != "" and c == "=" and not in_quote:
                in_key = False
                in_value = True
            elif c in ('"', "'"):
                if c == in_quote:
                    assert in_value
                    in_quote = False
                    attributes[key.casefold()] = value
                    key, value = "", ""
                    in_key = True
                    in_value = False
                elif in_quote is None:
                    in_quote = c
                else:
                    value += c
            elif in_key:
                key += c
            elif in_value:
                value += c

        if key:
            attributes[key.casefold()] = value

        return tag, attributes
    
    # Compare to the list of unfinished tags to determine what’s been omitted
    def implicit_tags(self, tag):
        while True:
            open_tags = [node.tag for node in self.unfinished]
            if open_tags == [] and tag != "html":
                self.add_tag("html")

            elif open_tags == ["html"] \
                and tag not in ["head", "body", "/html"]:
                if tag in self.HEAD_TAGS:
                    self.add_tag("head")
                else:
                    self.add_tag("body")
            

            elif open_tags == ["html", "head"] and \
                tag not in ["/head"] + self.HEAD_TAGS:
                self.add_tag("/head")
            else: break
    
    def parse(self):
        text = ""
        in_tag = False
        in_comment = False
        in_script = False
        for i, c in enumerate(self.body):
            if in_script:
                if self.body[i:i+len('</script>')] == '</script>':
                    in_script = False
                    self.add_text(text)
                    i += len('</script>')
                    text = ""
                    continue
                else:
                    text += c
                    continue
            if not in_script and self.body[i-len('<script>'):i] == '<script>':
                in_script = True
                text = " "
                continue
            if in_comment:
                if self.body[i-3:i] == '-->' and self.body[i-5:i] != '<!-->' and self.body[i-6:i] != '<!--->':
                    in_comment = False
                else:
                    continue

            if c == "<":
                if self.body[i:i+4] == '<!--':
                    in_comment = True
                    if text: 
                        self.add_text(text)
                        text = ""
                    continue
                in_tag = True
                if text: 
                    self.add_text(text)
                    text = ""
            elif c == ">":
                in_tag = False
                self.add_tag(text)
                text = ""
            else:
                text += c
        if not in_tag and text:
            self.add_text(text)
        return self.finish()
   
    # To add a text node we add it as a child of the last unfinished node
    def add_text(self, text):
        if text.isspace(): return # skip whitespace-only text nodes
        self.implicit_tags(None)
        parent = self.unfinished[-1]  # Get the last thing
        node = Text(text, parent)
        parent.children.append(node)

    def add_tag(self, tag):
        if tag.startswith("!"): return # Throw out <!doctype html> tag and comments
        
        tag, attributes = self.get_attributes(tag)
        self.implicit_tags(tag)

        open_tags = [node.tag for node in self.unfinished]

        if tag in self.SELF_CLOSING_TAGS:
            parent = self.unfinished[-1]
            node = Element(tag, attributes=attributes, parent=parent)
            parent.children.append(node)

        # A close tag finishes the last unfinished node by adding it to the previous unfinished node in the list
        elif tag.startswith("/"):
             # The very last tag is also an edge case, because there’s no unfinished node to add it to
            if len(self.unfinished) == 1: return
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        
        # Chapter4-exercise-paragraphs
        
        elif tag == "p" and "p" in open_tags:
            rebuild_tags = list()
            last_tag = self.unfinished.pop()
            while last_tag.tag != "p":
                rebuild_tags.append(last_tag)
                grandparent = self.unfinished[-1]
                grandparent.children.append(last_tag)
                last_tag = self.unfinished.pop()
            grandparent = self.unfinished[-1] # Close p tag
            grandparent.children.append(last_tag)

            t, attributes = self.get_attributes(tag) # Open new p tag
            # pnode = Element(t, grandparent, attributes)
            pnode = Element(t, attributes=attributes, parent=grandparent)

            self.unfinished.append(pnode)

            # Reopen all tags with new Element objects
            for node in rebuild_tags:
                parent = self.unfinished[-1]
                # rnode = Element(node.tag, parent, node.attributes)
                rnode = Element(node.tag, attributes=node.attributes, parent=parent)

                self.unfinished.append(rnode)

        # An open tag adds an unfinished node to the end of the list
        else:
            parent = self.unfinished[-1] if self.unfinished else None
            node = Element(tag, attributes=attributes, parent=parent)
            self.unfinished.append(node)
        
   
    # Once the parser is done, it turns the incomplete tree into a complete tree by just finishing any unfinished nodes
    def finish(self):
        if not self.unfinished:
            self.implicit_tags(None)
        while len(self.unfinished) > 1:
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        return self.unfinished.pop()
    
    HEAD_TAGS = [
        "base", "basefont", "bgsound", "noscript",
        "link", "meta", "title", "style", "script",
    ]

    SELF_CLOSING_TAGS = [
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
    ]
    
# See the tree
def print_tree(node, indent=0):
    print(" " * indent, node)
    for child in node.children:
        print_tree(child, indent + 2)