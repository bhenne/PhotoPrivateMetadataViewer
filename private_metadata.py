#!/usr/bin/env python

"""Module for privacy-related high-level photo metadata management"""

import pyexiv2

__author__ = "B. Henne"
__contact__ = "henne@dcsec.uni-hannover.de"
__copyright__ = "(c) 2012, B. Henne"
__license__ = "GPLv3"

class Metadatum(object):
    "An abstract metadatum"
    def __init__(self, name, value=None, key=None, description='no description'):
        self.name = name
        self.key = key
        self.description = description
        if isinstance(value, pyexiv2.ImageMetadata):
            self.parse(value)
        else:
            self.value = value
    def parse(self, imageMetadata):
        if self.key in imageMetadata:
            self.value = imageMetadata[self.key].value
            self.raw_value = self.value = imageMetadata[self.key].raw_value
        else:
            self.value = None
            self.raw_value = None
    def __str__(self):
        return '%s: %s' % (self.name, self.value)
    def __repr__(self):
        return self.__str__()


class MdMediaproPpl(Metadatum):
    """Xmp iView Media Pro schema: People"""
    def __init__(self, value):
        super(MdMediaproPpl, self).__init__(name='mediapro.People', value=value,
                                            key='Xmp.mediapro.People',
                                            description='Xmp iView Media Pro schema: People')


class MdIptc4ExtPpl(Metadatum):
    """Xmp IPTC Extension schema: PersonsInImage"""
    def __init__(self, value):
        super(MdIptc4ExtPpl, self).__init__(name='iptc4ext.People', value=value,
                                            key='Xmp.iptcExt.PersonInImage',
                                             description='Xmp IPTC Extension schema: PersonsInImage')

     
