"""Helpers for sanitising HTML input to the bot."""

import bleach

__all__ = ["clean"]


"""
Take the list of allowed tags and attributes from Riot for consistency:
https://github.com/matrix-org/matrix-react-sdk/blob/master/src/HtmlUtils.js#L180-L195
"""

ALLOWED_TAGS = [
    "font",  # custom to matrix for IRC-style font coloring
    "del",  # for markdown
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "blockquote",
    "p",
    "a",
    "ul",
    "ol",
    "sup",
    "sub",
    "nl",
    "li",
    "b",
    "i",
    "u",
    "strong",
    "em",
    "strike",
    "code",
    "hr",
    "br",
    "div",
    "table",
    "thead",
    "caption",
    "tbody",
    "tr",
    "th",
    "td",
    "pre",
    "span",
    "img",
]

ALLOWED_ATTRIBUTES = {
    "font": ["color", "data-mx-bg-color", "data-mx-color", "style"],
    "span": ["data-mx-bg-color", "data-mx-color", "style"],
    "a": ["href", "name", "target", "rel"],
    "img": ["src", "width", "height", "alt", "title"],
    "ol": ["start"],
}


def clean(html, **kwargs):
    """
    Sanitise HTML fragments.

    A version of `bleach.clean` but with Riot's allowed tags and ``strip=True``
    by default.
    """
    defaults = {
        "strip": True,
        "tags": ALLOWED_TAGS,
        "attributes": ALLOWED_ATTRIBUTES,
        "protocols": ["https", "http", "mxc"],
    }
    defaults.update(kwargs)

    return bleach.clean(html, **defaults)
