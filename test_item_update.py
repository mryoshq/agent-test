from fastapi.testclient import TestClient

from items import ItemStore
from main import create_app


def test_store_update_replaces_existing_item() -> None:
    store = ItemStore()
    created = store.create("pen", 1.5)

    updated = store.update(created.id, "book", 2.0)

    assert updated is not None
    assert updated.model_dump() == {"id": created.id, "name": "book", "price": 2.0}
    assert store.get(created.id) == updated


def test_store_update_missing_item_returns_none() -> None:
    assert ItemStore().update(1, "pen", 1.5) is None


def test_update_endpoint_returns_updated_item() -> None:
    client = TestClient(create_app())
    created = client.post("/items", json={"name": "pen", "price": 1.5})

    response = client.put(f"/items/{created.json()['id']}", json={"name": "book", "price": 2})

    assert response.status_code == 200
    assert response.json() == {"id": 1, "name": "book", "price": 2.0}
    assert client.get("/items/1").json() == response.json()


def test_invalid_update_keeps_existing_item_unchanged() -> None:
    client = TestClient(create_app())
    created = client.post("/items", json={"name": "pen", "price": 1.5})

    response = client.put("/items/1", json={"name": "", "price": 2})

    assert response.status_code == 422
    assert client.get("/items/1").json() == created.json()


def test_update_missing_item_returns_not_found() -> None:
    client = TestClient(create_app())

    response = client.put("/items/1", json={"name": "pen", "price": 1.5})

    assert response.status_code == 404
    assert response.json() == {"detail": "Item not found"}
    assert client.get("/items/1").status_code == 404
