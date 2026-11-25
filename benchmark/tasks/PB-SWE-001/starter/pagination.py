from typing import Any


def paginate(
    items: list[Any],
    page: int = 1,
    page_size: int = 10,
) -> dict[str, Any]:
    """Paginate a list of items and return pagination metadata."""

    if page < 1:
        raise ValueError("Page must be >= 1")

    if page_size < 1:
        raise ValueError("Page size must be >= 1")

    total_items = len(items)

    # BUG: This incorrectly rounds down when there is a partial final page.
    total_pages = total_items // page_size

    start_index = (page - 1) * page_size
    end_index = start_index + page_size

    page_items = items[start_index:end_index]

    return {
        "items": page_items,
        "page": page,
        "page_size": page_size,
        "total_items": total_items,
        "total_pages": total_pages,
        "has_previous": page > 1,
        "has_next": page < total_pages,
    }