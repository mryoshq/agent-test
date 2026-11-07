from pydantic import BaseModel


class Item(BaseModel):
    id: int
    name: str
    price: float


class ItemPage(BaseModel):
    items: list[Item]
    total: int
    offset: int
    limit: int


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

    def list_items(self, offset: int = 0, limit: int = 10) -> ItemPage:
        item_ids = sorted(self._items)[offset : offset + limit]
        return ItemPage(
            items=[self._items[item_id] for item_id in item_ids],
            total=len(self._items),
            offset=offset,
            limit=limit,
        )
