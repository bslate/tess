#!/usr/bin/env python

"""Converts 2D polygon point geometry into triangles.

Usage:
  tess.py [input] [output]

The input file should be formatted like this:

10.34 10.234
10 50
60 50
60 10

20 30
25 40
30 30

40 30
45 20
50 30

Each line represents X and Y data for a point. Empty lines signify a
new path. Therefore this sample file contains three paths.

If the output file name is not given it spills to standard output. The
output will be formatted like this:

# test_data.dat --> Standard Output: 3 paths, 12 triangles
8 3 9 f f t
3 8 6 f f f
7 6 8 f f t
6 7 2 f f f
9 2 7 f f t
2 9 3 f f t
4 3 6 f f t
3 4 0 f f t
4 0 5 f f t
0 5 1 f f t
2 1 5 t f f
6 2 5 f f t

Each line has the format: idx0, idx1, idx2, edge0, edge1, edge2

The indexes refer to points in the order they appear in the input file.

The edges are true/false values. edge0 tells you if the line between
idx0 and idx1 is a shape boundary. edge1 is for idx1 to idx2, edge2 is
for idx2 to idx1.

"""

from OpenGL.GLU import *
from OpenGL.GL import *

import sys
import traceback

class ZoteTess:

    def __init__(self):
        self.tess_style = 0
        self.current_shape = []

    def triangulate(self, shape):
        """
        Converts a list of paths into a list of triangles.

        The input object should be a subclass of Shape. It has a
        'paths' member, which is a list of lists. Each sub-list is an
        individual path. The tessellation will determine if paths
        represent holes or disjoint shapes.

        """
        triangles = [] # store result
        self.current_shape = []

        #
        # Define several callback functions.
        #
        def cb_vert(v):
            self.current_shape.append(v)
            
        def cb_begin(style):
            self.tess_style = style
                
        def cb_end():
            if self.tess_style == GL_TRIANGLE_FAN:
                c = self.current_shape.pop(0)
                p1 = self.current_shape.pop(0)
                while self.current_shape:
                    p2 = self.current_shape.pop(0)
                    triangles.append([c, p1, p2])
                    p1 = p2
            elif self.tess_style == GL_TRIANGLE_STRIP:
                p1 = self.current_shape.pop(0)
                p2 = self.current_shape.pop(0)
                while self.current_shape:
                    p3 = self.current_shape.pop(0)
                    triangles.append([p1, p2, p3])
                    p1 = p2
                    p2 = p3
            elif self.tess_style == GL_TRIANGLES:
                # each three points constitute a triangle, no sharing
                while self.current_shape:
                    p1 = self.current_shape.pop(0)
                    p2 = self.current_shape.pop(0)
                    p3 = self.current_shape.pop(0)
                    triangles.append([p1, p2, p3])
            else:
                print "Unknown tessellation style:", self.tess_style
            self.tess_style = None
            self.current_shape = []
        
                    
        def cb_error(what):
            print "error:", what
                        
        def cb_combine(c, v, weight):
            print "combine:", c, v, weight, "(this will probably cause problems)"
            return (c[0], c[1], c[2])

        tess = gluNewTess()
        
        gluTessCallback(tess, GLU_TESS_VERTEX, cb_vert)
        gluTessCallback(tess, GLU_TESS_BEGIN, cb_begin)
        gluTessCallback(tess, GLU_TESS_END, cb_end)
        gluTessCallback(tess, GLU_TESS_ERROR, cb_error)
        gluTessCallback(tess, GLU_TESS_COMBINE, cb_combine)

        count = 0
        gluTessBeginPolygon(tess, None)
        for path in shape.paths:
            gluTessBeginContour(tess)
            for pt in path:
                gluTessVertex(tess, pt, count)
                count = count + 1
            gluTessEndContour(tess)
        gluTessEndPolygon(tess)

        tuples = shape.make_bound_tuples()
        flat = shape.flattened_points()
        ret = []
        for t in triangles:
            perhaps = Triangle(t, tuples, flat)
            if not perhaps.degenerate:
                ret.append(perhaps)
        return ret

def is_edge(a, b, bounds):
    """Returns true if a and b are adjacent within a single path."""
    span = find_bound_tuple(a, b, bounds)
    if span is not None:
        return is_adjacent(a, b, span)
    else:
        return False

def is_adjacent(a, b, span):
    ret = False
    lower = min(a, b)
    upper = max(a, b)
    diff = upper - lower
    if diff is 1:
        ret = True
    elif lower is span[0] and upper is span[1]:
        ret = True
    return ret

def find_bound_tuple(a, b, bounds):
    """If a and b are both included in a bounds tuple, return it.
    Otherwise return None.

    """
    def inside(num, spanish):
        return num >= spanish[0] and num <= spanish[1]
        
    for span in bounds:
        if inside(a, span) and inside(b, span):
            return span
    return None

def cross(a, b):
    return (a[0] * b[1]) - (a[1] * b[0])

def vec(start, end):
    return (end[0] - start[0], end[1] - start[1])

