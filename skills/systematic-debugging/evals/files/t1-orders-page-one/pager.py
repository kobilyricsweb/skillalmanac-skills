def paginate(items, page, size):
    """Return one page of items. `page` counts from 0."""
    start = page * size
    return items[start:start + size]
