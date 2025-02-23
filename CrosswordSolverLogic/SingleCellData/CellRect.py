from ..Utility import GeometricCalculation as GeomCalc
from ..Type import Point

import operator

class CellRect:

    def __init__(self, points):
        self._points = self._pointsToRect(points)

    def __getitem__(self, index) -> Point:
        return self._points[index]
    
    def __iter__(self):
        return iter(self._points)
    
    def __eq__(self, other):
        for i in range(4):
            if (self._points[i][0] != other._points[i][0] or
                self._points[i][1] != other._points[i][1]):
                return False
        return True
    
    def _pointsToRect(self,points: list[Point]) -> list[Point]:
        bridx, _ = max(enumerate([pt[0] + pt[1] for pt in points]), key=operator.itemgetter(1))
        tlidx, _ = min(enumerate([pt[0] + pt[1] for pt in points]), key=operator.itemgetter(1))
        blidx, _ = min(enumerate([pt[0] - pt[1] for pt in points]), key=operator.itemgetter(1))
        tridx, _ = max(enumerate([pt[0] - pt[1] for pt in points]), key=operator.itemgetter(1))
        return [points[tlidx],
                points[blidx],
                points[bridx],
                points[tridx]]

    def center(self) -> Point:
        xsum = sum(x for x, y in self._points)
        ysum = sum(y for x, y in self._points)
        return (int(xsum/4),int(ysum/4))
    
    def circumference(self) -> float:
        l1 = GeomCalc.distBetweenPoints(self._points[0],self._points[1])
        l2 = GeomCalc.distBetweenPoints(self._points[1],self._points[2])
        l3 = GeomCalc.distBetweenPoints(self._points[2],self._points[3])
        l4 = GeomCalc.distBetweenPoints(self._points[3],self._points[0])
        return (l1+l2+l3+l4)

    def meanSideLength(self) -> float:
        return self.circumference()/4
    
    def area(self) -> float:
        return GeomCalc.polygonArea(self._points)
    
    def isRhombus(self) -> bool:
        factor = 0.15
        l1 = GeomCalc.distBetweenPoints(self._points[0],self._points[1])
        l2 = GeomCalc.distBetweenPoints(self._points[1],self._points[2])
        l3 = GeomCalc.distBetweenPoints(self._points[2],self._points[3])
        l4 = GeomCalc.distBetweenPoints(self._points[3],self._points[0])
        mean = (l1+l2+l3+l4)/4
        if (l1 <= mean * (1+factor) and l1 >= mean * (1-factor)
            and l2 <= mean * (1+factor) and l2 >= mean * (1-factor)
            and l3 <= mean * (1+factor) and l3 >= mean * (1-factor)
            and l4 <= mean * (1+factor) and l4 >= mean * (1-factor)):
            return True
        return False
    
    def pointInside(self, point: Point) -> bool:
        rectarea = self.area()
        areas = 0
        for i in range(4):
            p1 = self._points[i]
            p2 = self._points[(i+1)%4]
            if GeomCalc.pointOnLine(p1,p2,point):
                continue
            a = GeomCalc.distBetweenPoints(p1,p2)
            b = GeomCalc.distBetweenPoints(p1,point)
            c = GeomCalc.distBetweenPoints(p2,point)
            s = (a + b + c) / 2
            areas += (s*(s-a)*(s-b)*(s-c)) ** 0.5
        if rectarea >= areas:
            return True
        return False

    _points: list[Point] = [] # [topleft,bottomleft,bottomright,topright]
