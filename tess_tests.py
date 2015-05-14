#!/usr/bin/env python

from tess import *

class Square (Shape):

    def __init__(self):
        super(Square, self).__init__()
        a = (10, 10, 0)
        b = (20, 10, 0)
        c = (20, 20, 0)
        d = (10, 20, 0)
        self.paths.append([a, b, c, d]) # append a list

class Concave (Shape):
    def __init__(self):
        super(Concave, self).__init__()
        a = (20, 15, 0)
        b = (20, 5, 0)
        c = (10, 25, 0)
        d = (30, 25, 0)
        self.paths.append([a, c, b, d]) # note order is not alphabetical

class TetrisT (Shape):
    def __init__(self):
        super(TetrisT, self).__init__()
        # the first point is bottom left and goes clockwise from there
        self.paths.append([
            (-225.396225, -36.19598, 0),
            (-229.254745, -16.5716381, 0),
            (-209.6308, -12.7113495, 0),
            (-213.489441, 6.912962, 0),
            (-193.863342, 10.762394, 0),
            (-190.0048, -8.861887, 0),
            (-170.38089, -5.00150061, 0),
            (-166.522415, -24.62577, 0)
            ])

class SquareWithTriangleHoles(Shape):
    def __init__(self):
        super(SquareWithTriangleHoles, self).__init__()
        # square is abcd
        a = (10, 10, 0)
        b = (10, 50, 0)
        c = (60, 50, 0)
        d = (60, 10, 0)
        self.paths.append([a, b, c, d])
        # upward pointing triangle is efg
        e = (20, 30, 0)
        f = (25, 40, 0)
        g = (30, 30, 0)
        self.paths.append([e, f, g])
        # downward pointing triangle is hij
        h = (40, 30, 0)
        i = (45, 20, 0)
        j = (50, 30, 0)
        self.paths.append([h, i, j])

def main():    
    zt = ZoteTess()

    response = zt.triangulate(Square())
    print_triangles("Square", response)
    response = zt.triangulate(Concave())
    print_triangles("Concave", response)
    response = zt.triangulate(TetrisT())
    print_triangles("TetrisT", response)
    square_with_holes = SquareWithTriangleHoles()
    response = zt.triangulate(square_with_holes)
    print_triangles("Square With Triangle Holes", response)
            
    # print "Original data for square with triangle holes:"
    # square_with_holes.print_paths()

    df = DiskFile("test_data.dat")
    response = zt.triangulate(df)
    print_triangles("Disk file (test_data.dat)", response)

if __name__ == "__main__":
    main()
