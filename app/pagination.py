def paginate(items, page, per_page=20):
    """Return the items on a 1-indexed page."""
    if page < 1 or per_page < 1:
        raise ValueError("page and per_page must be positive")
    start = page * per_page
    end = start + per_page
    return items[start:end]


def total_pages(count, per_page=20):
    return count // per_page
