import enum

from sqlalchemy import Column, Integer, String, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import relationship

from .database import Base


class Level(str, enum.Enum):
    location = "location"
    department = "department"
    category = "category"
    subcategory = "subcategory"


class HierarchyNode(Base):
    """A single level of the Location > Department > Category > SubCategory tree.

    Modeled as a self-referencing adjacency list rather than four separate
    tables since it's a strict 4-level tree, and it gives every level the
    same CRUD surface.
    """

    __tablename__ = "hierarchy_nodes"
    __table_args__ = (UniqueConstraint("parent_id", "name", name="uq_parent_name"),)

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("hierarchy_nodes.id"), nullable=True, index=True)
    level = Column(Enum(Level), nullable=False)
    name = Column(String, nullable=False)

    parent = relationship("HierarchyNode", remote_side=[id], back_populates="children")
    children = relationship(
        "HierarchyNode", back_populates="parent", cascade="all, delete-orphan"
    )
