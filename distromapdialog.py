# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DistroMapDialog
                                 A QGIS plugin
 Creates simple distribution maps based on point localities and a polygon grid layer.
                             -------------------
        begin                : 2013-02-19
        copyright            : (C) 2013 by Rudi von Staden
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

from PyQt4 import QtCore, QtGui
from ui_distromap import Ui_DistroMap
# create the dialog for zoom to point


class DistroMapDialog(QtGui.QDialog):
    def __init__(self):
        QtGui.QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.ui = Ui_DistroMap()
        self.ui.setupUi(self)
