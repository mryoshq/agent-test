from fastapi.testclient import TestClient

from items import ItemStore
from main import create_app


def test_store_assigns_increasing_ids() -> None:
    store = ItemStore()

    first = store.create("pen", 1.5)
    second = store.create("book", 2.0)

    assert first.id == 1
    assert second.id == 2


def test_store_instances_are_independent() -> None:
    first_store = ItemStore()
    second_store = ItemStore()
    item = first_store.create("pen", 1.5)

    assert first_store.get(item.id) == item
    assert second_store.get(item.id) is None


def test_create_and_read_item_endpoints() -> None:
    client = TestClient(create_app())

    created = client.post("/items", json={"name": "pen", "price": 1.5})

    assert created.status_code == 201
    assert created.json() == {"id": 1, "name": "pen", "price": 1.5}
    assert client.get("/items/1").json() == created.json()


def test_read_missing_item_returns_not_found() -> None:
    response = TestClient(create_app()).get("/items/1")

    assert response.status_code == 404
    assert response.json() == {"detail": "Item not found"}
