#!/usr/bin/env python
"""wxPython Panel viewing an OSM map plus points and bounding boxes."""

__author__ = "P. Tute, B. Henne"
__contact__ = "henne@dcsec.uni-hannover.de"
__copyright__ = "(c) 2012, DCSec, Leibniz Universitaet Hannover, Germany"
__license__ = "GPLv3"

import os
import platform
import wx
import asyncore
from lib import tilenames as tiles
from lib.tileloader import TileLoader
from lib import calculations as calc

TILE_SIZE = 256 # px
POINT_SIZE = 3
RECTANGLE_FILL = True
# Alpha is kind of broken in Windows, do not use filled rectangles
if platform.system() == 'Windows':
    RECTANGLE_FILL = False
RECTANGLE_LINE_WIDTH = 2
RECTANGLE_FILL_ALPHA = 30 # 0-255

class MapPanel(wx.Panel):
    """Basic wx.Panel for viewing an OSM map.
    
    Panel shows map tiles and optional markers and bounding boxes.
    
    @author: B. Henne
    @author: P. Tute
    
    """

    def __init__(self, parent, cachedir='.cache', *args, **kwargs):
        """Init the MapPanel.
        
        @param cachedir: directory to store downloaded OSM tiles
        
        """
        wx.Panel.__init__(self, parent, *args, **kwargs)
        self.SetBackgroundColour("Light Grey")
        self.cache_dir = cachedir
        try:
            os.mkdir(self.cache_dir)
            print 'No cache folder found. Creating it.'
        except OSError:
            print 'Found cache folder.'
        self.placeholder = wx.EmptyImage(*self.Parent.GetSize())
        self.placeholder.ConvertColourToAlpha(0, 0, 0)
        self.placeholder = self.placeholder.ConvertToBitmap()
        self.tiles = {}
        self.tiles_used = {}
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self._center_lat = 52.382463
        self._center_lon = 9.717836
        self._center_x = 0
        self._center_y = 0
        self.rel_pos_x = 0
        self.rel_pos_y = 0
        self._zoom = 17
        self.create_map()
        self._distance_x = 0
        self._distance_y = 0
        self.calc_geotilesize()
        self.points = []
        self.point_colours = []
        self.rectangles = []
        self.rectangle_colours = []
        self.greyedOverlay = None    #: tuple [rga value, alpha]
        self.current_point = 0
        self.current_rectangle = 0
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.async_timer = wx.PyTimer(self.async_loop)
        self.async_timer.Start(500, False)

    def async_loop(self):
        """Iterate through all open syncore sockets.
        
        This has to be a method so it can be scheduled. It has no other use.

        """
        if asyncore.socket_map:
            asyncore.loop(count=1)
            self.Refresh()

    def OnKeyDown(self, e):
        keycode = e.GetKeyCode()
        print keycode
        if keycode == 43:
            # +: zoom in
            self.set_zoom(self.get_zoom() + 1)
            self.Refresh()
        elif keycode == 45:
            # -: zoom out
            self.set_zoom(self.get_zoom() - 1)
            self.Refresh()
        elif keycode == 80:
            # p: walk through points
            if len(self.points) > 0:
                self.current_point = (self.current_point + 1) % len(self.points)
                self.center = self.points[self.current_point]
                self.Refresh()
        elif keycode == 82:
            # r: walk through rectangles
            if len(self.rectangles) > 0:
                self.current_rectangle = (self.current_rectangle + 1) % len(self.rectangles)
                r = self.rectangles[self.current_rectangle]
                self.center = (r[0] + (r[2] - r[0]) / 2, r[1] + (r[3] - r[1]) / 2)
                self.Refresh()
        elif (keycode == wx.WXK_UP) or (keycode == wx.WXK_NUMPAD_UP):
            lat, lon = self.center
            self.center = (lat+self._distance_y/2, lon)
            self.Refresh()
        elif (keycode == wx.WXK_DOWN) or (keycode == wx.WXK_NUMPAD_DOWN):
            lat, lon = self.center
            self.center = (lat-self._distance_y/2, lon)
            self.Refresh()
        elif (keycode == wx.WXK_LEFT) or (keycode == wx.WXK_NUMPAD_LEFT):
            lat, lon = self.center
            self.center = (lat, lon-self._distance_x/2)
            self.Refresh()
        elif (keycode == wx.WXK_RIGHT) or (keycode == wx.WXK_NUMPAD_RIGHT):
            lat, lon = self.center
            self.center = (lat, lon+self._distance_x/2)
            self.Refresh()
        elif keycode == 49:
            self.zoom = 11
            self.Refresh()
        elif keycode == 50:
            self.zoom = 12
            self.Refresh()
        elif keycode == 51:
            self.zoom = 13
            self.Refresh()
        elif keycode == 52:
            self.zoom = 14
            self.Refresh()
        elif keycode == 53:
            self.zoom = 15
            self.Refresh()
        elif keycode == 54:
            self.zoom = 16
            self.Refresh()
        elif keycode == 55:
            self.zoom = 17
            self.Refresh()
        elif keycode == 56:
            self.zoom = 18
            self.Refresh()
        e.Skip()
    
    def OnPaint(self, Event):
        dc = wx.AutoBufferedPaintDCFactory(self)
        dc.Clear()
        size = self.GetSize()
        for coord in self.tiles_used:
            image = self.tiles[self.tiles_used[coord]]
            x = coord[0]
            y = coord[1]
            dc.DrawBitmap(image,
                          x * TILE_SIZE - self.rel_pos_x + size[0] / 2 - TILE_SIZE / 2, # substract half panel size to center on middle of tile...
                          y * TILE_SIZE - self.rel_pos_y + size[1] / 2 - TILE_SIZE / 2)
        # wx.GCDC for alpha channel support; map is drawn without alpha support to work in Windows...
        dc = wx.GCDC(dc)
        if self.points:
            self.draw_point_list(dc, self.points, self.point_colours)
        if self.rectangles:
            self.draw_rectangle_list(dc, self.rectangles, self.rectangle_colours)
        if self.greyedOverlay is not None:
            dc.DrawBitmap(wx.EmptyBitmapRGBA(size[0], size[1], 
                                             self.greyedOverlay[0], self.greyedOverlay[0], self.greyedOverlay[0], 
                                             self.greyedOverlay[1]), 
                          0, 0)
        del dc
        
    def OnSize(self, event):
        self.set_center((self._center_lat, self._center_lon))
        self.create_map()
        self.Refresh()

    def get_zoom(self):
        return self._zoom

    def set_zoom(self, zoom):
        self._zoom = min(max(0, zoom), 18) # 0 <= zoom <= 18
        self.create_map()
        self.calc_geotilesize()

    zoom = property(get_zoom, set_zoom)

    def get_lat(self):
        return self._center_lat

    def set_lat(self, lat):
        self._center_lat = min(max(-90, lat), 90) # -90 <= lat <= 90
        self.create_map()

    lat = property(get_lat, set_lat)

    def get_lon(self):
        return self._center_lon

    def set_lon(self, lon):
        self._center_lon = min(max(-180, lat), 180) # -180 <= lat <= 180
        self.create_map()

    lon = property(get_lon, set_lon)

    def get_center(self):
        return [self._center_lat, self._center_lon]

    def set_center(self, coords):
        self._center_lat = min(max(-90, coords[0]), 90) # -90 <= lat <= 90
        self._center_lon = min(max(-180, coords[1]), 180) # -180 <= lat <= 180
        self.create_map()

    center = property(get_center, set_center)
    
    def calc_geotilesize(self):
        """Calculates geographical size of a tile at current zoom."""
        s, w, n, e = tiles.tileEdges(self._center_x, self._center_y, self._zoom)
        self._distance_x = abs(w - e)
        self._distance_y = abs(n - s)
        
    def create_map(self):
        """Calculate all necessary coordinates and values, and get the right images."""
        # calculate tile number and borders of the tile in lat/lon
        self._center_x_float, self._center_y_float = calc.deg2num(self._center_lat, self._center_lon, self._zoom)
        self._center_x = int(self._center_x_float)
        self._center_y = int(self._center_y_float)
        # calculate offset needed for centering on the desired coordinates. 
        # Half of TILE_SIZE is substracted because when drawing we center on the middle of the tile.
        self.rel_pos_x = TILE_SIZE * (self._center_x_float - self._center_x) - TILE_SIZE / 2
        self.rel_pos_y = TILE_SIZE * (self._center_y_float - self._center_y) - TILE_SIZE / 2
        # determine, how many tiles are necessary around the center one...
        # this should be the tiles needed to fill the screen +1 to avoid borders
        width, height = self.GetSize()
        self.number_of_tiles = ((max(width, height) / TILE_SIZE) / 2) + 1
        # and load the tiles
        for y in xrange(-self.number_of_tiles, self.number_of_tiles + 1):
            for x in xrange(-self.number_of_tiles, self.number_of_tiles + 1):
                # absolute osm-values
                absolute_x = self._center_x + x
                absolute_y = self._center_y + y
                if (absolute_x, absolute_y, self.zoom) not in self.tiles:
                    # image is not in memory...load it
                    self.get_image(absolute_x, absolute_y, self.zoom)
                # add tile to the tiles that will be drawn...
                # (0, 0) is our center tile and will be in the middle of the panel
                self.tiles_used[(x, y)] = (absolute_x, absolute_y, self.zoom)

    def get_image(self, x, y, z, layer='mapnik'):
        """Load an image from the cache folder or download it.

        Try to load from cache-folder first, download and cache if no image was found.
        The image is placed in self.tiles by this method or by the TileLoader after downloading.

        @param x: OSM-tile number in x-direction
        @type x: int
        @param y: OSM-tile number in y-direction
        @type y: int
        @param z: OSM-zoom
        @type z: int in range [0, 18]
        @param layer: The used map layer (default 'mapnik')
        @type layer: string (one of 'tah', 'oam' and 'mapnik')
        
        """
        url = tiles.tileURL(x, y, z, layer)
        parts = url.split('/')[-4:]

        if not os.path.exists(os.path.join(self.cache_dir, *parts)):
            # Image is not cached yet. Create necessary folders and download image.
            tl = TileLoader(self, x, y, z, layer)
            #asyncore.loop(count=1)
            asyncore.loop(count=1)
            return
        image = wx.EmptyBitmap(1, 1)     # Create a bitmap container object. The size values are dummies.
        image.LoadFile(os.path.join(self.cache_dir, *parts), wx.BITMAP_TYPE_ANY)   # Load it with a file image.
        self.tiles[(x, y, z)] = image

    def draw_point(self, dc, lat, lon, wx_colour):
        """Draw a single point.

        @param dc: a wx.DC that will be used for drawing.
        @type dc: wx.DC
        @param lat: latitude of the point to be drawn on the map
        @param lon: longitude of the point to be drawn on the map
        @param wx_colour: the colour of the point
        @type wx_colour: wx colour, e. g. wx.RED

        """
        x, y = calc.latlon_to_xy(lat, lon, self.zoom, self)
        dc.SetPen(wx.Pen(wx_colour, 2))
        dc.DrawRectangle(x - POINT_SIZE / 2 + 1 - self.rel_pos_x,
                         y - POINT_SIZE / 2 + 1 - self.rel_pos_y,
                         POINT_SIZE, POINT_SIZE)

    def draw_rectangle_list(self, dc, rectangles, wx_colours):
        """Draw a list of rectangles all at once.

        @param dc: a wx.DC that will be used for drawing.
        @type dc: wx.DC
        @param coords: a list containing (lat, lon, lat, lon) sequences representing top left and bottom right corner of each rectangle.
        @param wx_colours: a list of at least as many colours as there are rectangles.
        @type wx_colours: iterable containing wx colours, e. g. wx.RED
        @param filled: if this is True, all rectangles will be drawn with an (not completely opaque) filling.
        
        """
        rects = []
        pens = []
        brushes = []
        for colour, line in enumerate(rectangles):
            x_left, y_top = calc.latlon_to_xy(line[0], line[1], self.zoom, self)
            x_right, y_bottom = calc.latlon_to_xy(line[2], line[3], self.zoom, self)
            width = abs(x_right - x_left)
            height = abs(y_bottom - y_top)
            rects.append([x_left - self.rel_pos_x, y_top - self.rel_pos_y, width, height])
            pen = wx.Pen(wx_colours[colour], RECTANGLE_LINE_WIDTH)
            pens.append(pen)
            if RECTANGLE_FILL:
                colour = pen.GetColour().Get(True)[:-1] + (RECTANGLE_FILL_ALPHA,) # take colour from pen, but replace alpha value
                brush = wx.Brush(colour)
            else:
                brush = wx.Brush(wx_colours[colour], wx.TRANSPARENT)
            brushes.append(brush)
        dc.DrawRectangleList(rects, pens, brushes)

    def draw_point_list(self, dc, coords, wx_colours):
        """Draw a list of points all at once.

        @param dc: a wx.DC that will be used for drawing.
        @type dc: wx.DC
        @param coords: a list containing (lat, lon) tuples.
        @param wx_colours: a list of at least as many colours as there are coord-pairs.
        @type wx_colours: iterable containing wx colours, e. g. wx.RED
        
        """
        draw_list = []
        pen_list = []
        for colour, coord in enumerate(coords):
            #self.draw_point(dc, coord[0], coord[1], wx_colours[colour])
            x, y = calc.latlon_to_xy(coord[0], coord[1], self.zoom, self)
            draw_list.append([x - POINT_SIZE / 2 + 1 - self.rel_pos_x,
                              y - POINT_SIZE / 2 + 1 - self.rel_pos_y,
                              POINT_SIZE, POINT_SIZE])
            pen_list.append(wx.Pen(wx_colours[colour], 2))
        dc.DrawRectangleList(draw_list, pen_list)


