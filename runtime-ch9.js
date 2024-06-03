console = { log: function(x) { call_python("log", x); } }

function Node(handle) { this.handle = handle; this.children = []; }

// ch9-node-children-exercise
Node.prototype.getChildren = function(parent) {
    return this.children;
}

Node.prototype.getAttribute = function(attr) {
    return call_python("getAttribute", this.handle, attr);
}

Node.prototype.appendChild = function(child) {
    return call_python("appendChild", this.handle, child.handle);
}

Node.prototype.insertBefore = function(element, before) {
    var handle = -1;
    if (before != null) {
        handle = before.handle;
    }
    return call_python("insertBefore", this.handle, element.handle, handle);
}

document = { querySelectorAll: function(s) {
    var handles = call_python("querySelectorAll", s);
    return handles.map(function(h) { return new Node(h) });
},
    // ch9-create-element exercise
    createElement: function(tag) {
        var handle = call_python("createElement", tag);
        return new Node(handle);
    }}

LISTENERS = {}

Node.prototype.addEventListener = function(type, listener) {
    if (!LISTENERS[this.handle]) LISTENERS[this.handle] = {};
    var dict = LISTENERS[this.handle];
    if (!dict[type]) dict[type] = [];
    var list = dict[type];
    list.push(listener);
}

Node.prototype.dispatchEvent = function(evt) {
    var type = evt.type;
    var handle = this.handle;
    var list = (LISTENERS[handle] && LISTENERS[handle][type]) || [];
    for (var i = 0; i < list.length; i++) {
        list[i].call(this, evt);
    }
    return {"do_default" : evt.do_default, "stop_propagation" : evt.stop_propagation};
}

function Event(type) {
    this.type = type
    this.do_default = true;
    this.stop_propagation = false // exercise
}

Event.prototype.preventDefault = function() {
    this.do_default = false;
}

Object.defineProperty(Node.prototype, 'innerHTML', {
    set: function(s) {
        call_python("innerHTML_set", this.handle, s.toString());
    }
});

//ch9-node-children-exercise
Object.defineProperty(Node.prototype, 'children', {
    get: function() {
        return handleToNodes(call_python("getChildren", this.handle));
    }
});

function handleToNodes(handles) {
    return handles.map(function(h) { return new Node(h) });
}

// ch9-bubbling-exercise
Event.prototype.stopPropagation = function() {
    this.stop_propagation = true;
}