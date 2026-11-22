"""Second sample file: a subclass of a class defined in geometry.py."""
from geometry import Shape


class Circle(Shape):
    radius: float

    def __init__(self, radius: float) -> None:
        self.radius: float = radius
        self.__id: int = 0

    def area(self) -> float:
        return 3.14159 * self.radius ** 2
