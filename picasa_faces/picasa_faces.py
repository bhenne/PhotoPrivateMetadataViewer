#!/usr/bin/env python
"""Picasa face information loading from .picasa.ini and contacts.xml files
@author: B. Henne"""

import os
from xml.etree import ElementTree as ET

__author__ = "B. Henne"
__contact__ = "henne@dcsec.uni-hannover.de"
__copyright__ = "(c) 2012, B. Henne"
__license__ = "GPLv3"

class PicasaContacts(object):
    """Stores Picasa Contacts from XML file.

    Contacts XML file typically is stored in Application Data/Support
    subdirectory Google/Picasa3/contacts/contacts.xml

    @author: B. Henne
    """
    
    try:
        user = os.getlogin()
    except:
        user = os.environ.get('USER') or os.environ.get('USERNAME')
    home = os.getenv('USERPROFILE') or os.getenv('HOME')
    defaultpaths = [ '%s/Library/Application Support/Google/Picasa2/contacts/contacts.xml' % home,
                     '%s/Library/Application Support/Google/Picasa3/contacts/contacts.xml' % home,
                     '%s\AppData\Local\Google\Picasa2\contacts\contacts.xml' % home,
                     '%s\AppData\Local\Google\Picasa3\contacts\contacts.xml' % home,
                     str(os.getenv('LocalAppData'))+'\Google\Picasa2\contacts\contacts.xml',
                     str(os.getenv('LocalAppData'))+'\Google\Picasa2\contacts\contacts.xml',
                     '%s/.google/picasa/3.8/drive_c/Documents\ and\ Settings/%s/Local\ Settings/Application\ Data/Google/Picasa2/contacts/contacts.xml' % (home, user),
                     os.getcwd()+'/contacts.xml',
                    ] #: default paths for searching for contacts.xml if instantiated with contactsXML=None
    
    def __init__(self, contactsXML, ignoreIOErrors=True):
        """Loads contacts from file

        @param contactsXML: filename w/path of contacts XML file
        """
        super(PicasaContacts, self).__init__()
        self.contacts = {}
        self.contactsXML = None
        if contactsXML is None:
            for path in self.defaultpaths:
                if os.path.isfile(path):
                    self.contactsXML = path
                    break
            if self.contactsXML is None and ignoreIOErrors == False:
                raise IOError('Could not find Picasa contacts XML file at any default path.')
        elif os.path.isfile(contactsXML):
            self.contactsXML = contactsXML
        else:
            if ignoreIOErrors == False:
                raise IOError('Picasa contacts XML file %s does not exist.' % contactsXML)
        root = ET.fromstring('<contacts></contacts>')
        try:
           tree = ET.parse(self.contactsXML)
           root = tree.getroot()
        except:
           pass
	for subelement in root:
		self.contacts[subelement.attrib['id']] = subelement.attrib['name']


class PicasaIniFaces(object):
    """Stores Picasa face information from a .picasa.ini file."""
    def  __init__(self, folder, picasaContacts=None, include_unnamed=False):
        """Loads face information from file

        @param folder: folder containing the .picasa.ini file
        @param picasaContacts: optional hash to name mapping
        """
        super(PicasaIniFaces, self).__init__()
        self.picasaContacts = None
        self.faces = {}
        if picasaContacts is not None and isinstance(picasaContacts, PicasaContacts):
            self.picasaContacts = picasaContacts
        if os.path.isdir(folder):
            self.folder = folder
            if os.path.isfile('%s/.picasa.ini' % folder):
                self.inifile = '%s/.picasa.ini' % folder
            else:
                raise IOError('Picasa file .picasa.ini does not exist in %s' % folder)
        else:
            raise IOError('Folder %s does not exist.' % folder)
        f = open(self.inifile, 'rt')
        thefile = None  #: filename
        thefaces = None #: list of face coordinates (left, top, width, height) \in 0..1
        for line in f:
            l = line[:-1]
            if l.startswith('['):
                filename = l[l.find("[")+1:l.find("]")]
                thefile = filename
                thefaces = []
            elif l.startswith('faces='):
                # see https://groups.google.com/a/googleproductforums.com/d/msg/picasa/vSpxjx7ss_c/36Q55HwVNt0J
                # The number encased in rect64() is a 64-bit hexadecimal number.
                # Break that up into four 16-bit numbers.
                # Divide each by the maximum unsigned 16-bit number (65535) and you'll have four numbers between 0 and 1.
                # The four numbers remaining give you relative coordinates for the face rectangle: (left, top, right, bottom).
                faces = l[6:-1].split(';')
                for face in faces:
                    rect, s, hash = face.partition(',')
                    if self.picasaContacts is not None and hash in self.picasaContacts.contacts:
                        hash = self.picasaContacts.contacts[hash]
                    clist = rect[7:-1]
                    while len(clist) < 16:
                        clist = '0%s' % clist
                    coords = [clist[0:4], clist[4:8], clist[8:12], clist[12:16]]
                    coords = [int(coords[0],16)/65535.0, int(coords[1],16)/65535.0, 
                              int(coords[2],16)/65535.0, int(coords[3],16)/65535.0] # left, top, right, bottom
                    coords = [coords[0], coords[1], coords[2]-coords[0], coords[3]-coords[1]] #: left, top, width, height
                    face = [hash, coords]
                    if hash != 'ffffffffffffffff' or include_unnamed == True:
                        thefaces.append(face)
                self.faces[thefile] = thefaces
    def __repr__(self):
        s = ''
        for file, faces in self.faces.items():
            s += '%s\n' % file
            for face in faces:
                s += '+ %s (%0.5f, %0.5f, %0.5f, %0.5f)\n' % (face[0], face[1][0], face[1][1], face[1][2], face[1][3])
        return s[:-1]
            

def test():
    c = PicasaContacts(None)
    c = PicasaContacts('samples/contacts.xml')
    t = PicasaIniFaces('samples', picasaContacts=c)
    print t


if __name__ == '__main__':
    test()
