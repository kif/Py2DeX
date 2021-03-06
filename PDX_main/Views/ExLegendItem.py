# -*- coding: utf8 -*-
# Py2DeX - GUI program for fast processing of 2D X-ray data
# Copyright (C) 2014  Clemens Prescher (clemens.prescher@gmail.com)
# GSECARS, University of Chicago
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
__author__ = 'Clemens Prescher'

from pyqtgraph.graphicsItems.GraphicsWidget import GraphicsWidget
from pyqtgraph.graphicsItems.LabelItem import LabelItem
from pyqtgraph.Qt import QtGui, QtCore
from pyqtgraph import functions as fn
from pyqtgraph.Point import Point
from pyqtgraph.graphicsItems.ScatterPlotItem import ScatterPlotItem, drawSymbol
from pyqtgraph.graphicsItems.PlotDataItem import PlotDataItem
from pyqtgraph.graphicsItems.GraphicsWidgetAnchor import GraphicsWidgetAnchor

__all__ = ['LegendItem']


class LegendItem(GraphicsWidget, GraphicsWidgetAnchor):
    """
    Displays a legend used for describing the contents of a plot.
    LegendItems are most commonly created by calling PlotItem.addLegend().

    Note that this item should not be added directly to a PlotItem. Instead,
    Make it a direct descendant of the PlotItem::

        legend.setParentItem(plotItem)

    Codebase was copied from original pyqtgraph legenditem code. It had to be included here,
    because the Pull request for additional features needed has not been worked through yet.

    """

    def __init__(self, size=None, offset=None, horSpacing=25, verSpacing=0, box=True):
        """
        ==============  ===============================================================
        **Arguments:**
        size            Specifies the fixed size (width, height) of the legend. If
                        this argument is omitted, the legend will autimatically resize
                        to fit its contents.
        offset          Specifies the offset position relative to the legend's parent.
                        Positive values offset from the left or top; negative values
                        offset from the right or bottom. If offset is None, the
                        legend must be anchored manually by calling anchor() or
                        positioned by calling setPos().
        horSpacing      Specifies the spacing between the line symbol and the label.
        verSpacing      Specifies the spacing between individual entries of the legend
                        vertically. (Can also be negative to have them really close)
        box             Specifies if the Legend should will be drawn with a rectangle
                        around it.
        ==============  ===============================================================

        """

        GraphicsWidget.__init__(self)
        GraphicsWidgetAnchor.__init__(self)
        self.setFlag(self.ItemIgnoresTransformations)
        self.layout = QtGui.QGraphicsGridLayout()
        self.layout.setVerticalSpacing(verSpacing)
        self.layout.setHorizontalSpacing(horSpacing)
        self.setLayout(self.layout)
        self.legendItems = []
        self.plotItems = []
        self.size = size
        self.offset = offset
        self.box = box
        #A numItems variable needs to be introduced, because chaining removeItem and addItem function in random order,
        # will otherwise lead to writing in the same layout row. Idea here is to always insert LabelItems on larger
        # and larger layout row numbers. The GraphicsGridlayout item will not care about empty rows.
        self.numItems = 0
        if size is not None:
            self.setGeometry(QtCore.QRectF(0, 0, self.size[0], self.size[1]))

    def setParentItem(self, p):
        ret = GraphicsWidget.setParentItem(self, p)
        if self.offset is not None:
            offset = Point(self.offset)
            anchorx = 1 if offset[0] <= 0 else 0
            anchory = 1 if offset[1] <= 0 else 0
            anchor = (anchorx, anchory)
            self.anchor(itemPos=anchor, parentPos=anchor, offset=offset)
        return ret

    def addItem(self, item, name):
        """
        Add a new entry to the legend.

        ==============  ========================================================
        **Arguments:**
        item            A PlotDataItem from which the line and point style
                        of the item will be determined or an instance of
                        ItemSample (or a subclass), allowing the item display
                        to be customized.
        title           The title to display for this item. Simple HTML allowed.
        ==============  ========================================================
        """

        # get item color
        pen = fn.mkPen(item.opts['pen'])
        color = pen.color()
        color_str = color.name()

        #create label with same color
        label = LabelItem()
        label.setAttr('color', str(color_str[1:]))
        label.setText(name)

        if isinstance(item, ItemSample):
            sample = item
        else:
            sample = ItemSample(item)

        self.legendItems.append((sample, label))
        self.plotItems.append(item)
        self.layout.addItem(sample, self.numItems, 0)
        self.layout.addItem(label, self.numItems, 1)
        self.numItems += 1
        self.updateSize()

    def removeItem(self, name):
        """
        Removes one item from the legend.

        ==============  ========================================================
        **Arguments:**
        name            Either the name displayed for this item or the originally
                        added item object.
        ==============  ========================================================
        """
        # Thanks, Ulrich!
        # cycle for a match
        for sample, label in self.legendItems:
            if label.text == name:  # hit
                self.legendItems.remove((sample, label))  # remove from itemlist
                self.layout.removeItem(sample)  # remove from layout
                sample.close()  # remove from drawing
                self.layout.removeItem(label)
                label.close()
                self.updateSize()  # redraq box
                return

        for ind, item in enumerate(self.plotItems):
            if item == name:
                sample, label = self.legendItems[ind]
                self.plotItems.remove(item)
                self.layout.removeItem(sample)
                sample.close()
                self.layout.removeItem(label)
                label.close()
                self.legendItems.remove((sample, label))
                self.updateSize()

    def updateSize(self):
        if self.size is not None:
            return
        #we only need to set geometry to 0, as now the horizontal and vertical spacing is set in
        # __init__.
        self.setGeometry(0, 0, 0, 0)

    def boundingRect(self):
        return QtCore.QRectF(0, 0, self.width(), self.height())

    def paint(self, p, *args):
        if self.box:
            p.setPen(fn.mkPen(255, 255, 255, 100))
            p.setBrush(fn.mkBrush(100, 100, 100, 50))
            p.drawRect(self.boundingRect())

    def hoverEvent(self, ev):
        ev.acceptDrags(QtCore.Qt.LeftButton)

    def mouseDragEvent(self, ev):
        if ev.button() == QtCore.Qt.LeftButton:
            dpos = ev.pos() - ev.lastPos()
            self.autoAnchor(self.pos() + dpos)


