Photo Private Metadata Viewer

This programm views your photos (jpegs) and shows you the typically relevant
private metadata that may be stored within your files.
To the best of my knowledge, currently there is no other programm capable of
showing the different person/region tags as supported by this tool.

Metadata is nice and useful, but also can be harmful.
Use it with caution.

Requirements:
 * Python 2.7
 * wxPython
 * pyexiv2 >= revision 373
 * libexiv2 >= version 0.23, or patched 0.22 (see doc/)

Usage:
 ./mdviewer.py
 or 'python mdviewer.py'
 or double-click mdviewer.py
  depending on your system, tested with Ubuntu Linux, OS X and Windows 7.

Features:
 * shows single files
 * browses files in a directory
 * browses files in a directory structure recursively
 * opens a file directly from the Web via its URL
 * shows a file's complete metadata tree
 * explicitly shows private metadata 
 * shows a map for GPS locations

Featured private metadata:
 * person (region) tags
   * stored in file with Metadata Working Group Region Schema
     as written by Google's Picasa 3.9+
   * stored in file with Microsoft Photo Region Information Schema
     as written by Windows Live Photo Gallery
   * stored in .picasa.ini
     as created by Google's Picasa 3.x

Working on:
 * GPS location
   * show exact GPS locations on the map (point)
 * textual locations
   * show textual locations including location information accuracy (bounding box)
 * potential private metadata
   as phone numbers, camera ids, aso.

How to tag persons/regions stored in files?
 see doc/HowToTag.txt

Contact:
 Benjamin Henne <henne@dcsec.uni-hannover.de>
