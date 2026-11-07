import os
from collections.abc import Callable

import httpx
import pytest
from fastapi.testclient import TestClient


INVALID_BODIES = [
    pytest.param({"price": 1.5}, "name", id="missing-name"),
    pytest.param({"name": "", "price": 1.5}, "name", id="empty-name"),
    pytest.param({"name": "a" * 101, "price": 1.5}, "name", id="long-name"),
    pytest.param({"name": 123, "price": 1.5}, "name", id="non-string-name"),
    pytest.param({"name": "pen"}, "price", id="missing-price"),
    pytest.param({"name": "pen", "price": -0.01}, "price", id="negative-price"),
    pytest.param({"name": "pen", "price": "abc"}, "price", id="non-number-price"),
    pytest.param({"name": "pen", "price": None}, "price", id="null-price"),
    pytest.param([], None, id="non-object-body"),
]


@pytest.fixture
def client_factory() -> Callable[[], TestClient]:
    import main

    assert callable(getattr(main, "create_app", None)), "main.create_app() is required"
    from main import create_app

    return lambda: TestClient(create_app())


@pytest.fixture
def client(client_factory: Callable[[], TestClient]) -> TestClient:
    return client_factory()


def assert_item(response: httpx.Response, status: int, name: str, price: float) -> int:
    assert response.status_code == status
    item = response.json()
    assert isinstance(item, dict)
    assert set(item) == {"id", "name", "price"}
    assert type(item["id"]) is int
    assert isinstance(item["name"], str)
    assert item["name"] == name
    assert type(item["price"]) in (int, float)
    assert item["price"] == price
    return item["id"]


def assert_validation(response: httpx.Response, field: str | None) -> None:
    assert response.status_code == 422
    body = response.json()
    assert isinstance(body, dict)
    errors = body["detail"]
    assert isinstance(errors, list)
    assert errors
    for error in errors:
        assert isinstance(error, dict)
        assert isinstance(error["loc"], list)
        assert isinstance(error["msg"], str)
        assert isinstance(error["type"], str)
    if field is None:
        assert any(error["loc"] == ["body"] for error in errors)
    else:
        assert any(error["loc"] and error["loc"][-1] == field for error in errors)


def assert_not_found(response: httpx.Response) -> None:
    assert response.status_code == 404
    assert response.json() == {"detail": "Item not found"}


def assert_empty(client: TestClient) -> None:
    response = client.get("/items")
    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "offset": 0, "limit": 10}


@pytest.mark.parametrize("name,price", [("pen", 1.5), ("a", 0), ("a" * 100, 2)])
def test_ac1_create_valid_item(client: TestClient, name: str, price: float) -> None:
    assert_item(client.post("/items", json={"name": name, "price": price}), 201, name, price)


@pytest.mark.e2e
def test_ac1_e2e_create_then_read() -> None:
    name = f"e2e-create-{os.getpid()}"
    with httpx.Client(base_url=os.environ["E2E_BASE_URL"], timeout=10) as http:
        created = http.post("/items", json={"name": name, "price": 1.5})
        item_id = assert_item(created, 201, name, 1.5)
        fetched = http.get(f"/items/{item_id}")
        assert_item(fetched, 200, name, 1.5)
        assert fetched.json() == created.json()


@pytest.mark.parametrize("body,field", INVALID_BODIES)
def test_ac2_invalid_create_stores_nothing(
    client: TestClient, body: object, field: str | None
) -> None:
    assert_validation(client.post("/items", json=body), field)
    assert_empty(client)


def test_ac3_read_existing_item(client: TestClient) -> None:
    created = client.post("/items", json={"name": "pen", "price": 1.5})
    item_id = assert_item(created, 201, "pen", 1.5)
    fetched = client.get(f"/items/{item_id}")
    assert_item(fetched, 200, "pen", 1.5)
    assert fetched.json() == created.json()


def test_ac3_read_missing_item(client: TestClient) -> None:
    assert_not_found(client.get("/items/1"))


def test_ac4_read_non_integer_id(client: TestClient) -> None:
    assert_validation(client.get("/items/abc"), "item_id")


def test_ac5_ids_start_at_one_and_increase(client: TestClient) -> None:
    for expected_id in range(1, 5):
        created = client.post("/items", json={"name": "pen", "price": 1.5})
        assert assert_item(created, 201, "pen", 1.5) == expected_id


def test_ac5_apps_have_independent_storage(
    client: TestClient, client_factory: Callable[[], TestClient]
) -> None:
    created = client.post("/items", json={"name": "first", "price": 1})
    assert assert_item(created, 201, "first", 1) == 1
    with client_factory() as other:
        assert_empty(other)
        assert_not_found(other.get("/items/1"))
        second = other.post("/items", json={"name": "second", "price": 2})
        assert assert_item(second, 201, "second", 2) == 1
        assert_item(other.get("/items/1"), 200, "second", 2)
        assert_item(client.get("/items/1"), 200, "first", 1)


