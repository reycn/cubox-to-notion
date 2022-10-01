import re

from mistune.inline_parser import LINK_LABEL
from mistune.util import unikey

__all__ = ["plugin_footnotes"]

#: inline footnote syntax looks like::
#:
#:    [^key]
INLINE_FOOTNOTE_PATTERN = r"\[\^(" + LINK_LABEL + r")\]"
INLINE_FOOTNOTE_TEXT_PATTERN = r"\^\[(" + LINK_LABEL + r")\]"

#: define a footnote item like::
#:
#:    [^key]: paragraph text to describe the note
DEF_FOOTNOTE = re.compile(
    r"( {0,3})\[\^(" + LINK_LABEL + r")\]:[ \t]*" r"((?:[^\n]*(?:\n+(?: {4}| *\t)[^\n]*)*" r")+)"
)


def parse_inline_footnote(inline, m, state):
    key = unikey(m.group(1))
    def_footnotes = state.get("def_footnotes")
    if not def_footnotes or key not in def_footnotes:
        return "text", m.group(0)

    duplicates = sum([k == key for k, _, __ in state["footnotes"]])
    index = state.get("footnote_index", 0)
    if duplicates == 0:
        index += 1
        state["footnote_index"] = index
        state["footnotes"].append((key, 0, False))
    else:
        state["footnotes"].append((key, duplicates, False))
    return "footnote_ref", key, index, duplicates


def parse_inline_text_footnote(inline, m, state):
    key = unikey(m.group(1))
    index = state.get("footnote_index", 0)
    index += 1
    state["footnote_index"] = index
    state["footnotes"].append((key, 0, True))
    return "footnote_ref", key, index, 0


def parse_def_footnote(block, m, state):
    key = unikey(m.group(2))
    if key not in state["def_footnotes"]:
        state["def_footnotes"][key] = m.group(3)


def parse_footnote_item(block, k, i, is_inline_text, state):
    def_footnotes = state["def_footnotes"]

    text = k if is_inline_text else def_footnotes[k]

    stripped_text = text.strip()
    if "\n" not in stripped_text:
        children = [{"type": "paragraph", "text": stripped_text}]
    else:
        # todo: This is not perfect. Maybe replacing all tabs with 4 spaces is good.
        pattern = re.compile(r"( {4}| *\t)", flags=re.M)
        text = pattern.sub("", text, count=1)
        children = block.parse(text, state, block.rules)
        if not isinstance(children, list):
            children = [children]

    return {"type": "footnote_item", "children": children, "params": (k, i, is_inline_text)}


def md_footnotes_hook(md, result, state):
    footnotes_and_duplicates = state.get("footnotes")
    if not footnotes_and_duplicates:
        return result

    children = [
        parse_footnote_item(md.block, k, i + 1, is_inline_text, state)
        for i, (k, dup, is_inline_text) in enumerate(footnotes_and_duplicates)
        if dup == 0
    ]
    tokens = [{"type": "footnotes", "children": children}]
    output = md.block.render(tokens, md.inline, state)
    return result + output


def render_ast_footnote_ref(key, index, dup):
    return {"type": "footnote_ref", "key": key, "index": index}


def render_ast_footnote_item(children, key, index, is_inline_text):
    return {
        "type": "footnote_item",
        "children": children,
        "key": key,
        "index": index,
    }


def render_html_footnote_ref(key, index, dup):
    i = str(index)
    id_str = i if dup == 0 else i + ":" + str(dup)
    html = '<sup class="footnote-ref" id="fnref-' + id_str + '">'
    return html + '<a href="#fn-' + i + '">' + id_str + "</a></sup>"


def render_html_footnotes(text):
    return '<section class="footnotes">\n<ol>\n' + text + "</ol>\n</section>\n"


def render_html_footnote_item(text, key, index, is_inline_text):
    i = str(index)
    back = '<a href="#fnref-' + i + '" class="footnote">&#8617;</a>'

    text = key.strip() if is_inline_text else text.rstrip()
    if text.endswith("</p>"):
        text = text[:-4] + back + "</p>"
    else:
        text = text + back
    return '<li id="fn-' + i + '">' + text + "</li>\n"


def plugin_footnotes(md):
    md.inline.register_rule("footnote", INLINE_FOOTNOTE_PATTERN, parse_inline_footnote)
    md.inline.register_rule(
        "footnote_text", INLINE_FOOTNOTE_TEXT_PATTERN, parse_inline_text_footnote
    )
    index = md.inline.rules.index("std_link")
    if index != -1:
        md.inline.rules.insert(index, "footnote")
        md.inline.rules.insert(index + 1, "footnote_text")
    else:
        md.inline.rules.append("footnote")
        md.inline.rules.append("footnote_text")

    md.block.register_rule("def_footnote", DEF_FOOTNOTE, parse_def_footnote)
    index = md.block.rules.index("def_link")
    if index != -1:
        md.block.rules.insert(index, "def_footnote")
    else:
        md.block.rules.append("def_footnote")

    if md.renderer.NAME == "html":
        md.renderer.register("footnote_ref", render_html_footnote_ref)
        md.renderer.register("footnote_item", render_html_footnote_item)
        md.renderer.register("footnotes", render_html_footnotes)
    elif md.renderer.NAME == "ast":
        md.renderer.register("footnote_ref", render_ast_footnote_ref)
        md.renderer.register("footnote_item", render_ast_footnote_item)

    md.after_render_hooks.append(md_footnotes_hook)
