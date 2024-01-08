from typing import List
from pydantic import BaseModel, ConfigDict, RootModel


class BaseORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class BaseListModel(RootModel):
    root: List[BaseORMModel]

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]