class MdMwgRs(Metadatum):
    """Xmp Metadata Working Group Region Schema
    
    @see http://www.metadataworkinggroup.org/pdf/mwg_guidance.pdf"""
    UNKNOWN = 1024
    POINT = 1
    CIRCLE = 2
    RECTANGLE = 4
    FACE = 8
    PET = 16
    FOCUS = 32
    BARCODE = 64 
    def __init__(self, value):
        super(MdMwgRs, self).__init__(name='mwg-rs', value=value, 
                                      key='Xmp.mwg-rs.Regions',
                                      description='Xmp Metadata Working Group Region Schema Data')
    @classmethod
    def example(self):
        """List of Tuples with [type, name, x, y <, diameter|{width, height}>]"""
        return [ [self.FACE | self.POINT,     'John Doe', 0.2, 0.2 ],
                 [self.FACE | self.CIRCLE,    'Jane Doe', 0.4, 0.4, 0.1],
                 [self.FACE | self.RECTANGLE, 'J.J. Doe', 0.6, 0.6, 0.1, 0.1] ]
    def parse(self, imageMetadata):
        if 'Xmp.mwg-rs.Regions/mwg-rs:AppliedToDimensions' in imageMetadata:
            if 'Xmp.mwg-rs.Regions/mwg-rs:AppliedToDimensions/stDim:w' in imageMetadata and 'Xmp.mwg-rs.Regions/mwg-rs:AppliedToDimensions/stDim:h' in imageMetadata:
               self.AppliedToDimensions = (imageMetadata['Xmp.mwg-rs.Regions/mwg-rs:AppliedToDimensions/stDim:w'].value,
                                           imageMetadata['Xmp.mwg-rs.Regions/mwg-rs:AppliedToDimensions/stDim:h'].value,
                                           imageMetadata['Xmp.mwg-rs.Regions/mwg-rs:AppliedToDimensions/stDim:unit'].value)
        if 'Xmp.mwg-rs.Regions/mwg-rs:RegionList' in imageMetadata:
            i = 1
            self.value = []
            while 'Xmp.mwg-rs.Regions/mwg-rs:RegionList[%i]' % i in imageMetadata:
                v = None
                # Area in RegionStruct is required
                if 'Xmp.mwg-rs.Regions/mwg-rs:RegionList[%i]/mwg-rs:%s' % (i, 'Area') in imageMetadata:
                    # OPTIONAL
                    # Type is optional closed choise
                    type = self.UNKNOWN
                    if 'Xmp.mwg-rs.Regions/mwg-rs:RegionList[%i]/mwg-rs:%s' % (i, 'Type') in imageMetadata:
                        t = imageMetadata['Xmp.mwg-rs.Regions/mwg-rs:RegionList[%i]/mwg-rs:%s' % (i, 'Type')].value.lower()
                        if t == 'face':
                            type = self.FACE
                        elif t == 'pet':
                            type = self.PET
                        elif t == 'focus':
                            type = self.FOCUS
                        elif t == 'barcode':
                            type = self.BARCODE                        
                    # Name/short Description of Region is optional
                    name = ''
                    if 'Xmp.mwg-rs.Regions/mwg-rs:RegionList[%i]/mwg-rs:%s' % (i, 'Name') in imageMetadata:
                        name = imageMetadata['Xmp.mwg-rs.Regions/mwg-rs:RegionList[%i]/mwg-rs:%s' % (i, 'Name')].value
                    # Description of Region is optional
                    description = ''
                    if 'Xmp.mwg-rs.Regions/mwg-rs:RegionList[%i]/mwg-rs:%s' % (i, 'Description') in imageMetadata:
                        description = imageMetadata['Xmp.mwg-rs.Regions/mwg-rs:RegionList[%i]/mwg-rs:%s' % (i, 'Description')].value
                    #TODO: FocusUsage, BarCodeValue, Extensions
                    # parse REQUIRED Area values
                    if 'Xmp.mwg-rs.Regions/mwg-rs:RegionList[%i]/mwg-rs:Area/stArea:%s' % (i, 'x') in imageMetadata:
                        xcenter =  float(imageMetadata['Xmp.mwg-rs.Regions/mwg-rs:RegionList[%i]/mwg-rs:Area/stArea:%s' % (i, 'x')].value)
                    else:
                        xcenter = float('-inf')
                    if 'Xmp.mwg-rs.Regions/mwg-rs:RegionList[%i]/mwg-rs:Area/stArea:%s' % (i, 'y') in imageMetadata:
                        ycenter =  float(imageMetadata['Xmp.mwg-rs.Regions/mwg-rs:RegionList[%i]/mwg-rs:Area/stArea:%s' % (i, 'y')].value)
                    else:
                        ycenter = float('-inf')
                    if 'Xmp.mwg-rs.Regions/mwg-rs:RegionList[%i]/mwg-rs:Area/stArea:%s' % (i, 'w') in imageMetadata:
                        width =  float(imageMetadata['Xmp.mwg-rs.Regions/mwg-rs:RegionList[%i]/mwg-rs:Area/stArea:%s' % (i, 'w')].value)
                    else:
                        width = float('-inf')
                    if 'Xmp.mwg-rs.Regions/mwg-rs:RegionList[%i]/mwg-rs:Area/stArea:%s' % (i, 'h') in imageMetadata:
                        height =  float(imageMetadata['Xmp.mwg-rs.Regions/mwg-rs:RegionList[%i]/mwg-rs:Area/stArea:%s' % (i, 'h')].value)
                    else:
                        height = float('-inf')
                    if 'Xmp.mwg-rs.Regions/mwg-rs:RegionList[%i]/mwg-rs:Area/stArea:%s' % (i, 'd') in imageMetadata:
                        diameter =  float(imageMetadata['Xmp.mwg-rs.Regions/mwg-rs:RegionList[%i]/mwg-rs:Area/stArea:%s' % (i, 'd')].value)
                    else:
                        diameter = float('-inf')
                    if 'Xmp.mwg-rs.Regions/mwg-rs:RegionList[%i]/mwg-rs:Area/stArea:%s' % (i, 'unit') in imageMetadata:
                        unit =  imageMetadata['Xmp.mwg-rs.Regions/mwg-rs:RegionList[%i]/mwg-rs:Area/stArea:%s' % (i, 'unit')].value
                    else:
                        unit = 'normalized'
                    # and see what we've got
                    if (xcenter >= 0) and (ycenter >= 0):
                        # rectangle
                        if (width >= 0) and (height >= 0):
                            type |= self.RECTANGLE
                            v = [type, name, xcenter, ycenter, width, height]
                            #v = [type, name, xcenter-width/2, ycenter-height/2, width, height]
                        # circle
                        elif (diameter >= 0):
                            type |= self.CIRCLE
                            v = [type, name, xcenter, ycenter, diameter]
                        # point
                        else:
                            type |= self.POINT
                            v = [type, name, xcenter, ycenter]
                    else:
                        # should never happen
                        v = [type, name]
                    self.value.append(v)
                i += 1
                self.value = sorted(self.value)
        else:
            self.value = None

        
