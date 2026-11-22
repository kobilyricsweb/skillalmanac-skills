"""Sample shapes for the class diagram smoke test."""
from abc import ABC, abstractmethod
from typing import List, Optional


class Shape(ABC):
    name: str = "shape"

    def __init__(self, name: str) -> None:
        self.label: str = name

    @abstractmethod
    def area(self) -> float:
        ...

    @staticmethod
    def unit() -> str:
        return "cm"


class Canvas:
    shapes: List[Shape]
    _focus: Optional[Shape]

    def add(self, shape: Shape) -> None:
        self.shapes.append(shape)
