import math
import tkinter
import tkinter.font

# move set_parameters from browser to layout

# Chapter3-exercise-centered-text
def set_parameters(**params):
    global WIDTH, HEIGHT, HSTEP, VSTEP, SCROLL_STEP
    if "WIDTH" in params: WIDTH = params["WIDTH"]
    if "HEIGHT" in params: HEIGHT = params["HEIGHT"]
    if "HSTEP" in params: HSTEP = params["HSTEP"]
    if "VSTEP" in params: VSTEP = params["VSTEP"]
    if "SCROLL_STEP" in params: SCROLL_STEP = params["SCROLL_STEP"]

# Helper classes for chapter 3
class Text:
    def __init__(self, text):
        self.text = text
    def __repr__(self):
        return "Text('{}')".format(self.text)

class Tag:
    def __init__(self, tag):
        self.tag = tag
    def __repr__(self):
        return "Tag('{}')".format(self.tag)

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
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
    def __init__(self, tokens):
        self.display_list = []
        self.cursor_x = HSTEP
        self.cursor_y = VSTEP
        self.weight = "normal"
        self.style = "roman"
        self.size = 16
        self.center = False # Chapter3-exercise-centered-text
        self.sup = False #superscripts exercise
        self.in_abbr = False # small-caps exercise
        self.sup_y = math.inf

        self.line = []

        for tok in tokens:
            self.token(tok)

        self.flush()

    def token(self, tok):
        if isinstance(tok, Text):
            for word in tok.text.split():
                self.word(word)
            return

        if tok.tag == "i":
            self.style = "italic"
        elif tok.tag == "/i": # Closing tag
            self.style = "roman"
        elif tok.tag == "b":
            self.weight = "bold"
        elif tok.tag == "/b":
            self.weight = "normal"
        elif tok.tag == "small":
            self.size -= 2
        elif tok.tag == "/small":
            self.size += 2
        elif tok.tag == "big":
            self.size += 4
        elif tok.tag == "/big":
            self.size -= 4
        elif tok.tag == "br": # Line break
            self.flush()
        elif tok.tag == "/p": # Closing paragraph
            self.flush()
            self.cursor_y += VSTEP
        # chapter3-exercise-centered-text
        elif tok.tag == "h1 class=\"title\"":
            self.flush()
            self.center = True
        elif tok.tag == "/h1":
            self.flush()
            self.center = False
        elif tok.tag == "sup": # Superscripts exercise
            self.flush_base()
            self.sup = True
        elif tok.tag == "/sup":
            self.flush_base()
            self.sup = False
        elif tok.tag == "abbr":
            self.in_abbr = True
        elif tok.tag == "/abbr":
            self.in_abbr = False

    def word(self, word):
        font = get_font(self.size, self.weight, self.style)

        # Chapter 3 small caps exercise
        if self.in_abbr:
            abbr_font = get_font(self.size // 2, "bold", self.style)
            split_word = self.split_abbr(word)

            for word_part in split_word:
                if word_part[0].islower():
                    word_part = word_part.upper()
                    w = abbr_font.measure(word_part)

                    if self.cursor_x + w >= WIDTH - HSTEP:
                        self.flush()

                    self.line.append((self.cursor_x, word_part, abbr_font))
                    self.cursor_x += w
                else:
                    w = font.measure(word_part)
                    if self.cursor_x + w >= WIDTH - HSTEP:
                        self.flush()

                    self.line.append((self.cursor_x, word_part, font))
                    self.cursor_x += w

            self.cursor_x += font.measure(" ")
            return

        # Chapter3 soft-hyphens exercise
        if self.sup:
            font = get_font(self.size // 2, self.weight, self.style)

        if "\N{soft hyphen}" in word:
            words = word.split("\N{soft hyphen}")

            line_prefix = ""
            for curr, part in enumerate(words):
                if curr == len(words) - 1:
                    line_prefix += part
                    break

                line_prefix += part
                w = font.measure(line_prefix + "-")
                next_w = font.measure(line_prefix + words[curr + 1] + "-")
                if (
                    self.cursor_x + w <= WIDTH - HSTEP
                    and self.cursor_x + next_w > WIDTH - HSTEP
                ):
                    self.line.append((self.cursor_x, line_prefix + "-", font))
                    self.flush()
                    line_prefix = ""
                
            self.line.append((self.cursor_x, line_prefix, font))
            self.cursor_x += font.measure(line_prefix + " ")
        else:
            w = font.measure(word)
            if self.cursor_x + w >= WIDTH - HSTEP:
                self.flush()

            self.line.append((self.cursor_x, word, font))
            self.cursor_x += w + font.measure(" ")


    # Chapter 3 small caps exercise
    def split_abbr(self, word):
        words = list()
        if not word:
            return words

        is_lower = word[0].islower()
        curr_word = ""
        for char in word:
            if (char.islower() and not is_lower) or (not char.islower() and is_lower):
                words.append(curr_word)
                curr_word = ""
                is_lower = char.islower()
            curr_word += char

        if curr_word:
            words.append(curr_word)

        return words

    def flush(self):
        if not self.line:
            return

        baseline, max_descent = self.flush_base()
        self.sup_y = 0
        self.cursor_y = baseline + 1.25 * max_descent
        self.cursor_x = HSTEP

    def flush_base(self):
        # Computing where that line should be depends on the tallest word on the line
        metrics = [font.metrics() for x, word, font in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])
        baseline = self.cursor_y + 1.25 * max_ascent

        # Chapter3-exercise-centered-text
        if self.center:
            final_x, final_word, final_font = self.line[-1]
            line_length = self.cursor_x - final_font.measure(" ") - HSTEP
            padding = (WIDTH - line_length) // 2 - HSTEP
        else:
            padding = 0

        for x, word, font in self.line:
            y = baseline - font.metrics("ascent")
            if not self.sup:
                self.sup_y = min(self.sup_y, y)
            # Chapter3-exercise-superscripts
            if self.sup:
                y = self.sup_y

            self.display_list.append((x + padding, y, word, font))
        
        self.line = []
        max_descent = max(metric["descent"] for metric in metrics)
        return baseline, max_descent
    
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