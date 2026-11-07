from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from items import Item, ItemStore


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

    @app.get("/items/{item_id}", response_model=Item)
    def read_item(item_id: int) -> Item:
        item = app.state.item_store.get(item_id)
        if item is None:
            raise HTTPException(status_code=404, detail="Item not found")
        return item

    return app


app = create_app()
