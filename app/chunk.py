def chunk(items, size):
    """Split items into lists of at most `size` elements."""
    return [items[i:i + size] for i in range(0, len(items) - size, size)]
