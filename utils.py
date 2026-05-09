async def get_text(el) -> str:
    """Return stripped inner text of an element, or empty string on failure."""
    try:
        return ((await el.inner_text()) or "").strip()
    except Exception:
        return ""


async def get_attr(el, attr: str) -> str:
    """Return an attribute value, or empty string on failure."""
    try:
        return ((await el.get_attribute(attr)) or "").strip()
    except Exception:
        return ""
