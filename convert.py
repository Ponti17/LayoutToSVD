#! /usr/bin/python

"""
Cadence Layout to SVG Converter
Written by: Matthew Beckler (mbeckler@cmu.edu)

Website: For the latest version and more information, visit:
         http://www.mbeckler.org/cadence_plot/

Summary: This script will convert an ASCII stream dump of a Cadence Virtuoso
         Layout into an SVG file, suitable for opening with Inkscape. From
         Inkscape, it can be converted to a number of different formats,
         including GIF, JPG, PNG, and PDF.

How To:  First, you need to dump the layout from Cadence. From the ICFB window,
         go to "File" -> "Export" -> "Stream". Enter in the library, cell, and
         view name. Click the box next to "ASCII Dump", enter a filename for
         output, then click on "Options" near the top. In the options window,
         be sure to check the following options:
           "Convert PCells to Geometry"
           "Do not preserve pins"
           "Convert Paths to Polygons"
        Click "OK" in the options window, and click "OK" in the Stream Out
        window. Check to make sure that your file was created on disk. Let's 
        assume that the stream dump filename was "dump.txt".

        Next, run this script as "./convert.py dump.txt output.svg". If you
        only want to output a sub-cell of the total layout you dumped to disk,
        then you should add the desired sub-cell's name as the final argument
        to the script: "./convert.py dump.txt output.svg subcellname".

        Finally, once the SVG file has been created on disk, you should open it
        in Inkscape, and hit "Control + Shift + D" to open the Document 
        Properties dialog. Since the document bounding box is not set by this
        script, you should hit the "Fit page to selection" button to fix the 
        document borders. You should also change the document background from 
        100% transparent to 100% opaque. From here, you can Save As a PDF, 
        or use the export dialog "Control + Shift + E" to export a bitmap such 
        as a GIF or PNG. If you want to print in large format, saving as a PDF 
        will result in much better quality, as PDF is a vector format.

        Be warned that Inkscape (specifically the garbage collector it uses) 
        might have issues if you are trying to work with a very large SVG file.
        In my experience, these issues were not due to running out of RAM or
        swap, but due to a limitation with the GC system. You'll have better
        luck if you don't try to display all of the image in Inkscape, but save
        as PDF/PNG without looking at the entire document.
"""

import sys
import operator

"""
These are the layer color definitions. For each layer, you should define a 
color for the polygon fill, the opacity of the fill, and a color for the 
polygon's border. The layer numbers were determined experimentally, and you
may need to add more layer definitions if your design uses different/more 
layers. For instance, our designs didn't go past Metal4, so there are no
definitions for metal layers 5 and above. Colors should be specified as a
six-digit hex code (like HTML), and opacity should be either 0.0 - 1.0 or
1 - 255.
"""
layer_colors = {} #("fg color", "fg opacity", "stroke color")
# layer_colors[1] =  ("e71f0d",   "0.5",        "e71f0d"      ) # Oxide
# layer_colors[2] =  ("9900e6",   "0.1",        "9900e6"      ) # Nwell
# layer_colors[3] =  ("01fe00",   "0.3",        "01fe00"      ) # poly
# layer_colors[4] =  ("ffff00",   "0.2",        "ffff00"      ) # Nimp
# layer_colors[5] =  ("bf4026",   "0.1",        "bf4026"      ) # Pimp
# layer_colors[6] =  ("ffffff",   "1.0",        "000000"      ) # Contact
# layer_colors[7] =  ("0000ff",   "0.3",        "0000ff"      ) # M1
# layer_colors[8] =  ("39bfff",   "1.0",        "38bfff"      ) # Via1-2
# layer_colors[9] =  ("ff0000",   "0.3",        "ff0000"      ) # M2
# layer_colors[10] = ("ff8000",   "1.0",        "ff8000"      ) # Via2-3
# layer_colors[11] = ("01cc66",   "0.3",        "01cc66"      ) # M3
# layer_colors[30] = ("9900e6",   "1.0",        "9900e6"      ) # Via3-4
# layer_colors[31] = ("ffbff2",   "0.3",        "ffbff2"      ) # M4
# layer_colors[62] = ("ff00ff",   "0.0",        "ff00ff"      ) # prBndry
# layer_colors[85] = ("bf4026",   "0.0",        "bf4026"      ) # PWdummy

