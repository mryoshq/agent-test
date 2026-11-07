from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from items import Item, ItemPage, ItemStore


class ItemRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: float = Field(ge=0)


def create_app() -> FastAPI:
    app = FastAPI()
    app.state.item_store = ItemStore()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/version")
    def version() -> dict[str, str]:
        return {"version": "0.1.0"}

    @app.get("/time")
    def time() -> dict[str, str]:
        return {"time": datetime.now(timezone.utc).isoformat()}

    @app.post("/items", status_code=201, response_model=Item)
    def create_item(request: ItemRequest) -> Item:
        return app.state.item_store.create(request.name, request.price)

    @app.get("/items", response_model=ItemPage)
    def list_items(
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=10, ge=1, le=100),
    ) -> ItemPage:
        return app.state.item_store.list_items(offset, limit)

    @app.get("/items/{item_id}", response_model=Item)
    def read_item(item_id: int) -> Item:
        item = app.state.item_store.get(item_id)
        if item is None:
            raise HTTPException(status_code=404, detail="Item not found")
        return item

    @app.put("/items/{item_id}", response_model=Item)
    def update_item(item_id: int, request: ItemRequest) -> Item:
        item = app.state.item_store.update(item_id, request.name, request.price)
        if item is None:
            raise HTTPException(status_code=404, detail="Item not found")
        return item

    return app


app = create_app()
