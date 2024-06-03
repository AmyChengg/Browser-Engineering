import dukpy
from cssparser import *

RUNTIME_JS = open("runtime.js").read()
EVENT_DISPATCH_JS = \
    "new Node(dukpy.handle).dispatchEvent(new Event(dukpy.type))"

class JSContext:
    def __init__(self, tab):
        self.interp = dukpy.JSInterpreter()
        self.interp.export_function("log", print)
        self.interp.evaljs(RUNTIME_JS)
        self.interp.export_function("querySelectorAll",
            self.querySelectorAll)
        self.tab = tab
        self.node_to_handle = {}
        self.handle_to_node = {}

        self.interp.export_function("getAttribute", self.getAttribute)
        self.interp.export_function("innerHTML_set", self.innerHTML_set)
        self.interp.export_function("createElement", self.createElement)
        self.interp.export_function("appendChild", self.appendChild)
        self.interp.export_function("insertBefore", self.insertBefore)
        self.interp.export_function("getChildren", self.getChildren)


    def run(self, code):
        return self.interp.evaljs(code)
    
    # ch9-node-children-exercise
    def getChildren(self, handle):
        elt = self.handle_to_node[handle]
        return [self.get_handle(child) for child in elt.children if isinstance(child, Element)]
    
    # ch9-create-element-exercise
    def createElement(self, tag):
        new_elt = Element(tag, {}, None)
        handle = self.get_handle(new_elt)
        return handle
    
    def appendChild(self, parent, child):
        node_parent = self.handle_to_node[parent] 
        node_child = self.handle_to_node[child] 
        node_child.parent = node_parent
        node_parent.children.append(node_child)
    
    def insertBefore(self, parent, element, before):
        node_parent = self.handle_to_node[parent]
        node_element = self.handle_to_node[element]
        node_element.parent = node_parent
        if (before == -1):
            node_parent.children.append(node_element)
        else:
            node_before = self.handle_to_node[before]
            for i, node in enumerate(node_parent.children):
                if node == node_before:
                    node_parent.children.insert(i, node_element)
                    break

    def get_handle(self, elt):
        if elt not in self.node_to_handle:
            handle = len(self.node_to_handle)
            self.node_to_handle[elt] = handle
            self.handle_to_node[handle] = elt
        else:
            handle = self.node_to_handle[elt]
        return handle
    
    def querySelectorAll(self, selector_text):
        selector = CSSParser(selector_text).selector()
        nodes = [node for node
             in tree_to_list(self.tab.nodes, [])
             if selector.matches(node)]
        return [self.get_handle(node) for node in nodes]
    
    def getAttribute(self, handle, attr):
        elt = self.handle_to_node[handle]
        attr = elt.attributes.get(attr, None)
        return attr if attr else ""

    #ch9-bubbling-exercise
    def dispatch_event(self, type, elt):
        handle = self.node_to_handle.get(elt, -1)
        ret = self.interp.evaljs(EVENT_DISPATCH_JS, type=type, handle=handle)
        if not ret["stop_propagation"] and elt.parent:
            self.dispatch_event(type, elt.parent)
        return not ret["do_default"]

    def innerHTML_set(self, handle, s):
        doc = HTMLParser("<html><body>" + s + "</body></html>").parse()
        new_nodes = doc.children[0].children
        elt = self.handle_to_node[handle]
        elt.children = new_nodes
        for child in elt.children:
            child.parent = elt
        self.tab.render()

def tree_to_list(tree, list):
    list.append(tree)
    for child in tree.children:
        tree_to_list(child, list)
    return list