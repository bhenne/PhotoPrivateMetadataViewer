#!/usr/bin/env python
"""Loads OSM tiles from the Web using threading and urllib3"""

import os
import sys
import random
import threading

from Queue import Queue
import urllib3

import wx

__author__ = "B. Henne"
__maintainer__ = "B. Henne"
__contact__ = "henne@dcsec.uni-hannover.de"
__copyright__ = "(c) 2012, DCSec, Leibniz Universitaet Hannover, Germany"
__license__ = "GPLv3"


LAYERS = {"tah": ["cassini.toolserver.org:8080", "/http://a.tile.openstreetmap.org/+http://toolserver.org/~cmarqu/hill/"],
          "oam": ["oam1.hypercube.telascience.org", "/tiles/1.0.0/openaerialmap-900913/"],
          "mapnikold": ["tile.openstreetmap.org", "/mapnik/"],
          "mapnik": [["a.tile.openstreetmap.org", "b.tile.openstreetmap.org", "c.tile.openstreetmap.org"], "/"],
}


class TileLoader(object):
    """A tile downloader using threads for downloads"""

    def __init__(self, tile_list={}, cache_dir='.cache', NUM_WORKER=1, NUM_SOCKETS=3):
        """Inits the TileLoader with its threads"""

        self.dl_queue = Queue()
        self.load_queue = Queue()
        self.data_dir = os.path.join(os.path.dirname(os.path.abspath(sys.modules[self.__module__].__file__)), 'data')
        self.cache_dir = cache_dir
        self.tile_list = tile_list
        self.loading_image = wx.EmptyBitmap(1, 1)
        self.loading_image.LoadFile(os.path.join(self.data_dir, 'loading.png'), wx.BITMAP_TYPE_ANY)
        self.NUM_SOCKETS = NUM_SOCKETS
        self.t = []
        for w in xrange(0, NUM_WORKER):
            self.t.append(threading.Thread(target=self.worker))
        for t in self.t:
            t.setDaemon(True)
            t.start()

    def worker(self):
        """Thread worker"""

        http = urllib3.PoolManager(maxsize=self.NUM_SOCKETS)
        while True:
            tile = self.dl_queue.get()
            ok = False
            tries = 3
            while (ok == False) and (tries > 0):
                tries -= 1
                r = http.request('GET', tile[0])
                ok = self.handle_response(r.data, tile[1], tile[2], tile[3], tile[4], tile[5])
            self.load_queue.put((tile[1], tile[2], tile[3], tile[4], tile[5]))
            self.dl_queue.task_done()

    def handle_response(self, r, x, y, z, layer, file_extension):
        """Handles download responses, writes images to files"""

        if '<html>' in r:
            # something went wrong...mostlikely a 404 error
            return False
        elements = [self.cache_dir, layer, str(z), str(x)]
        path = ''
        for element in elements:
            path = os.path.join(path, element)
            try:
                os.mkdir(path)
            except OSError:
                #folder exists, no need to create
                pass
        path = os.path.join(path, str(y) + file_extension)
        image_file = open(path, 'wb')
        image_file.write(r)
        image_file.flush()
        image_file.close()
        return True

    def load_images(self):
        """Loads images downloaded by workers to tile_list"""

        for i in xrange(0, self.load_queue.qsize()):
            x, y, z, layer, file_extension = self.load_queue.get()
            path = os.path.join(self.cache_dir, layer, str(z), str(x), str(y) + file_extension)
            image = wx.EmptyBitmap(1, 1)
	    image.LoadFile(path, wx.BITMAP_TYPE_ANY)
            self.tile_list[(x, y, z)] = image
            self.load_queue.task_done()

    def enqueue_tile(self, x, y, z, layer='mapnik'):
        """Enqueues a tile to be downloaded"""

        if type(LAYERS[layer][0]) == str:
            host = LAYERS[layer][0]
        elif type(LAYERS[layer][0]) == list:
            host = random.choice(LAYERS[layer][0])
        layer = layer

        base_url_extension = LAYERS[layer][1]
        file_extension = '.jpg' if layer == 'oam' else '.png'

        #path = os.path.join(self.cache_dir, layer, str(z), str(x), str(y) + file_extension)
        #assert os.path.isfile(path) == False
        self.tile_list[(x, y, z)] = self.loading_image

	url = 'http://' + host + base_url_extension + str(z) + '/' + str(x) + '/' + str(y) + file_extension
        self.dl_queue.put((url, x, y, z, layer, file_extension))
	return True


def test():
    myApp = wx.App()
    t = TileLoader()
    import time
    x=40
    while 1:
        if x < 50:
            for i in xrange(0,20):
                t.enqueue_tile(34, x, 16)
        if t.dl_queue.qsize() <= 0:
            break
	print "Queue size: %s" % t.dl_queue.qsize()
        time.sleep(1)
        t.load_images()
        x += 1


if __name__ == '__main__':
    test()

