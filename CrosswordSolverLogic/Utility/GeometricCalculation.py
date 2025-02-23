from ..Type import Point, Line, Triangle

import numpy as np
from shapely.geometry import Polygon

def distBetweenPoints(a: Point,b: Point) -> float:
    return np.sqrt(((b[0]-a[0]) ** 2) + ((b[1]-a[1]) ** 2))

def pointOnLine(lp1: Point, lp2: Point, p: Point) -> bool:
    left_side = (lp2[1] - lp1[1]) * (p[0] - lp1[0])
    right_side = (p[1] - lp1[1]) * (lp2[0] - lp1[0])
    return left_side == right_side

def pointDistToLine(lp1: Point, lp2: Point, p: Point) -> float:
    numerator  = abs((lp2[0] - lp1[0]) * (lp1[1] - p[1]) - (lp1[0] - p[0]) * (lp2[1] - lp1[1]))
    denominator = np.sqrt((lp2[0] - lp1[0]) ** 2 + (lp2[1] - lp1[1]) ** 2)
    return numerator / denominator

def crossProduct(a: Point, b: Point, p: Point) -> float:
    ab = np.array(b) - np.array(a)
    ap = np.array(p) - np.array(a)
    return ab[0] * ap[1] - ab[1] * ap[0]

def lineIntersection(line1: Line, line2: Line) -> Point | None:
    big = max(line1[0][0],line1[0][1],line1[1][0],line1[1][1],line2[0][0],line2[0][1],line2[1][0],line2[1][1])
    p1 = (float(line1[0][0]/big), float(line1[0][1]/big))
    p2 = (float(line1[1][0]/big), float(line1[1][1]/big))
    p3 = (float(line2[0][0]/big), float(line2[0][1]/big))
    p4 = (float(line2[1][0]/big), float(line2[1][1]/big))

    # Berechne den Schnittpunkt der beiden Linien, wenn er existiert
    a1, b1, c1 = _lineEquation(p1, p2)
    a2, b2, c2 = _lineEquation(p3, p4)

    # Berechne die Determinante der Koeffizientenmatrix
    det = a1 * b2 - a2 * b1

    # Wenn det == 0, sind die Linien parallel und schneiden sich nicht.
    if det == 0:
        return None
    # Berechne den Schnittpunkt (x, y)
    x = int(((b2 * c1 - b1 * c2) / det) * big)
    y = int(((a1 * c2 - a2 * c1) / det) * big)
    return (x, y)

def _lineEquation(p1: tuple[float,float], p2: tuple[float,float]) -> tuple[float,float,float]:
    # Berechne die Koeffizienten der linearen Gleichung Ax + By = C für die Linie, die durch p1 und p2 geht.
    x1, y1 = p1
    x2, y2 = p2
    a = y2 - y1
    b = x1 - x2
    c = a * x1 + b * y1
    return a, b, c

def polygonArea(points: list[Point]) -> float:
    if len(points) < 3:
        return 0
    area = 0
    for i in range(len(points)):
        j = (i + 1) % len(points)
        area += points[i][0] * points[j][1]
        area -= points[i][1] * points[j][0]
    area = abs(area) / 2
    return area

def centerOfTriangle(triangle: Triangle) -> Point:
    return (int(sum(x for x,y in triangle)/3),
            int(sum(y for x,y in triangle)/3))

def nonOverlapPolygonArea(points1: list[Point],points2: list[Point]) -> float:
    poly1 = Polygon(points1)
    poly2 = Polygon(points2)
    return (poly2-poly1).area + (poly1 - poly2).area
