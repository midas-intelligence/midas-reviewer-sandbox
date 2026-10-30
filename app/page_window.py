def page_window(current, total, size=5):
    """Page numbers to show around the current page, 1-indexed and clamped to [1, total]."""
    half = size // 2
    start = max(1, min(current - half, total - size + 1))
    end = min(total, start + size - 1)
    return list(range(start, end + 1))
