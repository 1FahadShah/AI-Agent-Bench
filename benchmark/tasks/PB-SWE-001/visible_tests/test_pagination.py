import pytest
from pagination import paginate


def test_total_pages_rounds_up_for_partial_page():
    items = list(range(23))

    result = paginate(items, page=1, page_size=10)

    assert result["total_items"] == 23
    assert result["total_pages"] == 3


def test_has_next_is_true_when_partial_final_page_exists():
    items = list(range(23))

    result = paginate(items, page=2, page_size=10)

    assert result["has_next"] is True


def test_final_partial_page_returns_remaining_items():
    items = list(range(23))

    result = paginate(items, page=3, page_size=10)

    assert result["items"] == [20, 21, 22]
    assert result["total_pages"] == 3
    assert result["has_previous"] is True
    assert result["has_next"] is False


def test_exact_division_calculates_total_pages_correctly():
    items = list(range(20))

    result = paginate(items, page=2, page_size=10)

    assert result["total_pages"] == 2
    assert result["items"] == list(range(10, 20))
    assert result["has_next"] is False


def test_empty_input_has_zero_total_pages():
    result = paginate([], page=1, page_size=10)

    assert result["items"] == []
    assert result["total_items"] == 0
    assert result["total_pages"] == 0
    assert result["has_previous"] is False
    assert result["has_next"] is False


def test_request_beyond_final_page_returns_empty_items():
    items = list(range(23))

    result = paginate(items, page=4, page_size=10)

    assert result["items"] == []
    assert result["total_pages"] == 3
    assert result["has_previous"] is True
    assert result["has_next"] is False


def test_invalid_page_raises_value_error():
    with pytest.raises(ValueError, match="Page must be >= 1"):
        paginate([1, 2, 3], page=0, page_size=2)


def test_invalid_page_size_raises_value_error():
    with pytest.raises(ValueError, match="Page size must be >= 1"):
        paginate([1, 2, 3], page=1, page_size=0)


def test_items_are_returned_in_original_order():
    items = ["alpha", "beta", "gamma", "delta", "epsilon"]

    result = paginate(items, page=2, page_size=2)

    assert result["items"] == ["gamma", "delta"]


def test_original_items_list_is_not_mutated():
    items = list(range(23))
    original_items = items.copy()

    paginate(items, page=2, page_size=10)

    assert items == original_items