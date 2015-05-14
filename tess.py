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

# Comments start with the pound sign
# They are used to give you a readable summary of what's going on.
10.32 10.234
10 50
60 50
10 50
60 50
20 30
<and so on>

The first triangle is the first three points. The second triangle is
defined by points four, five, and six. And so on.

"""

from OpenGL.GLU import *
from OpenGL.GL import *

import sys
import traceback

class ZoteTess:

    def __init__(self):
        self.tess_style = 0
        self.current_shape = []

    def make_triangles(self, flat_points_list):
        """
        Converts a list of points into a list of triangles.

        The input list is expected to have three points comprising a
        triangle in a row.

        The output is a list of lists. Each sub-list has three
        elements with the vertices of each triangle. The triangles
        are not guaranteed to be in a particular winding order, so if
        you need the triangles to all share the same surface normal
        you'll have to do additional math.

        """
        ret = []
        for i in range(0, len(flat_points_list), 3):
            ret.append([flat_points_list[0],
                        flat_points_list[1],
                        flat_points_list[2]])
        return ret
        
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
            self.current_shape.append(list(v[0:2]))
            
        def cb_begin(style):
            self.tess_style = style
                
        def cb_end():
            if self.tess_style == GL_TRIANGLE_FAN:
                c = self.current_shape.pop(0)
                p1 = self.current_shape.pop(0)
                while self.current_shape:
                    p2 = self.current_shape.pop(0)
                    triangles.extend([c, p1, p2])
                    p1 = p2
            elif self.tess_style == GL_TRIANGLE_STRIP:
                p1 = self.current_shape.pop(0)
                p2 = self.current_shape.pop(0)
                while self.current_shape:
                    p3 = self.current_shape.pop(0)
                    triangles.extend([p1, p2, p3])
                    p1 = p2
                    p2 = p3                
            elif self.tess_style == GL_TRIANGLES:
                triangles.extend(self.current_shape)
            else:
                print "Unknown tessellation style:", self.tess_style
            self.tess_style = None
            self.current_shape = []
        
                    
        def cb_error(what):
            print "error:", what
                        
        def cb_combine(c, v, weight):
            return (c[0], c[1], c[2])

        tess = gluNewTess()
        
        gluTessCallback(tess, GLU_TESS_VERTEX, cb_vert)
        gluTessCallback(tess, GLU_TESS_BEGIN, cb_begin)
        gluTessCallback(tess, GLU_TESS_END, cb_end)
        gluTessCallback(tess, GLU_TESS_ERROR, cb_error)
        gluTessCallback(tess, GLU_TESS_COMBINE, cb_combine)

        gluTessBeginPolygon(tess, None)
        for path in shape.paths:
            gluTessBeginContour(tess)
            for pt in path:
                gluTessVertex(tess, pt, pt)
            gluTessEndContour(tess)
        gluTessEndPolygon(tess)
        
        return triangles

class Shape(object):

    def __init__(self):
        self.paths = []

    def print_paths(self):
        for path in self.paths:
            for pt in path:
                print str(pt[0]) + ", " + str(pt[1])

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
        print t[0], t[1], t[2]
    print ""

def send_output(inputFile, outputFile, numPaths, flat_points, output):
    output.write("# " + inputFile + " --> " + outputFile + ": " +
                 str(numPaths) + " paths, " + str(len(flat_points) / 3) +
                 " triangles\n")
    for t in flat_points:
        output.write(str(t[0]) + " " + str(t[1]) + "\n")
        
def usage():
    print __doc__
    
if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            zt = ZoteTess()
            df = DiskFile(sys.argv[1])
            flat_points_list = zt.triangulate(df) # a single list of points
            # print_triangles("Disk file (test_data.dat)", response)
            if len(sys.argv) > 2:
                output = open(sys.argv[2], "w")
                fn = sys.argv[2]
            else:
                output = sys.stdout
                fn = "Standard Output"
            send_output(sys.argv[1], fn, len(df.paths), flat_points_list, output)
        except Exception, e:
            print(traceback.format_exc())
            print "Got exception while trying to read file", sys.argv[1]
            usage()
    else:
        usage()