def test_ac6_empty_list(client: TestClient) -> None:
    assert_empty(client)


@pytest.mark.parametrize(
    "params,offset,limit",
    [
        ({}, 0, 10),
        ({"offset": 10}, 10, 10),
        ({"offset": 20, "limit": 10}, 20, 10),
        ({"offset": 25, "limit": 10}, 25, 10),
        ({"offset": 30, "limit": 10}, 30, 10),
        ({"limit": 1}, 0, 1),
        ({"offset": 3, "limit": 4}, 3, 4),
        ({"limit": 100}, 0, 100),
    ],
)
def test_ac6_pagination(
    client: TestClient, params: dict[str, int], offset: int, limit: int
) -> None:
    items = []
    for index in range(25):
        name = f"item-{25 - index}"
        created = client.post("/items", json={"name": name, "price": index})
        assert_item(created, 201, name, index)
        items.append(created.json())
    items.sort(key=lambda item: item["id"])
    response = client.get("/items", params=params)
    assert response.status_code == 200
    page = response.json()
    assert page == {
        "items": items[offset : offset + limit],
        "total": 25,
        "offset": offset,
        "limit": limit,
    }
    for field in ("total", "offset", "limit"):
        assert type(page[field]) is int


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
def test_ac7_invalid_pagination(client: TestClient, field: str, value: str) -> None:
    assert_validation(client.get("/items", params={field: value}), field)


@pytest.mark.parametrize("name,price", [("book", 3.25), ("x", 0), ("x" * 100, 2)])
def test_ac8_update_replaces_item(client: TestClient, name: str, price: float) -> None:
    created = client.post("/items", json={"name": "pen", "price": 1.5})
    item_id = assert_item(created, 201, "pen", 1.5)
    updated = client.put(f"/items/{item_id}", json={"name": name, "price": price})
    assert assert_item(updated, 200, name, price) == item_id
    fetched = client.get(f"/items/{item_id}")
    assert_item(fetched, 200, name, price)
    assert fetched.json() == updated.json()


def test_ac8_update_missing_item_creates_nothing(client: TestClient) -> None:
    assert_not_found(client.put("/items/1", json={"name": "pen", "price": 1.5}))
    assert_not_found(client.get("/items/1"))
    assert_empty(client)


def test_ac8_update_non_integer_id(client: TestClient) -> None:
    response = client.put("/items/abc", json={"name": "pen", "price": 1.5})
    assert_validation(response, "item_id")


@pytest.mark.e2e
def test_ac8_e2e_create_update_then_read() -> None:
    name = f"e2e-update-{os.getpid()}"
    with httpx.Client(base_url=os.environ["E2E_BASE_URL"], timeout=10) as http:
        created = http.post("/items", json={"name": name, "price": 1.5})
        item_id = assert_item(created, 201, name, 1.5)
        updated_name = f"{name}-updated"
        updated = http.put(f"/items/{item_id}", json={"name": updated_name, "price": 0})
        assert assert_item(updated, 200, updated_name, 0) == item_id
        fetched = http.get(f"/items/{item_id}")
        assert_item(fetched, 200, updated_name, 0)
        assert fetched.json() == updated.json()


@pytest.mark.parametrize("body,field", INVALID_BODIES)
def test_ac9_invalid_update_preserves_item(
    client: TestClient, body: object, field: str | None
) -> None:
    created = client.post("/items", json={"name": "pen", "price": 1.5})
    item_id = assert_item(created, 201, "pen", 1.5)
    assert_validation(client.put(f"/items/{item_id}", json=body), field)
    fetched = client.get(f"/items/{item_id}")
    assert_item(fetched, 200, "pen", 1.5)
    assert fetched.json() == created.json()


def test_ac10_delete_and_never_reuse_id(client: TestClient) -> None:
    created = client.post("/items", json={"name": "pen", "price": 1.5})
    item_id = assert_item(created, 201, "pen", 1.5)
    deleted = client.delete(f"/items/{item_id}")
    assert deleted.status_code == 204
    assert deleted.content == b""
    assert_not_found(client.get(f"/items/{item_id}"))
    assert_not_found(client.delete(f"/items/{item_id}"))
    assert_empty(client)
    next_item = client.post("/items", json={"name": "book", "price": 2})
    assert assert_item(next_item, 201, "book", 2) > item_id


def test_ac10_delete_non_integer_id(client: TestClient) -> None:
    assert_validation(client.delete("/items/abc"), "item_id")


@pytest.mark.e2e
def test_ac10_e2e_create_delete_then_read_missing() -> None:
    name = f"e2e-delete-{os.getpid()}"
    with httpx.Client(base_url=os.environ["E2E_BASE_URL"], timeout=10) as http:
        created = http.post("/items", json={"name": name, "price": 1.5})
        item_id = assert_item(created, 201, name, 1.5)
        deleted = http.delete(f"/items/{item_id}")
        assert deleted.status_code == 204
        assert deleted.content == b""
        assert_not_found(http.get(f"/items/{item_id}"))