layer_colors[3]   =  ("9900e6",   "0.1",        "9900e6"      ) # NW
layer_colors[6]   =  ("e71f0d",   "0.5",        "e71f0d"      ) # OD
layer_colors[17]  =  ("01fe00",   "0.3",        "01fe00"      ) # PO
layer_colors[18]  =  ("01fe00",   "0.0",        "01fe00"      ) # ??
layer_colors[25]  =  ("01fe00",   "0.0",        "01fe00"      ) # PP
layer_colors[26]  =  ("01fe00",   "0.0",        "01fe00"      ) # ??
layer_colors[30]  =  ("ffffff",   "1.0",        "ffffff"      ) # CO
layer_colors[31]  =  ("0000ff",   "0.3",        "0000ff"      ) # M1
layer_colors[32]  =  ("ff0000",   "0.3",        "ff0000"      ) # M2
layer_colors[33]  =  ("01cc66",   "0.3",        "01cc66"      ) # M3
layer_colors[34]  =  ("ffbff2",   "0.3",        "ffbff2"      ) # M4
layer_colors[35]  =  ("01fe00",   "0.0",        "01fe00"      ) # M5
layer_colors[36]  =  ("01fe00",   "0.0",        "01fe00"      ) # M6
layer_colors[37]  =  ("01fe00",   "0.0",        "01fe00"      ) # M7
layer_colors[38]  =  ("01fe00",   "0.0",        "01fe00"      ) # M8
layer_colors[57]  =  ("01fe00",   "0.0",        "01fe00"      ) # VIA7
layer_colors[75]  =  ("01fe00",   "0.0",        "01fe00"      ) # PDK
layer_colors[77]  =  ("01fe00",   "0.0",        "01fe00"      ) # CTM
layer_colors[88]  =  ("01fe00",   "0.0",        "01fe00"      ) # DMEXCL
layer_colors[131] =  ("01fe00",   "0.0",        "01fe00"      ) # M1 Pin
layer_colors[132] =  ("01fe00",   "0.0",        "01fe00"      ) # M2 Pin
layer_colors[133] =  ("01fe00",   "0.0",        "01fe00"      ) # M3 Pin
layer_colors[148] =  ("01fe00",   "0.0",        "01fe00"      ) # CTMDMY
layer_colors[149] =  ("01fe00",   "0.0",        "01fe00"      ) # PO Pin
layer_colors[150] =  ("bf4026",   "0.0",        "bf4026"      ) # CBM

# We keep track of all the undefined_layers so we can tell the user at the end of execution.
undefined_layers = set()

"""
Plain SVG documents do not include any layering capabilities, as far as I know.
Based on some experiments, it seemed that items are rendered from the top down,
so putting the lower layers first seems to produce a more accurate drawing.
We first put all our polygons into this list, as a tuple of (layer, string), so
that we can sort the polygons by layer, and write them from lowest layer to
highest layer before writing them to the SVG file.
"""
to_write = []

# Each object needs to have a unique id, so we keep this global variable.
object_id = 0

"""
There are two types of objects: Polygons, and Containers.
They both inherit from Cell, which defines the print_me function.
"""
class Cell:
    """ this function prints the cell and all children """
    def print_me(self, x, y, angle, mirror):
        pass

"""
The Container class stores a list of its children, along with their relative
position, rotation, and mirroring property. When a Container is asked to print
itself at a certain position, rotation, and mirroring, it simply computes each
child's updated position, and asks the child to print itself. Notice that the 
angle for each child is computed as the Container's rotation plus the child's
relative rotation, mod 360 degrees. The mirroring property is similarly defined
but since it is a boolean flag, the XOR (^) is used instead: basically, the 
child should be mirrored only if either the parent is mirrored, or the child is
mirrored, but not if both parent and child are mirrored.
"""
class Container(Cell):
    def __init__(self):
        self.children = []

    def add(self, obj, x, y, angle, mirror):
        """ adds the object as a child with relative offset (x,y) """
         # we make a tuple to put in the list
        self.children.append( (obj, x, y, angle, mirror) )

    def print_me(self, x, y, angle, mirror):
        # go through each child component and have them print themselves:
        for c in self.children:
            # first, compute the child's new origin
            c_x, c_y = rot_mirror_and_offset(c[1], c[2], angle, mirror, x, y)
            c[0].print_me(c_x, c_y, (c[3] + angle) % 360, c[4] ^ mirror)

