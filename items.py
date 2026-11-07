from pydantic import BaseModel


class Item(BaseModel):
    id: int
    name: str
    price: float


class ItemStore:
    def __init__(self) -> None:
        self._items: dict[int, Item] = {}
        self._next_id = 1

    def create(self, name: str, price: float) -> Item:
        item = Item(id=self._next_id, name=name, price=price)
        self._items[self._next_id] = item
        self._next_id += 1
        return item

    def get(self, item_id: int) -> Item | None:
        return self._items.get(item_id)
