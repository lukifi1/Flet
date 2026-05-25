import base64

from app.features.qr_store.actions import (
    encode_preview_src,
    filter_qr_codes,
    parse_sort_value,
    sort_qr_codes,
)


# Prüft, dass Bilddaten für die Vorschau als Base64 kodiert werden.
def test_encode_preview_src_returns_base64_for_binary_data():
    binary_data = b"png bytes"

    result = encode_preview_src({"binary_data": binary_data})

    assert result == base64.b64encode(binary_data).decode()


# Prüft, dass ohne Bilddaten keine Vorschauquelle erzeugt wird.
def test_encode_preview_src_returns_empty_string_without_binary_data():
    assert encode_preview_src({}) == ""


# Prüft, dass gespeicherte QR-Codes über den Suchtext gefiltert werden.
def test_filter_qr_codes_filters_by_query():
    qr_codes = [
        {"id": 1, "qr_type": "URL", "data": "https://example.com", "category_name": "Links"},
        {"id": 2, "qr_type": "Text", "data": "Shopping list", "category_name": "Private"},
    ]

    result = filter_qr_codes(qr_codes, query="example")

    assert result == [qr_codes[0]]


# Prüft die kombinierte Filterung nach Kategorie und Favoritenstatus.
def test_filter_qr_codes_filters_by_category_and_favorite():
    qr_codes = [
        {"id": 1, "data": "Work link", "category_name": "Work", "is_favorite": True},
        {"id": 2, "data": "Work note", "category_name": "Work", "is_favorite": False},
        {"id": 3, "data": "Private note", "category_name": "Private", "is_favorite": True},
    ]

    result = filter_qr_codes(qr_codes, category_filter="Work", favorites_only=True)

    assert result == [qr_codes[0]]


# Prüft die absteigende Sortierung nach ID.
def test_sort_qr_codes_sorts_by_id_descending():
    qr_codes = [
        {"id": 1, "data": "First"},
        {"id": 3, "data": "Third"},
        {"id": 2, "data": "Second"},
    ]

    result = sort_qr_codes(qr_codes, "id", ascending=False)

    assert [qr["id"] for qr in result] == [3, 2, 1]


# Prüft die Sortierung nach Kategorie ohne Beachtung der Grossschreibung.
def test_sort_qr_codes_sorts_category_case_insensitive():
    qr_codes = [
        {"id": 1, "category_name": "work"},
        {"id": 2, "category_name": "Links"},
        {"id": 3, "category_name": "private"},
    ]

    result = sort_qr_codes(qr_codes, "category_name", ascending=True)

    assert [qr["id"] for qr in result] == [2, 3, 1]


# Prüft, dass Sortierwerte in Feldname und Richtung zerlegt werden.
def test_parse_sort_value_returns_field_and_direction():
    assert parse_sort_value("created_at.desc") == ("created_at", False)
    assert parse_sort_value("category_name.asc") == ("category_name", True)
    assert parse_sort_value("id") == ("id", True)