"""
A Polygon is the base geometric object. Rectangles in the ASCII dump stream are
converted to 5-point polygons for simplicity. Polygon objects keep their list
of points (scaled down by dividing by 10), as well as their layer, which is
used to find the color. This class uses rot_mirror_and_offset to compute the
new locations of its points based on the information the parent sends in.
"""
class Polygon(Cell):
    """ this object reprsents a polygon """
    
    def __init__(self, points, layer):
        global object_id, layer_colors
        self.points = []
        for p in points:
            self.points.append( (p[0] / 10, p[1] / 10) )
        self.layer = layer
        # self.id is used as the unique SVG id
        self.id = "path" + str(object_id)
        object_id += 1

    def print_me(self, x, y, angle, mirror):
        """ Prints this polygon, offset by x,y """
        if self.layer in layer_colors:
            color_info = layer_colors.get(self.layer)
        else:
            # the layer does not exist
            print("WARNING!")
            print("  This input file uses a layer (" + str(self.layer) + ") that is not defined!")
            print("  The objects in this layer will be drawn as black boxes.")
            print("  To fix this, simply add a new line to the source file for the new layer.")
            print("  Please look in the source around line 60.")
            undefined_layers.add(self.layer)
            color_info = ("000000", "0.8", "000000")
        style = "fill:#" + color_info[0] + ";fill-opacity:" + color_info[1] + ";stroke:#" + color_info[2] + ";stroke-width:2;stroke-linecap:round;stroke-linejoin:round;stroke-miterlimit:4;stroke-dasharray:none;stroke-dashoffset:0;stroke-opacity:1"
        
        path = "M"
        first = True
        for p in self.points:
            if first == False:
                path += " L"
            
            my_x, my_y = rot_mirror_and_offset(p[0], p[1], angle, mirror, x, y)
        
            # because inkscape uses graphics coordinates:
            my_y = -my_y
        
            path += " " + str(my_x) + "," + str(my_y);
            first = False
            
        path += " z"

        to_write.append( (self.layer, '    <path\n       d="' + path + '"\n       id="' + self.id + '"\n       style="' + style + '" />\n') )

"""
Takes the original object's coordinates (obj_x and obj_y), applies a rotation
of "angle" degrees (CCW), applies the mirroring across the X-axis if specified,
and adds in the position offset (off_x and off_y). This function does not take
into account the different in y-axis coordinate systems between Cadence (math)
and Inkscape (graphics).
"""
def rot_mirror_and_offset(obj_x, obj_y, angle, mirror, off_x, off_y):
    if angle == 90:
        my_x = -obj_y
        my_y = obj_x
    elif angle == 180:
        my_x = -obj_x
        my_y = -obj_y
    elif angle == 270:
        my_x = obj_y
        my_y = -obj_x
    else: # angle == 0
        my_x = obj_x
        my_y = obj_y               
    
    if mirror:
        my_y = -my_y
        
    my_x += off_x
    my_y += off_y
    
    return my_x, my_y
    
"""
Once we have read in the entire file, and have populated our data structures
with all the geometry data, we sort the "to_write" list to produce the proper
layering in the SVG (see explanation above), and write each line to the file.
"""
def dump_to_write_to_file(output_file):
    global to_write
    # first we sort the items:
    to_write = sorted(to_write, key=operator.itemgetter(0))
    for x in to_write:
        output_file.write(x[1] + "\n")

"""
Produces a standard, plain vanilla SVG header. The width and height aren't
really that useful, as we can't compute the bounding box in this script without
a lot of work, and you can use Inkscape to reset the bounding box to contain
every object with a single button click.
"""
def make_svg_header(output_file, width, height):
    output_file.write("<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?>\n")
    output_file.write("<!-- Created with Inkscape (http://www.inkscape.org/) -->\n")
    output_file.write("<svg\n")
    output_file.write("   xmlns:svg=\"http://www.w3.org/2000/svg\"\n")
    output_file.write("   xmlns=\"http://www.w3.org/2000/svg\"\n")
    output_file.write("   version=\"1.0\"\n")
    output_file.write('   width="%d"\n' % width)
    output_file.write('   height="%d"\n' % height)
    output_file.write("   id=\"svg2\">\n")
    output_file.write("  <defs\n")
    output_file.write("     id=\"defs4\" />\n")

# Close up the <svg> tag
def make_svg_footer(output_file):
    output_file.write("</svg>\n")

