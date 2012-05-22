"""Loads OSM tiles asynchronously from the Web."""

__author__ = "P. Tute"
__copyright__ = "(c) 2012, DCSec, Leibniz Universitaet Hannover, Germany"
__license__ = "GPLv3"

import os
import asyncore
import threading
import asynchttp
import wx

PORT = 80
METHOD = 'GET'

LAYERS = {"tah": ["cassini.toolserver.org:8080", "/http://a.tile.openstreetmap.org/+http://toolserver.org/~cmarqu/hill/"],
          "oam": ["oam1.hypercube.telascience.org", "/tiles/1.0.0/openaerialmap-900913/"],
          "mapnik": ["tile.openstreetmap.org", "/mapnik/"]
}

class TileLoader(asynchttp.AsyncHTTPConnection):
    """This class uses asynchttp to download OSM tiles in an asynchronous manner.
    
    @author: P. Tute
    
    """
    def __init__(self, viewer, x, y, z, layer='mapnik'):
        """viewer is an instance of the viewer that uses the tiles.
        layer is one of 'tah', 'oam', and 'mapnik' (default)."""
        host = LAYERS[layer][0]
        self.layer = layer
        asynchttp.AsyncHTTPConnection.__init__(self, host, PORT)

        self.base_url_extension = LAYERS[layer][1]
        #self.file_extension = '.' + self.tileLayerExt(layer)
        self.file_extension = '.jpg' if layer == 'oam' else '.png'

        self.viewer = viewer
        self.x, self.y, self.z = x, y, z
        self.viewer.tiles[(self.x, self.y, self.z)] = viewer.placeholder
        
        self.connect()

    def get_tile(self):
        """Builds a response and tries to download the right tile from x, y, andd zoom-values."""
        url = self.base_url_extension + str(self.z) + '/' + str(self.x) + '/' + str(self.y) + self.file_extension
        self.putrequest('GET', url)
        self.endheaders()
        self.getresponse()

    def handle_connect(self):
        asynchttp.AsyncHTTPConnection.handle_connect(self)
        self.get_tile()

    def handle_response(self):
        if self.response.status != 200:
            # something went wrong...mostlikely a 404 error
            raise asynchttp.AsyncHTTPException('Trying to get tile ended up with status %s (%s).'
                    % (self.response.status, self.response.reason), name=str(self))
            return
        elements = [self.viewer.cache_dir, self.layer, str(self.z), str(self.x)]
        path = ''
        for element in elements:
            path = os.path.join(path, element)
            try:
                os.mkdir(path)
            except OSError:
                #folder exists, no need to create
                pass
        path = os.path.join(path, str(self.y) + self.file_extension)
        image_file = open(path, 'wb')
        image_file.write(self.response.body)
        image_file.flush()
        image_file.close()
        image = wx.EmptyBitmap(1, 1)     # Create a bitmap container object. The size values are dummies.
        image.LoadFile(path, wx.BITMAP_TYPE_ANY)   # Load it with a file image.
        #image.anchor_x = image.width / 2
        #image.anchor_y = image.height / 2
        self.viewer.tiles[(self.x, self.y, self.z)] = image
