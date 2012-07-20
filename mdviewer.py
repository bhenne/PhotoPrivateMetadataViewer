#!/usr/bin/env python

import sys, os
import pyexiv2, private_metadata
import picasa_faces.picasa_faces
import wx
from lib.proportionalsplitter import ProportionalSplitter
from osm_map.map_viewer import MapPanel

__author__ = "B. Henne"
__contact__ = "henne@dcsec.uni-hannover.de"
__copyright__ = "(c) 2012, B. Henne"
__license__ = "GPLv3"

def unifix(any):
    """Workaround for some bad unicode exceptions / wrong encoded metadata"""
    if any is None:
        return u''
    try:
        return unicode(any)
    except:
        return unicode(any, errors='replace')

class ImagePanel(wx.Panel):
    def __init__(self, parent, *args, **kwargs):
        wx.Panel.__init__(self, parent, *args, **kwargs)
        self.SetBackgroundColour("Light Grey")
        placeholder = (wx.EmptyImage(*self.GetSize()))
        placeholder.ConvertColourToAlpha(0,0,0)
        self.setImage(placeholder)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.SetFocus()

    def OnSize(self, e):
        self.Refresh()

    def OnPaint(self, e):
        panelw, panelh = self.GetClientSize()
        minsize = self.GetMinSize()
        minfactor = min(1.0*minsize[0]/self.w,1.0*minsize[1]/self.h)
        factor = max(minfactor, min(1.0*panelw/self.w, 1.0*panelh/self.h, 1.0))
        bmp = self.image.Scale(self.w*factor, self.h*factor, quality=wx.IMAGE_QUALITY_HIGH).ConvertToBitmap()
        posx, posy = (panelw - self.w*factor)/2, (panelh - self.h*factor)/2  
        dc = wx.AutoBufferedPaintDCFactory(self)
        dc.Clear()
        dc.DrawBitmap(bmp, posx, posy, True)
        if self.rects is not None:
            dc.SetBrush(wx.TRANSPARENT_BRUSH)
            for r in self.rects:
                dc.SetPen(wx.Pen(r[5], 2, wx.SOLID))
                left = int((r[1])*self.w*factor)+posx
                top = int((r[2])*self.h*factor)+posy
                dc.DrawRectangle(left, top, int(r[3]*self.w*factor), int(r[4]*self.h*factor))
                dc.SetTextForeground(r[5])
                dc.DrawText(r[0].replace(" ", "\n"), left, top)
        del dc

    def setImage(self, image, rects=None):
        if isinstance(image, wx.Image):
            self.image = image
        elif os.path.isfile(image):
            self.image = wx.Image(image, wx.BITMAP_TYPE_ANY)
        else:
            raise(IOError, 'ImagePanel.setImage(image): image neither is a wx.Image nor a path to an image file')
        self.w = self.image.GetWidth()
        self.h = self.image.GetHeight()
        self.rects = rects
        self.Refresh()
        

class PrivateMDPanel(wx.Panel):
    def __init__(self, parent, *args, **kwargs):
        wx.Panel.__init__(self, parent, *args, **kwargs)
        self.text = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.text, 1, wx.EXPAND)
        self.SetSizer(sizer)


class MDTreePanel(wx.Panel):

    def __init__(self, parent, *args, **kwargs):
        wx.Panel.__init__(self, parent, *args, **kwargs)
        self.tree = wx.TreeCtrl(self)
        self.setupTree(None)
        self.tree.ExpandAll()
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.tree, 1, wx.EXPAND)
        self.SetSizer(sizer)
        #self.Bind(wx.EVT_CHAR, self.OnChar)
        #self.Bind(wx.EVT_TREE_KEY_DOWN, self.OnChar)

    def setupTree(self, data):
        tree = self.tree
        root = tree.AddRoot('browse file metadata ...')
        f = self.GetClassDefaultAttributes().font
        f.SetWeight(wx.FONTWEIGHT_LIGHT)
        tree.SetItemFont(root, f)

    def setMetadata(self, metadatatree, reset=True):
        def _recur(datanode, treectrlnode):
            if len(datanode.children) > 0:
                for currentdatanode in datanode.children:
                    data = u': '+unifix(currentdatanode.data) if (currentdatanode.data is not None) and (unifix(currentdatanode.data) != u'') else u''
                    child = self.tree.AppendItem(treectrlnode, currentdatanode.name+data)
                    self.tree.SetItemFont(child, f)
                    _recur(currentdatanode, child)

        f = self.GetClassDefaultAttributes().font
        if reset == True:
            self.tree.DeleteChildren(self.tree.GetRootItem())
        if metadatatree.root is not None:
            _recur(metadatatree.root, self.tree.GetRootItem())

    #def OnChar(self, event):
    #    keycode = event.GetKeyCode()
    #    print "x", keycode
    #    print keycode
    #    if keycode == wx.WXK_ESCAPE:
    #        ret  = wx.MessageBox('Are you sure to quit?', 'Question', 
    #            wx.YES_NO | wx.NO_DEFAULT, self)
    #        if ret == wx.YES:
    #            self.Close()
    #    elif (keycode == 83):
    #        frame.nextImage()
    #        print frame.nextImage
    #    elif  (keycode == 65):
    #        frame.previousImage()
    #    event.Skip()


