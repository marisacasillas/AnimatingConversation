#!/usr/bin/env python


def all_paths(rows, cols):
    points = [Point(i, j)
            for i in range(1, rows + 1)
            for j in range(1, cols + 1)]
    for n, p1 in enumerate(points):
        yield [p1]
        for p2 in points[n+1:]:
            path = find_path(p1, p2)
            yield path
            path.reverse()
            yield path


def find_path(p1, p2):
    di = 1 if p1.i < p2.i else -1
    dj = 1 if p1.j < p2.j else -1
    path = [p1]
    i, j = p1.i, p1.j
    while i != p2.i or j != p2.j:
        if i != p2.i:
            i += di
        if j != p2.j:
            j += dj
        path.append(Point(i, j))
    return path


class Point(object):

    def __init__(self, i, j):
        self.i, self.j = i, j


if __name__ == '__main__':
    main()
