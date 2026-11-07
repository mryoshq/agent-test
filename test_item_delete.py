from fastapi.testclient import TestClient

from items import ItemStore
from main import create_app


def test_store_deletes_existing_item() -> None:
    store = ItemStore()
    item = store.create("pen", 1.5)

    assert store.delete(item.id) is True
    assert store.get(item.id) is None


def test_store_delete_missing_item_returns_false() -> None:
    assert ItemStore().delete(1) is False


def test_store_does_not_reuse_deleted_id() -> None:
    store = ItemStore()
    deleted_item = store.create("pen", 1.5)
    store.delete(deleted_item.id)

    next_item = store.create("book", 2.0)

    assert next_item.id > deleted_item.id


def test_delete_endpoint_returns_no_content_and_not_found_for_repeat() -> None:
    client = TestClient(create_app())
    created = client.post("/items", json={"name": "pen", "price": 1.5})
    item_id = created.json()["id"]

    deleted = client.delete(f"/items/{item_id}")
    repeated = client.delete(f"/items/{item_id}")

    assert deleted.status_code == 204
    assert deleted.content == b""
    assert repeated.status_code == 404
    assert repeated.json() == {"detail": "Item not found"}
