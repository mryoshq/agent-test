import pytest
from fastapi.testclient import TestClient

from items import ItemStore
from main import create_app


@pytest.mark.parametrize(
    "offset,limit", [(0, 10), (10, 10), (20, 10), (25, 10), (30, 1), (3, 4), (0, 100)]
)
def test_store_pagination(offset: int, limit: int) -> None:
    store = ItemStore()
    items = [store.create(f"item-{25 - index}", index) for index in range(25)]

    page = store.list_items(offset, limit)

    assert page.items == items[offset : offset + limit]
    assert page.total == 25
    assert page.offset == offset
    assert page.limit == limit


def test_store_listing_defaults_and_no_mutation() -> None:
    store = ItemStore()
    assert store.list_items().model_dump() == {"items": [], "total": 0, "offset": 0, "limit": 10}
    items = [store.create(f"item-{index}", index) for index in range(12)]
    assert store.list_items().items == items[:10]
    store.list_items(5, 2)
    assert store.list_items(0, 100).items == items
    assert store.create("next", 0).id == 13


def test_list_endpoint_defaults_and_app_isolation() -> None:
    first = TestClient(create_app())
    second = TestClient(create_app())
    items = [first.post("/items", json={"name": "pen", "price": 1.5}).json() for _ in range(12)]

    response = first.get("/items")
    assert response.status_code == 200
    assert response.json() == {"items": items[:10], "total": 12, "offset": 0, "limit": 10}
    assert first.get("/items?offset=10&limit=1").json() == {
        "items": items[10:11],
        "total": 12,
        "offset": 10,
        "limit": 1,
    }
    assert second.get("/items").json() == {"items": [], "total": 0, "offset": 0, "limit": 10}
    assert second.post("/items", json={"name": "book", "price": 0}).json()["id"] == 1


@pytest.mark.parametrize(
    "field,value",
    [
        ("offset", "-1"),
        ("limit", "0"),
        ("limit", "101"),
        ("offset", "abc"),
        ("limit", "abc"),
        ("offset", "1.5"),
        ("limit", "1.5"),
    ],
)
def test_list_rejects_invalid_query(field: str, value: str) -> None:
    response = TestClient(create_app()).get("/items", params={field: value})
    assert response.status_code == 422
    assert any(error["loc"] == ["query", field] for error in response.json()["detail"])


@pytest.mark.parametrize(
    "body,field",
    [
        ({"price": 1}, "name"),
        ({"name": "", "price": 1}, "name"),
        ({"name": "x" * 101, "price": 1}, "name"),
        ({"name": 123, "price": 1}, "name"),
        ({"name": "pen"}, "price"),
        ({"name": "pen", "price": -1}, "price"),
        ({"name": "pen", "price": "abc"}, "price"),
        ({"name": "pen", "price": None}, "price"),
        ([], None),
    ],
)
def test_rejected_create_preserves_listing_and_ids(body: object, field: str | None) -> None:
    client = TestClient(create_app())
    response = client.post("/items", json=body)
    assert response.status_code == 422
    location = ["body", field] if field is not None else ["body"]
    assert any(error["loc"] == location for error in response.json()["detail"])
    assert client.get("/items").json() == {"items": [], "total": 0, "offset": 0, "limit": 10}
    assert client.post("/items", json={"name": "pen", "price": 0}).json()["id"] == 1