class MainWindow(wx.Frame):
    def __init__(self, parent, id, title, *args, **kwargs):
        wx.Frame.__init__(self, parent, id, title, *args, **kwargs)
        self.imagepanel = MapPanel(self)
        self.imagepanel.create_map()
        self.imagepanel.points.append([ 52.37930, 9.72310])      # DCSec, LUH, Hannover, Germany
        self.imagepanel.points.append([ 40.69840, -74.04150])    # Ellis Island, New York, USA
        self.imagepanel.points.append([-33.99195, 151.23141])    # Bare Island, Sydney, Australia
        self.imagepanel.points.append([-51.69274, -57.85352])    # Stanley, Falkland Islands
        self.imagepanel.point_colours = ['red'] * len(self.imagepanel.points)
        self.imagepanel.rectangles.append([52.383280, 9.715250, 52.381950,  9.719430])    # Welfenschloss, Hannover, Germany
        self.imagepanel.rectangles.append([52.504319, 9.522644, 52.275200, 9.9182091])    # Hannover, Germany
        self.imagepanel.rectangle_colours = ['red', 'green']
        self.imagepanel.SetFocus()
        self.Show()


if __name__ == '__main__':
   myApp = wx.App()
   frame = MainWindow(None, -1, 'wxMapPanelTest', size=(1024, 768))
   myApp.MainLoop()
