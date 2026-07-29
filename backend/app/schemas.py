from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from .models import Level


class NodeBase(BaseModel):
    level: Level
    name: str
    parent_id: Optional[int] = None


class NodeCreate(NodeBase):
    pass


class NodeUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[int] = None


class Node(NodeBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class NodeTree(Node):
    children: List["NodeTree"] = []


NodeTree.model_rebuild()
