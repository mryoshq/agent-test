# Goal items: an /items REST API

Create, read, list with pagination, update and delete items, kept in memory, with input validation
that answers 422 and names the bad field.

## Interface contract

What tests may import and rely on. Fixed before any code exists.

- `main.create_app()` takes no arguments and returns a new FastAPI app with its own, empty item storage.
- `main.app` is `create_app()`. uvicorn serves `main:app`.
- Apps made by `create_app()` keep `GET /health`, `GET /version` and `GET /time` working as they do today.
- Tests use `fastapi.testclient.TestClient(create_app())`, importing `create_app` inside a fixture.
- An item in every response is a JSON object with exactly these keys:
  - `id`: integer, chosen by the server;
  - `name`: string;
  - `price`: number.
- A request body for create and update is a JSON object with:
  - `name`: required string, 1 to 100 characters;
  - `price`: required number, 0 or more.
- "Not found" responses are status 404 with the body `{"detail": "Item not found"}`.
- Validation errors are status 422 with FastAPI's standard body: `{"detail": [...]}`, a non-empty list whose
  entries each have `loc` (list), `msg` (string) and `type` (string).
  - For a bad body field, at least one entry's `loc` ends with that field's name (`"name"` or `"price"`).
  - For a body that is not a JSON object, at least one entry's `loc` is `["body"]`.
  - For a bad query parameter, at least one entry's `loc` ends with that parameter's name.
  - For a bad path id, at least one entry's `loc` ends with `"item_id"`.

## Acceptance criteria

### AC1: Create an item
`POST /items` with a valid body returns 201 and the new item: the `name` and `price` sent, and an integer `id`.
Verified by: TestClient tests, and one e2e test over real HTTP that creates an item and then reads it back
with `GET /items/{id}`.

### AC2: Create rejects invalid input with 422
`POST /items` returns 422 (with the error body from the interface contract) when:
- `name` is missing, is `""`, is longer than 100 characters, or is not a string (for example `123`);
- `price` is missing, is negative, or is not a number (for example `"abc"` or `null`);
- the body is not a JSON object (for example `[]`).
Nothing is stored after a rejected request.
Verified by: TestClient tests, one per case, checking the status, the body shape and the `loc` rule.

### AC3: Read one item
`GET /items/{id}` returns 200 and the item for an existing id. For an id that does not exist, it returns the
404 "not found" response.
Verified by: TestClient tests.

### AC4: Read with a non-integer id returns 422
`GET /items/abc` returns 422 with the error body from the interface contract (`loc` ends with `"item_id"`).
Verified by: TestClient test.

### AC5: Ids and separate storage
- In a new app, the first item created gets id 1 and each next item gets the next integer (1, 2, 3, ...).
- Two apps made by `create_app()` do not share items: an item created in one is not found in the other.
Verified by: TestClient tests.

### AC6: List items with pagination
`GET /items` returns 200 and `{"items": [...], "total": <int>, "offset": <int>, "limit": <int>}`.
- `items` is the stored items sorted by `id` ascending, from position `offset`, at most `limit` of them.
- `total` is the number of stored items. `offset` and `limit` echo the values used.
- Defaults: `offset` 0, `limit` 10.
- An `offset` at or past `total` gives `items: []` with the right `total`.
Verified by: TestClient tests (for example 25 items read as pages of 10, 10, 5).

### AC7: List rejects invalid pagination with 422
`GET /items` returns 422 (error body from the interface contract, `loc` ends with the parameter name) when
`offset` is negative, `limit` is less than 1, `limit` is more than 100, or either one is not an integer
(for example `limit=abc`).
Verified by: TestClient tests, one per case.

### AC8: Update an item
`PUT /items/{id}` with a valid body replaces that item's `name` and `price` and returns 200 and the updated
item with the same `id`. A later `GET /items/{id}` returns the updated item.
For an id that does not exist, it returns the 404 "not found" response and creates nothing.
`PUT /items/abc` returns 422 (`loc` ends with `"item_id"`).
Verified by: TestClient tests, and one e2e test over real HTTP that creates, updates and reads back an item.

### AC9: Update rejects invalid input with 422
`PUT /items/{id}` on an existing item returns 422 for every invalid body listed in AC2, and the stored item
stays unchanged.
Verified by: TestClient tests.

### AC10: Delete an item
`DELETE /items/{id}` on an existing item returns 204 with an empty body. After that:
- `GET /items/{id}` returns the 404 "not found" response;
- a second `DELETE /items/{id}` returns the 404 "not found" response;
- the next created item gets a new id, never the deleted one.
`DELETE /items/abc` returns 422 (`loc` ends with `"item_id"`).
Verified by: TestClient tests, and one e2e test over real HTTP that creates, deletes and then fails to read
an item.

## Non-functional

### NF1: In-memory storage only
Items live in the memory of the app object. No files, databases or network calls for storage. Items are
gone when the process restarts.

### NF2: No new dependencies
`requirements.txt` and `requirements-dev.txt` stay unchanged.

### NF3: Logic outside the routes
Storage and item logic live in a plain class in its own module (for example `ItemStore` in `items.py`),
created in `create_app()` and kept on `app.state`. Route functions only read the request, call that class
and shape the response (see AGENTS.md).

### NF4: Existing endpoints unchanged
`GET /health`, `GET /version` and `GET /time` return what they return today, and their existing tests pass
unchanged.

## Out of scope

Tests must not assert anything about these, in either direction:
- authentication, persistence, PATCH, filtering, searching, sorting options;
- numeric strings for `price` (such as `"1.5"`), booleans for `price`, whitespace-only names, and unknown
  extra fields in the body: each may be accepted or rejected;
- the exact text of `msg` and `type` in 422 entries;
- behavior under concurrent requests;
- the order of keys in JSON objects.
