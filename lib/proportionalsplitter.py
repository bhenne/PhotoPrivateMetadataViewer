# -*- coding:utf-8 -*0

'''
provenance:
http://wiki.wxpython.org/index.cgi/ProportionalSplitterWindow
'''

import wx

class ProportionalSplitter(wx.SplitterWindow):
        def __init__(self,parent, id = -1, proportion=0.66, size = wx.DefaultSize, *a, **k):
                wx.SplitterWindow.__init__(self,parent,id,wx.Point(0, 0),size, *a, **k)
                self.SetMinimumPaneSize(10) #the minimum size of a pane.
                self.proportion = proportion
                if not 0 < self.proportion < 1:
                        raise ValueError, "proportion value for ProportionalSplitter must be between 0 and 1."
                self.ResetSash()
                self.Bind(wx.EVT_SIZE, self.OnReSize)
                self.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED, self.OnSashChanged, id=id)
                ##hack to set sizes on first paint event
                self.Bind(wx.EVT_PAINT, self.OnPaint)
                self.firstpaint = True

        def SplitHorizontally(self, win1, win2):
                if self.GetParent() is None: return False
                return wx.SplitterWindow.SplitHorizontally(self, win1, win2,
                                                           int(round(self.GetParent().GetSize().GetHeight() * self.proportion)))

        def SplitVertically(self, win1, win2):
                if self.GetParent() is None: return False
                return wx.SplitterWindow.SplitVertically(self, win1, win2,
                                                         int(round(self.GetParent().GetSize().GetWidth() * self.proportion)))

        def GetExpectedSashPosition(self):
                if self.GetSplitMode() == wx.SPLIT_HORIZONTAL:
                        tot = max(self.GetMinimumPaneSize(),self.GetParent().GetClientSize().height)
                else:
                        tot = max(self.GetMinimumPaneSize(),self.GetParent().GetClientSize().width)
                return int(round(tot * self.proportion))

        def ResetSash(self):
                self.SetSashPosition(self.GetExpectedSashPosition())

        def OnReSize(self, event):
                "Window has been resized, so we need to adjust the sash based on self.proportion."
                self.ResetSash()
                event.Skip()

        def OnSashChanged(self, event):
                "We'll change self.proportion now based on where user dragged the sash."
                pos = float(self.GetSashPosition())
                if self.GetSplitMode() == wx.SPLIT_HORIZONTAL:
                        tot = max(self.GetMinimumPaneSize(),self.GetParent().GetClientSize().height)
                else:
                        tot = max(self.GetMinimumPaneSize(),self.GetParent().GetClientSize().width)
                self.proportion = pos / tot
                event.Skip()

        def OnPaint(self,event):
                if self.firstpaint:
                        if self.GetSashPosition() != self.GetExpectedSashPosition():
                                self.ResetSash()
                        self.firstpaint = False
                event.Skip()

# Example window with two splitters:
# _________________
# |          |    |
# |          |    |
# |__________|    |
# |          |    |
# |          |    |
# |__________|____|

#from ProportionalSplitter import ProportionalSplitter

class MainFrame(wx.Frame):

        def __init__(self,parent,id,title,position,size):
                wx.Frame.__init__(self, parent, id, title, position, size)

                ## example code that would be in your window's init handler:

                ## create splitters:
                self.split1 = ProportionalSplitter(self,-1, 0.66)
                self.split2 = ProportionalSplitter(self.split1,-1, 0.50)
                self.split3 = ProportionalSplitter(self.split1,-1, 0.50)

                ## create controls to go in the splitter windows...
                self.toprightpanel = wx.Notebook(self.split3, wx.ID_ANY)
                self.topleftpanel = wx.Notebook(self.split2, wx.ID_ANY)
                self.bottomleftpanel = wx.Notebook(self.split2, wx.ID_ANY)
                
                self.bottomrightpanel = wx.Notebook(self.split3, wx.ID_ANY)
                ## add your controls to the splitters:
                self.split1.SplitVertically(self.split2, self.split3)
                self.split2.SplitHorizontally(self.topleftpanel, self.bottomleftpanel)
                self.split3.SplitHorizontally(self.toprightpanel, self.bottomrightpanel)

if __name__ == '__main__':
        app = wx.App()
        frame = MainFrame(None, wx.ID_ANY, 'ProportionalSplitter', (0, 0), (800, 600))
        frame.Centre()
        frame.Show()
        app.MainLoop()
