# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DistroMapDialog
                                 A QGIS plugin
 Creates simple distribution maps based on point localities and a polygon grid layer.
                             -------------------
        begin                : 2013-02-19
        copyright            : (C) 2013 by Rudi von Staden, Victor Olaya
        email                : rudivs@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from builtins import str
from builtins import object
from qgis.core import QgsFeature
from qgis.PyQt.QtWidgets import (QDialog, QComboBox)
from .ui_distromap import Ui_DistroMap

# Add a method to QComboBox to get the current item data
def currentItemData(self):
    return str(self.itemData(self.currentIndex()))

QComboBox.currentItemData = currentItemData

class Features(object):
# Class adapted from version in Sextante QGisLayers driver (by Victor Olaya)

    def __init__(self, layer):
        self.layer = layer
        self.iter = layer.getFeatures()
        self.selection = False;
        self.selected = layer.selectedFeatures()
        if len(self.selected) > 0:
            self.selection = True
            self.idx = 0;

    def __iter__(self):
        return self

    def next(self):
        if self.selection:
            if self.idx < len(self.selected):
                feature = self.selected[self.idx]
                self.idx += 1
                return feature
            else:
                raise StopIteration()
        else:
            if self.iter.isClosed():
                raise StopIteration()
            f = QgsFeature()
            if self.iter.nextFeature(f):
                return f
            else:
                self.iter.close()
                raise StopIteration()

    def __len__(self):
        if self.selection:
            return int(self.layer.selectedFeatureCount())
        else:
            return int(self.layer.featureCount())


class DistroMapDialog(QDialog):
    def __init__(self):
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.ui = Ui_DistroMap()
        self.ui.setupUi(self)