# Begin main code
if len(sys.argv) < 3:
    sys.exit("Usage: %s input_file output_file" % sys.argv[0])
    
input_file = open(sys.argv[1], 'r')
output_file = open(sys.argv[2], 'w')
make_svg_header(output_file, 100, 100)

cells = {} # this will store our cells, lookup by name

# This variable stores the cell we are currently parsing
# Newly parsed polygons will be added to this object
currentCell = 0

line = input_file.readline()
while line != '':
    if line.startswith("Cell Name"):
        # defining a new cell type
        things = line.split()
        currentCell = Container()
        name = things[3].strip(',')
        cells[name] = currentCell
        # Now, currentCell is the currently open cell,
        # and any subsequently parsed pieces will be added to this cell.
    elif line.startswith("Cell Instance"):
        # instantiating an object
        name = line.split()[6]
        line = input_file.readline()
        things = line.split()
        coord = things[2].strip('()').split(",")
        x = int(coord[0])/10
        y = int(coord[1])/10
        angle = float(things[5])
        mirror = bool(int(things[8]))
        c = cells[name]
        currentCell.add(c, x, y, angle, mirror)
    elif line.startswith("End Cell Definition"):
        pass # nothing to do here
    elif line.startswith("Rectangle"):
        things = line.split()
        layer = int(things[4])
        coord = things[11].strip('()').split(",")
        x1 = int(coord[0])
        y1 = int(coord[1])
        coord = things[12].strip('()').split(",")
        x2 = int(coord[0])
        y2 = int(coord[1])
        # to save code, we just make this rectangle into a polygon
        points = []
        points.append( (x1, y1) )
        points.append( (x1, y2) )
        points.append( (x2, y2) )
        points.append( (x2, y1) )
        points.append( (x1, y1) )
        p = Polygon(points, layer)
        currentCell.add(p, 0, 0, 0, 0)
        # the polygon is already handling it's own offset, so we leave x=0, y=0
    elif line.startswith("Polygon"):
        things = line.split()
        layer = int(things[4])
        numPoints = int(things[13])
        points = []
        numPointsLeft = numPoints
        while True:
            line = input_file.readline()
            things = line.split()
                
            if numPointsLeft >= 4:
                coord = things[0].strip('()').split(",")
                points.append( (int(coord[0]), int(coord[1])) )
                coord = things[1].strip('()').split(",")
                points.append( (int(coord[0]), int(coord[1])) )
                coord = things[2].strip('()').split(",")
                points.append( (int(coord[0]), int(coord[1])) )
                coord = things[3].strip('()').split(",")
                points.append( (int(coord[0]), int(coord[1])) )
                numPointsLeft -= 4
            elif numPointsLeft == 3:
                coord = things[0].strip('()').split(",")
                points.append( (int(coord[0]), int(coord[1])) )
                coord = things[1].strip('()').split(",")
                points.append( (int(coord[0]), int(coord[1])) )
                coord = things[2].strip('()').split(",")
                points.append( (int(coord[0]), int(coord[1])) )
                numPointsLeft -= 3
            elif numPointsLeft == 2:
                coord = things[0].strip('()').split(",")
                points.append( (int(coord[0]), int(coord[1])) )
                coord = things[1].strip('()').split(",")
                points.append( (int(coord[0]), int(coord[1])) )
                numPointsLeft -= 2
            elif numPointsLeft == 1:
                coord = things[0].strip('()').split(",")
                points.append( (int(coord[0]), int(coord[1])) )
                numPointsLeft -= 1

            if numPointsLeft == 0:
                break
        
        p = Polygon(points, layer)
        currentCell.add(p, 0, 0, 0, 0)
        # the polygon is already handling it's own offset, so we leave x=0, y=0
    
    line = input_file.readline()

if len(sys.argv) == 4:
    # the user specified a cell to print out
    cells[sys.argv[3]].print_me(0, 0, 0, 0)
else:
    # the last cell defined should be the top-level cell
    currentCell.print_me(0, 0, 0, 0)

# now that we have printed our polygons to the list, we write them to the file
dump_to_write_to_file(output_file)

print("Finished writing " + str(len(to_write)) + " polygons to file.")
if len(undefined_layers) > 0:
    print("There were %d undefined layers: %s" % (len(undefined_layers), list(undefined_layers)))

make_svg_footer(output_file)
output_file.close()
input_file.close()
