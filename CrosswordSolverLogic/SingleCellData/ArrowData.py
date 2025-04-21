from ..Type import Point

class ArrowData:
    def __init__(self, origin: Point, direction: Point, position: float):
        self.origin = origin
        self.direction = direction
        self.position = position