class MdMPRI(Metadatum):
    """Xmp Microsoft Photo RegionInfo Schema
    
    @see http://msdn.microsoft.com/en-us/library/ee719905%28VS.85%29.aspx"""
    ANYWHERE = 0
    RECTANGLE = 4
    FACE = 8
    def __init__(self, value):
        super(MdMPRI, self).__init__(name='mp-ri', value=value, 
                                     key='Xmp.MP.RegionInfo',
                                     description='Metadata Working Group Region Schema Data')
    @classmethod
    def example(self):
        """List of Tuples with [type, name, <x-left, y-top, width, height>]"""
        return [ [self.FACE | self.ANYWHERE,  'John Doe' ],
                 [self.FACE | self.RECTANGLE, 'Jane Doe', 0.6, 0.6, 0.1, 0.1] ]
    def parse(self, imageMetadata):
        if 'Xmp.MP.RegionInfo/MPRI:Regions' in imageMetadata:
            i = 1
            self.value = []
            while 'Xmp.MP.RegionInfo/MPRI:Regions[%i]' % i in imageMetadata:
                # PersonDisplayName is required field
                if 'Xmp.MP.RegionInfo/MPRI:Regions[%i]/%s' % (i, 'MPReg:PersonDisplayName') in imageMetadata:     
                    name = imageMetadata['Xmp.MP.RegionInfo/MPRI:Regions[%i]/%s' % (i, 'MPReg:PersonDisplayName')].value
                    # PersonLiveCID is optional, store as name extension
                    if 'Xmp.MP.RegionInfo/MPRI:Regions[%i]/%s' % (i, 'MPReg:PersonLiveCID') in imageMetadata:
                        name += ' (%s)' % imageMetadata['Xmp.MP.RegionInfo/MPRI:Regions[%i]/%s' % (i, 'MPReg:PersonLiveCID')].value
                    # Rectangle is optional, People may marked without any
                    if 'Xmp.MP.RegionInfo/MPRI:Regions[%i]/%s' % (i, 'MPReg:Rectangle') in imageMetadata:
                        r = imageMetadata['Xmp.MP.RegionInfo/MPRI:Regions[%i]/%s' % (i, 'MPReg:Rectangle')].value
                        left, top, width, height = eval(r)
                        v = [self.FACE | self.RECTANGLE, name, left, top, width, height]
                    else:
                        v = [self.FACE | self.ANYWHERE, name]
                self.value.append(v)
                i += 1
            self.value = sorted(self.value)
        else:
            self.value = None


class WGS84Location(Metadatum):

    def __init__(self, value):
        super(WGS84Location, self).__init__(name='Exif-GPSInfo', value=value,
                                             key='Exif.GPSInfo',
                                             description='WGS-84 Latitude/Longitude Location')
    def parse(self, imageMetadata):
        latref = 0
        if 'Exif.GPSInfo.GPSLatitudeRef' in imageMetadata:
	        if imageMetadata['Exif.GPSInfo.GPSLatitudeRef'].value == 'N':
                    latref = 1
	        elif imageMetadata['Exif.GPSInfo.GPSLatitudeRef'].value == 'S':
                    latref = -1
	        else:
  	            print 'not interpretable GPSLatitudeRef:', imageMetadata['Exif.GPSInfo.GPSLatitudeRef'].value
        lonref = 0
        if 'Exif.GPSInfo.GPSLongitudeRef' in imageMetadata:
	        if imageMetadata['Exif.GPSInfo.GPSLongitudeRef'].value == 'E':
                    lonref = 1
	        elif imageMetadata['Exif.GPSInfo.GPSLongitudeRef'].value == 'W':
    	            lonref = -1
	        else:
  	            print 'not interpretable GPSLongitudeRef:', imageMetadata['Exif.GPSInfo.GPSLongitudeRef'].value
        flat = 0
        if 'Exif.GPSInfo.GPSLatitude' in imageMetadata:
	    lat = imageMetadata['Exif.GPSInfo.GPSLatitude'].value
	    flat = float(lat[0]) + float(lat[1])/60 + float(lat[2])/3600
        flon = 0
        if 'Exif.GPSInfo.GPSLongitude' in imageMetadata:
            lon = imageMetadata['Exif.GPSInfo.GPSLongitude'].value
            flon = float(lon[0]) + float(lon[1])/60 + float(lon[2])/3600
        falt = 0
        if 'Exif.GPSInfo.GPSAltitude' in imageMetadata:
            falt = float(imageMetadata['Exif.GPSInfo.GPSAltitude'].value)
            if 'Exif.GPSInfo.GPSAltitudeRef' in imageMetadata:
                if int(imageMetadata['Exif.GPSInfo.GPSAltitudeRef'].value) == 1:
                    falt *= -1
        fdop = 0
        if 'Exif.GPSInfo.GPSDOP' in imageMetadata:
            dop = imageMetadata['Exif.GPSInfo.GPSDOP'].value
            fdop = float(dop)
        if (flat != 0) and (flon != 0):
            self.value = [ flat*latref, flon*lonref, falt , fdop] #: lat, lon, alt, dop
        else:
            self.value = None

    