class PicasaContactsDialog(wx.Dialog):
    def __init__(self, parent, title, *args, **kwargs):
        wx.Dialog.__init__(self, parent, wx.ID_ANY, title, *args, **kwargs)
        vbox = wx.BoxSizer(wx.VERTICAL)
        # headline
        text = wx.StaticText(self, 11, 'Select or reset your contacts.xml')
        vbox.Add(text, 1, wx.ALIGN_CENTER | wx.ALL, border=10)
        # text input
        fieldsizer = wx.BoxSizer(wx.HORIZONTAL)
        textlabel = wx.StaticText(self, label='Path: ')
        self.textfield = wx.TextCtrl(self)
        fieldsizer.Add(textlabel, 1, wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
        fieldsizer.Add(self.textfield, 12, wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        # reset or select file
        fieldButtonsizer = wx.BoxSizer(wx.HORIZONTAL)
        selectButton = wx.Button(self, wx.ID_FIND, "Select")
        resetButton = wx.Button(self, wx.ID_CLEAR, "Reset")
        fieldButtonsizer.Add(resetButton, 1, wx.RIGHT, border=5)
        fieldButtonsizer.Add(selectButton, 1, wx.RIGHT, border=5)
        # add sizer
        vbox.Add(fieldsizer, 0.5, wx.ALIGN_CENTER | wx.ALL, border=10)
        vbox.Add(fieldButtonsizer, 0.5, wx.ALIGN_RIGHT)
        # add final buttons
        bsizer = self.CreateButtonSizer(wx.OK|wx.CANCEL)
        vbox.Add(bsizer, 1, wx.ALIGN_CENTER | wx.ALL, border=10)
        self.SetSizer(vbox)
        self.Fit()
        # bind events to buttons 
        resetButton.Bind(wx.EVT_BUTTON, self.OnResetButton)
        selectButton.Bind(wx.EVT_BUTTON, self.OnSelectButton)

    def OnResetButton(self, e):
        self.textfield.SetValue('')

    def OnSelectButton(self, e):
        dlg = wx.FileDialog(self, "Choose your Picasa contacts.xml storing face names", self.GetParent().dirname, "", "*.xml", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.textfield.SetValue('%s/%s' % (dlg.GetDirectory(), dlg.GetFilename()))
        dlg.Destroy()

    def GetValue(self):
        return self.textfield.GetValue()

    def SetValue(self, value):
        return self.textfield.SetValue(value)


class MainWindow(wx.Frame):
    def __init__(self, parent, id, title,  *args, **kwargs):
        wx.Frame.__init__(self, parent, id, title, *args, **kwargs)
        self.frameTitlePrefix = title
        self.simpleView = False

        # Image handling
        self.initImageHandling()
        # Load config from file
        self.loadConfigFromFile()

        # Setting up the menu
        filemenu = wx.Menu()
        menuOpenF = filemenu.Append(wx.ID_OPEN, "Open &File"," Open an image file to view and browse")
        menuOpenD = filemenu.Append(wx.ID_ANY, "Open &Dir"," Open a directory to browse images")
        menuOpenU = filemenu.Append(wx.ID_ANY, "Open &URL"," Open an image file from a web URL (http://...)")
        menuAbout = filemenu.Append(wx.ID_ABOUT, "&About"," Information about this program")
        menuExit  = filemenu.Append(wx.ID_EXIT,"E&xit"," Terminate the program")
        settmenu = wx.Menu()
        menuGUIview = settmenu.AppendCheckItem(wx.ID_ANY, "Show simple GUI")
        menuGUIview.Check(self.simpleView)
        menuOpenR = settmenu.AppendCheckItem(wx.ID_ANY, "Browse directories recursively")
        menuOpenR.Check(self.browseRecursively)
        menuDlTmp = settmenu.AppendCheckItem(wx.ID_ANY, "Download URL images to ~/.mdviewer (instead of TMP)")
        menuDlTmp.Check(self.downloadURLstoHOME)
        menupicontacts = settmenu.Append(wx.ID_ANY,"Set Picasa &contacts.xml path","Set filepath to Picasa's contacts.xml (if not default or could not be found)")
        menuesavecfg = settmenu.Append(wx.ID_ANY,"Save &configuration now","Save configuration to file")

        # Creating the menubar
        menuBar = wx.MenuBar()
        menuBar.Append(filemenu,"&File")
        menuBar.Append(settmenu,"&Settings")
        self.SetMenuBar(menuBar)

        # Events for menus
        self.Bind(wx.EVT_MENU, self.OnOpenFile, menuOpenF)
        self.Bind(wx.EVT_MENU, self.OnOpenDir, menuOpenD)
        self.Bind(wx.EVT_MENU, self.OnOpenURL, menuOpenU)
        self.Bind(wx.EVT_MENU, self.GUISimpleView, menuGUIview)
        self.Bind(wx.EVT_MENU, self.OnOpenRec, menuOpenR)
        self.Bind(wx.EVT_MENU, self.OpenURLTmpHome, menuDlTmp)
        self.Bind(wx.EVT_MENU, self.saveConfigToFile, menuesavecfg)
        self.Bind(wx.EVT_MENU, self.setPicasaContacts, menupicontacts)
        self.Bind(wx.EVT_MENU, self.OnExit, menuExit)
        self.Bind(wx.EVT_MENU, self.OnAbout, menuAbout)

        if self.simpleView == True:
          # Define sizer
          sizer = wx.BoxSizer(wx.VERTICAL)
          self.imagepanel  = ImagePanel(self, size=(400,300))
          self.privmdpanel = PrivateMDPanel(self)
          sizer.Add(self.imagepanel,  4, wx.EXPAND)
          sizer.Add(self.privmdpanel, 1, wx.EXPAND)
          self.SetSizer(sizer)
        else:
          # Define splitter
          self.splitNS  = ProportionalSplitter(self,         -1, 0.66)
          self.splitNWO = ProportionalSplitter(self.splitNS, -1, 0.75)
          self.splitSWO = ProportionalSplitter(self.splitNS, -1, 0.60)
          # Define content
          self.imagepanel  = ImagePanel(self.splitNWO, size=(200,150))
          self.mappanel    = MapPanel(self.splitNWO)
          self.privmdpanel = PrivateMDPanel(self.splitSWO)
          self.mdtreepanel = MDTreePanel(self.splitSWO)
          # Define splitting
          self.splitNS.SplitHorizontally(self.splitNWO, self.splitSWO)
          self.splitNWO.SplitVertically(self.imagepanel, self.mappanel)
          self.splitSWO.SplitVertically(self.privmdpanel, self.mdtreepanel)

          # Setup map
          self.mappanel.create_map()

        # Events for GUI elements
        self.imagepanel.Bind(wx.EVT_KEY_UP, self.OnKeyUp)

        # Show
        self.Show()

    def initImageHandling(self):
        self.dirname = os.getcwd()
        self.filename = ''
        self.filelist = []
        self.currentfileid = 0
        self.image_metadata = {}
        self.picasa_faces = None
        self.picasaContactsFile = None
        self.lastImageLoadedDir = ''
        self.browseRecursively = False
        self.downloaddir = None
        self.tempdir = None
        self.downloadURLstoHOME = False
        
    def OnAbout(self,e):
        dlg = wx.MessageDialog(self, " Photo Private Metadata Viewer \n by Benjamin Henne \n<henne@dcsec.uni-hannover.de>\n", "About photo private_metadata viewer", wx.OK)
        dlg.ShowModal()
        dlg.Destroy()

    def OnExit(self,e):
        self.Close(True)

    def OnOpenFile(self,e):
        dlg = wx.FileDialog(self, "Choose an image file", self.dirname, "", "*.*", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.ImplOpenDirFile(os.path.dirname(os.path.abspath(dlg.GetDirectory())+'/'), os.path.basename(dlg.GetFilename()), type='file')
        dlg.Destroy()
        
    def OnOpenDir(self,e):
        dlg = wx.DirDialog(self, "Choose a directory containing images", self.dirname)
        if dlg.ShowModal() == wx.ID_OK:
            self.ImplOpenDirFile(os.path.dirname(os.path.abspath(dlg.GetPath())+'/'), '', type='file')
        dlg.Destroy()
        
    def OnOpenURL(self, e):
        dlg = wx.TextEntryDialog(self, "Open File from web URL:", "Open URL")
        dlg.SetValue("http://")
        if dlg.ShowModal() == wx.ID_OK:
            value = dlg.GetValue()
            if not (value.startswith('http://') or value.startswith('https://')):
                value = 'http://'+value
            self.ImplOpenDirFile(os.path.dirname(value), os.path.basename(value), type='URL')
        dlg.Destroy()

    def setPicasaContacts(self, e):
        dlg = PicasaContactsDialog(self, "Choose your Picasa contacts.xml storing face names")
        if self.picasaContactsFile is not None:
            dlg.SetValue(self.picasaContactsFile)
        if dlg.ShowModal() == wx.ID_OK:
            value = dlg.GetValue()
            if value != '':
                self.picasaContactsFile = value
            else:
                self.picasaContactsFile = None
        dlg.Destroy()
        self.loadImage(picasaReload=True)

    def OnOpenRec(self, e):
        self.browseRecursively = not self.browseRecursively
        self.ImplOpenDirFile(self.dirname, self.filename)

    def OpenURLTmpHome(self, e):
        self.downloadURLstoHOME = not self.downloadURLstoHOME
        self.downloaddir = None

    def GUISimpleView(self, e):
        self.simpleView = not self.simpleView
        dlg = wx.MessageDialog(self, "You have to 1) save configuration and 2) restart the viewer to apply changes to GUI.", "Have to restart", wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    def OnKeyUp(self, event):
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_ESCAPE:
            ret  = wx.MessageBox('Are you sure to quit?', 'Question', 
                wx.YES_NO | wx.NO_DEFAULT, self)
            if ret == wx.YES:
                self.Close()
        elif (keycode == wx.WXK_RIGHT) or (keycode == wx.WXK_NUMPAD_RIGHT) or (keycode == 83):
            self.ImplNextImage()
        elif (keycode == wx.WXK_LEFT) or (keycode == wx.WXK_NUMPAD_LEFT) or (keycode == 65):
            self.ImplPreviousImage()
        event.Skip()

    def loadConfigFromFile(self):
        home = os.getenv('HOME') or os.getenv('USERPROFILE')
        cfgfile = home+'/.mdviewer/'+'mdviewer.cfg'
        if os.path.isfile(cfgfile):
            import ConfigParser
            c = ConfigParser.SafeConfigParser({ 'browserecursively': str(self.browseRecursively),
                                                'dltohome': str(self.downloadURLstoHOME),
                                                'picasaini': str(self.picasaContactsFile),
                                                'simpleview': str(self.simpleView),
                                                })
            c.read(cfgfile)                                    
            self.browseRecursively = c.getboolean('mdviewer', 'browserecursively')
            self.downloadURLstoHOME = c.getboolean('mdviewer', 'dltohome')
            self.picasaContactsFile = c.get('mdviewer', 'picasaini')
            self.simpleView = c.getboolean('mdviewer', 'simpleview')

    def saveConfigToFile(self, e):
        home = os.getenv('HOME') or os.getenv('USERPROFILE')
        dir = home+'/.mdviewer/'
        if not os.path.isdir(dir):
            os.mkdir(dir)
        import ConfigParser
        c = ConfigParser.SafeConfigParser()
        c.add_section('mdviewer')
        c.set('mdviewer', 'browserecursively', str(self.browseRecursively))
        c.set('mdviewer', 'dltohome', str(self.downloadURLstoHOME))
        c.set('mdviewer', 'picasaini', str(self.picasaContactsFile))
        c.set('mdviewer', 'simpleview', str(self.simpleView))
        cfile = open(dir+'mdviewer.cfg', 'wb')
        c.write(cfile)
        cfile.close()

    def getJpgs(self, dir, recursive):
        list = []
        if os.path.isdir(dir):
            if recursive == False:
                for file in os.listdir(dir):
                    if file.lower().endswith('.jpg'):
                        list.append(os.path.join(dir, file))
            else:
                for path, paths, files in os.walk(dir):
                    for file in files:
                        if file.lower().endswith('.jpg'):
                            list.append(os.path.join(path, file))
        return sorted(list)

    def loadImage(self, picasaReload=False):
        #TODO: try+except IOError
    
        def shortenedfilename(flen=30, dlen=50):
            base = self.filename
            dir = self.dirname
            if len(base) > flen:
                base = base[0:flen/2-2]+'[..]'+base[-flen/2-2:]
            if len(dir) > dlen - len(base):
                dir = dir[0:(dlen - len(base))/2-2]+'[..]'+dir[-(dlen - len(base))/2-2:]
            return '%s/%s' % (dir, base)
        
        self.image_metadata = {}
        if self.filename != '':
            # picasa metadata from .picasa.ini
            if self.dirname != self.lastImageLoadedDir or picasaReload == True:
                    if os.path.isfile(os.path.join(self.dirname, '.picasa.ini')):
                        self.picasa_faces = picasa_faces.picasa_faces.PicasaIniFaces(self.dirname, picasa_faces.picasa_faces.PicasaContacts(self.picasaContactsFile))
            # image metadata from image file
            self.md = private_metadata.PrivateMetadata(self.fullname)
            try:
                self.md.read()
            except IOError as strerror:
                raise IOError('Could not read metadata from file: %s' % strerror)
            self.parseMetadata(self.md, self.picasa_faces)
            self.imagepanel.setImage(self.fullname, rects=self.image_rects)
        else:
            placeholder = (wx.EmptyImage(*self.GetSize()))
            placeholder.ConvertColourToAlpha(0,0,0)
            self.imagepanel.setImage(placeholder)
        self.privmdpanel.text.SetValue(str(self.image_metadata))
        frameTitleSuffix = ': %s' % shortenedfilename() if self.filename != '' else ''
        self.SetTitle(self.frameTitlePrefix+frameTitleSuffix)
        self.lastImageLoadedDir = self.dirname
        if self.simpleView == False:
            self.mdtree = private_metadata.MetadataTree(self.md, nsprefix=False)
            self.mdtreepanel.setMetadata(self.mdtree)
            self.privmdpanel.text.SetValue(str(self.image_metadata))
            if 'WGS84' in self.image_metadata:
                loc = self.image_metadata['WGS84']
                self.mappanel.greyedOverlay = None
                self.mappanel.points = [[loc[0], loc[1]]]
                self.mappanel.point_colours = ['red'] * len(self.mappanel.points)
                #TODO: read location accuracy from GPSDOP and draw rectangle/circle
                #    ! we cannot calculate any accuracy rectangle by any DOP
                #self.mappanel.rectangles = [[0, 0, 1, 1]]
                #self.mappanel.rectangle_colours = ['red']
                self.mappanel.center = self.mappanel.points[0]
                self.mappanel.Refresh()
            else:
                self.mappanel.greyedOverlay = [ 50, 80 ]
                self.mappanel.points = []
                self.mappanel.rectangles = []
                self.mappanel.Refresh()


    def parseMetadata(self, md, picasa_faces):
        rects = []
        people = []
        if picasa_faces is not None and self.filename in picasa_faces.faces and \
           picasa_faces.faces[self.filename] is not None and len(picasa_faces.faces[self.filename]) > 0:
                for i in picasa_faces.faces[self.filename]:
                    people.append(i[0])
                    rects.append([ i[0], i[1][0], i[1][1], i[1][2], i[1][3], 'blue' ])
        mpri = md.privateMetadata['people:mpri'].value
        if mpri is not None and len(mpri) > 0:
            for i in mpri:
                people.append(i[1])
                if i[0] & private_metadata.MdMPRI.RECTANGLE:
                    rects.append([ i[1], i[2], i[3], i[4], i[5], 'red' ])
        mwgrs = md.privateMetadata['people:mwgrs'].value
        if mwgrs is not None and len(mwgrs) > 0:
            for i in mwgrs:
                people.append(i[1])
                if i[0] & private_metadata.MdMwgRs.RECTANGLE:
                    rects.append([ i[1], i[2]-i[4]/2, i[3]-i[5]/2, i[4], i[5], 'green' ])
                if i[0] & private_metadata.MdMwgRs.CIRCLE:
                    # use diameter as width and height
                    rects.append([ i[1], i[2]-i[4]/2, i[3]-i[4]/2, i[4], i[4], 'green' ])
                if i[0] & private_metadata.MdMwgRs.POINT:
                    d = 0.04
                    rects.append([ i[1], i[2]-d/2, i[3]-d/2, d, d, 'green' ])
        mediaproppl = md.privateMetadata['people:mediapro'].value
        if mediaproppl is not None:
            people.append(mediaproppl)
        iptc4extPII = md.privateMetadata['people:iptc4ext'].value
        if iptc4extPII is not None:
            people.append(iptc4extPII)

        if len(rects) > 0:
            self.image_rects = rects
        else:
            self.image_rects = None
        self.image_metadata['people'] = sorted(people)
	if md.privateMetadata['location:wgs84'].value is not None:
		self.image_metadata['WGS84'] = md.privateMetadata['location:wgs84'].value

    def ImplOpenDirFile(self, directory, filename, type='file'):
            if type == 'file':
                self.ImplNextImage = self.ImplNextImageLocal
                self.ImplPreviousImage = self.ImplPreviousImageLocal
            elif type == 'URL':
                self.ImplNextImage = self.ImplNextImageLocal
                self.ImplPreviousImage = self.ImplPreviousImageLocal
                #self.ImplNextImage = lambda *x, **xx: None # we can override this to browse image only, e.g. via Flickr API
                #self.ImplNextImage = lambda *x, **xx: None # or any other api, if using service specifiv url. browse only using
                # IOString instead of downloading image files. Or download, but browse images at service ...
                if self.downloaddir == None:
                    home = os.getenv('HOME') or os.getenv('USERPROFILE')
                    if self.downloadURLstoHOME == True and home is not None:
                        userdir = home+'/.mdviewer/'
                        if not os.path.isdir(userdir):
                            os.mkdir(userdir, 0755)
                        self.downloaddir = userdir
                    else:
                        if self.tempdir == None:
                            import tempfile
                            self.tempdir = tempfile.mkdtemp()
                        self.downloaddir = self.tempdir
                import urllib2
                try:
                    dlfile = open('%s/%s' % (self.downloaddir, filename), 'wb')
                    dlfile.write(urllib2.urlopen('%s/%s' % (directory, filename)).read())
                    dlfile.close()
                    directory = self.downloaddir
                except IOError:
                    sys.stderr.write('URL not found: %s/%s' % (directory, filename))
                    directory = self.dirname
                    filename = self.filename
            self.dirname = directory
            self.filename = filename
            self.fullname = os.path.join(self.dirname, self.filename)
            self.filelist = self.getJpgs(self.dirname, self.browseRecursively)
            if len(self.filelist) > 0:
                if self.filename == '':
                    self.currentfileid = 0
                    self.filename = os.path.basename(self.filelist[self.currentfileid])
                    self.dirname = os.path.dirname(self.filelist[self.currentfileid])
                    self.fullname = os.path.join(self.dirname, self.filename)
                else:
                    self.currentfileid = self.filelist.index(self.fullname)

            self.loadImage()

    def ImplNextImage(self):
        pass
        
    def ImplPreviousImage(self):
        pass

    def ImplNextImageLocal(self):
        try:
            self.currentfileid = (self.currentfileid + 1) % len(self.filelist)
            self.filename = os.path.basename(self.filelist[self.currentfileid])
            self.dirname = os.path.dirname(self.filelist[self.currentfileid])
            self.fullname = os.path.join(self.dirname, self.filename)
            self.loadImage()
        except ZeroDivisionError:
            pass

    def ImplPreviousImageLocal(self):
        try:
            self.currentfileid = (self.currentfileid - 1) % len(self.filelist)
            self.filename = os.path.basename(self.filelist[self.currentfileid])
            self.dirname = os.path.dirname(self.filelist[self.currentfileid])
            self.fullname = os.path.join(self.dirname, self.filename)
            self.loadImage()
        except ZeroDivisionError:
            pass


def parseCLIparameters():
    if len(sys.argv) > 1:
        input = os.path.abspath(sys.argv[1])
        if os.path.isfile(input):
            frame.ImplOpenDirFile(os.path.dirname(input), os.path.basename(input))
        elif os.path.isdir(input):
            frame.ImplOpenDirFile(os.path.dirname(input+'/'), '')



if __name__ == '__main__':
    myApp = wx.App()
    frame = MainWindow(None, -1, 'Photo Private Metadata Viewer (alpha)', size=(800,600))
    parseCLIparameters()
    myApp.MainLoop()