class Triangle(object):
    def __init__(self, tri, bounds, flattened_points):
        """Given three input indexes (e.g. 7, 3, 12) and a list of boundary
        tuples, create a triangle whose surface normal points the
        correct way and knows which edges are user-defined.

        Surface normal: the winding order of the points will on exit
        be defined such that it is in a right-handed coordinate
        system. Specifically: let vec1 run from p0 to p1, and vec2
        from p0 to p2. vec1 x vec2 is positive.

        Edges: Each edge of a triangle might be on the boundary of the
        shape, or it might be internal to the shape. An edge is True
        if it is on the boundary of the shape. We know it is on the
        boundary if the vertex indices are adjacent within a single
        path.

        Say we have an input paths list with indexes like this:
            [ [0, 1, 2, 3, 4], [5, 6, 7], [8, 9, 10] ]

        Use Shape's make_bound_tuples method to generate the list of
        tuples that looks like this: [ (0, 4), (5, 7), (8, 10) ], and
        pass that in as the 'bounds' parameter.
        
        Points 1 and 2 are adjacent (as are 2 and 1). Points 4 and 0
        are adjacent because lists are considered circular. Points 4
        and 5 are NOT adjacent because they come from different lists.

        With these path bounds and triangle verts at 6, 7, 9, the
        resulting triangle will have edges [True, False, False] since
        the first edge from 6 to 7 is a boundary, while the other two
        are not.

        """
        self.degenerate = False
        self.points = [None] * 3 # because that's easy to understand, right?
        self.points[0] = tri[0]
        self.points[1] = tri[1]
        self.points[2] = tri[2]
        self.edges = [None] * 3
        self.edges[0] = is_edge(tri[0], tri[1], bounds)
        self.edges[1] = is_edge(tri[1], tri[2], bounds)
        self.edges[2] = is_edge(tri[2], tri[0], bounds)
        # Ensure the winding order is correct. Cross product must be positive.
        # Swap things around if it is not.
        #
        # make vectors from 0 to 1 and 0 to 2
        v1 = vec(flattened_points[tri[0]], flattened_points[tri[1]])
        v2 = vec(flattened_points[tri[0]], flattened_points[tri[2]])
        c = cross(v1, v2)
        if abs(c) < 0.0001:
            self.degenerate = True
        elif (c < 0):
            # swap points 0 and 2
            tmpPt = self.points[0]
            self.points[0] = self.points[2]
            self.points[2] = tmpPt
            # swap edges 0 and 1
            tmpEdge = self.edges[0]
            self.edges[0] = self.edges[1]
            self.edges[1] = tmpEdge

    def __str__(self):
        def tf(b):
            if b:
                return "t"
            else:
                return "f"
            
        return str(self.points[0]) + " " + str(self.points[1]) + " " + str(self.points[2]) + " " + tf(self.edges[0]) + " " + tf(self.edges[1]) + " " + tf(self.edges[2])
        

class Shape(object):

    def __init__(self):
        self.paths = []

    def print_paths(self):
        for path in self.paths:
            for pt in path:
                print str(pt[0]) + ", " + str(pt[1])

    def make_bound_tuples(self):
        """Returns a list of tuples. Each has the lower and upper inclusive
        bounds of a path.

        Example input: [ [0, 1, 2, 3, 4], [5, 6, 7], [8, 9, 10] ]
        Example output: [ (0, 4), (5, 7), (8, 10) ]
        """
        ret = []
        low = 0
        for path in self.paths:
            high = low + len(path) - 1
            ret.append((low, high))
            low = high + 1
        return ret

    def flattened_points(self):
        ret = []
        for sublist in self.paths:
            for item in sublist:
                ret.append(item)
        return ret
    
class DiskFile(Shape):
    def __init__(self, file_name):
        super(DiskFile, self).__init__()
        try:
            infile = open(file_name)
        except:
            print "Could not open file:", file_name
            sys.exit()
        
        path = []
        for line in infile:
            try:
                if len(line) < 2:
                    self.paths.append(path)
                    path = []
                else:
                    tokens = line.split()
                    if len(tokens) is 2:
                        x = float(tokens[0])
                        y = float(tokens[1])
                        point = (x, y, 0)
                        path.append(point)
            except:
                print "Error reading line from", file_name
                print "Perhaps there's a syntax error?"
                sys.exit()
        self.paths.append(path)

def print_triangles(label, triangles):
    print label, "--", len(triangles), "triangles"
    print "-----------"
    print ""
    for t in triangles:
        print t
    print ""

def send_output(inputFile, outputFile, numPaths, triangles, output):
    output.write("# " + inputFile + " --> " + outputFile + ": " +
                 str(numPaths) + " paths, " + str(len(triangles)) +
                 " triangles\n")
    for t in triangles:
        output.write(str(t) + "\n")
        
def usage():
    print __doc__
    
if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            zt = ZoteTess()
            df = DiskFile(sys.argv[1])
            triangles = zt.triangulate(df) # list of Triangle objects
            if len(sys.argv) > 2:
                output = open(sys.argv[2], "w")
                fn = sys.argv[2]
            else:
                output = sys.stdout
                fn = "Standard Output"
            send_output(sys.argv[1], fn, len(df.paths), triangles, output)
        except Exception, e:
            print(traceback.format_exc())
            print "Got exception while trying to read file", sys.argv[1]
            # usage()
    else:
        usage()