class PrivateMetadata(pyexiv2.ImageMetadata):
    
    def __init__(self, filename=None):
        super(PrivateMetadata, self).__init__(filename)
        #self.imageMetadata = pyexiv2.ImageMetadata(filename)
        self.privateMetadata = None
    
    def read(self):
        super(PrivateMetadata, self).read()
        self.__parsePrivateMetadata()
    
    def __parsePrivateMetadata(self):
        # Persons, Faces, Regions
        self.privateMetadata = {}
        self.privateMetadata['people:mediapro'] = MdMediaproPpl(self)
        self.privateMetadata['people:iptc4ext'] = MdIptc4ExtPpl(self)
        self.privateMetadata['people:mwgrs'] = MdMwgRs(self)
        self.privateMetadata['people:mpri'] = MdMPRI(self)
        self.privateMetadata['location:wgs84'] = WGS84Location(self)


def unifix(any):
    if any is None:
        return u''
    try:
        return unicode(any)
    except:
        return unicode(any, errors='replace')


class MetadataTree(object):

    class Node (object):
        def __init__(self, data, name=u'', parent=None):
            self.name = unifix(name)
            self.data = data
            self.parent = parent
            self.children = []
        def add_child(self, child):
            self.children.append(child)
            child.parent = self
            return child
        def has_child_called(self, name):
            return [child for child in self.children if child.name == name]
        def __str__(self, depth=0):
            if self.parent is not None:
                myname = u'%s%s: %s\n' % (u' '*depth, unifix(self.name), unifix(self.data))
            else:
                myname = u''
                depth=-1
            mychildren = u''
            for child in self.children:
                mychildren += child.__str__(depth=depth+1)
            ret = u'%s%s' % (myname, mychildren)
            if self.parent is not None:
                return ret
            else:
                return ret.rstrip('\n')
            
    def __init__(self, metadata, nsprefix=True, stripSingleChildNodes=True):
        """@param nsprefix: suppress namespace prefixes if possible
           @param stripSingleChildNodes: if a node has only one child combine them to lower hierarchy depth"""
        super(MetadataTree, self).__init__()
        self.root = None
        self.loadMetadata(metadata, nsprefix=nsprefix)
        if stripSingleChildNodes == True:
            self.stripSingleChildNodes()
        
    def loadMetadata(self, metadata, nsprefix=True):
        def _multisplit(s, seps=['.','/'], nsprefix=True):
            res = [s.replace('[', '.[')]
            for sep in seps:
                s, res = res, []
                for seq in s:
                    res += seq.split(sep)
            if nsprefix == True:
                return res
            else:
                return [e.split(':')[-1] for e in res]
        if len(metadata.keys()) > 0:
            self.root = self.Node(data=None, name=u'', parent=None)
            for k, v in metadata.iteritems():
                currentnode = self.root
                for nodename in _multisplit(k, nsprefix=nsprefix):
                    thatchild = currentnode.has_child_called(nodename)
                    if len(thatchild) == 0:
                        currentnode = currentnode.add_child(self.Node(data=None, name=nodename, parent=None))
                    else:
                        currentnode = thatchild[0]
                try:
                    currentnode.data = v.value
                except:
                    currentnode.data = v.raw_value
            
    def stripSingleChildNodes(self):
        def _recur(node):
            if len(node.children) > 0:
                for currentnode in node.children:
                    if (len(currentnode.children) == 1) and ((currentnode.data == None) or (currentnode.data == u'')) and not (currentnode.name.startswith('[')):
                        currentnode.children[0].name = currentnode.name+u'|'+currentnode.children[0].name
                        currentnode.children[0].parent = currentnode.parent
                        currentnode.parent.children[currentnode.parent.children.index(currentnode)] = currentnode.children[0]
                        #print currentnode.name
                        #print [n.name for n in currentnode.parent.children]
                        #print currentnode.parent.children[currentnode.parent.children.index(currentnode)].name
                        #print currentnode.children[0]
                    _recur(currentnode)
        if self.root is not None:
            _recur(self.root)
        
        
    def __str__(self):
        return self.root.__str__()
	


def testImage():
    import Image, StringIO
    i = Image.new('RGBA', (20,20))
    s = StringIO.StringIO()
    i.save( s, "JPEG", quality = 95)
    jpg_data = s.getvalue()
    return jpg_data

def test():
    # new image w/o metadata
    p = PrivateMetadata.from_buffer(testImage())
    p.read()
    print '%s\n' % p.exif_keys
    # a face-tagged image
    p = PrivateMetadata('samples/empty.jpg')
    p.read()
    print '%s\n' % p.privateMetadata
    print '%s\n' % MetadataTree(p, nsprefix=False, stripSingleChildNodes=True)

  
if __name__ == '__main__':
    test()