class ItemSample(GraphicsWidget):
    """ Class responsible for drawing a single item in a LegendItem (sans label).

    This may be subclassed to draw custom graphics in a Legend.
    """
    ## Todo: make this more generic; let each item decide how it should be represented.
    def __init__(self, item):
        GraphicsWidget.__init__(self)
        self.item = item

    def boundingRect(self):
        return QtCore.QRectF(0, 0, 20, 20)

    def paint(self, p, *args):
        #p.setRenderHint(p.Antialiasing)  # only if the data is antialiased.
        opts = self.item.opts

        if opts.get('fillLevel', None) is not None and opts.get('fillBrush', None) is not None:
            p.setBrush(fn.mkBrush(opts['fillBrush']))
            p.setPen(fn.mkPen(None))
            p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(2, 18), QtCore.QPointF(18, 2), QtCore.QPointF(18, 18)]))

        if not isinstance(self.item, ScatterPlotItem):
            p.setPen(fn.mkPen(opts['pen']))
            p.drawLine(2, 18, 18, 2)

        symbol = opts.get('symbol', None)
        if symbol is not None:
            if isinstance(self.item, PlotDataItem):
                opts = self.item.scatter.opts

            pen = fn.mkPen(opts['pen'])
            brush = fn.mkBrush(opts['brush'])
            size = opts['size']

            p.translate(10, 10)
            path = drawSymbol(p, symbol, size, pen, brush)

