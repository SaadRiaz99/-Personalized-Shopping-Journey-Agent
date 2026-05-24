import json

from agent.tools import (
    CATALOGUE,
    search_items_fn as search_items,
    filter_by_tag_fn as filter_by_tag,
    get_item_details_fn as get_item_details,
)


def test_search_finds_title():
    results = json.loads(search_items("dune"))
    assert any(r["title"] == "Dune" for r in results)


def test_search_finds_category():
    results = json.loads(search_items("movie"))
    assert all(r["category"] == "Movie" for r in results)


def test_search_partial_match():
    results = json.loads(search_items("mart"))
    assert any(r["title"] == "The Martian" for r in results)


def test_search_empty():
    results = json.loads(search_items("xyznonexistent"))
    assert results == []


def test_filter_by_tag_returns_matches():
    results = json.loads(filter_by_tag("sci-fi"))
    assert all("sci-fi" in r["tags"] for r in results)


def test_filter_by_tag_with_rating():
    results = json.loads(filter_by_tag("sci-fi", min_rating=4.6))
    assert all(r["rating"] >= 4.6 for r in results)


def test_filter_by_tag_no_min_rating():
    results = json.loads(filter_by_tag("sci-fi"))
    assert len(results) >= 1


def test_filter_by_tag_nonexistent():
    results = json.loads(filter_by_tag("nonexistent_tag_xyz"))
    assert results == []


def test_get_item_details_found():
    result = json.loads(get_item_details(1))
    assert result["title"] == "Dune"
    assert result["id"] == 1


def test_get_item_details_not_found():
    result = get_item_details(99999999)
    assert "No item found" in result


def test_get_item_details_edge():
    result = json.loads(get_item_details(12))
    assert result["title"] == "Philips Hue Lights"


def test_all_items_have_required_fields():
    for item in CATALOGUE:
        assert "id" in item
        assert "title" in item
        assert "tags" in item
        assert "rating" in item
        assert "category" in item


def test_ratings_in_range():
    for item in CATALOGUE:
        assert 0.0 <= item["rating"] <= 5.0
