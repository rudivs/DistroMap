# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DistroMap
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
# Import the PyQt and QGIS libraries
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
# Initialize Qt resources from file resources.py
import resources_rc
# Import the code for the dialog
from distromapdialog import DistroMapDialog

def getLayerFromId (uniqueId):
    return QgsMapLayerRegistry.instance().mapLayer(uniqueId)

class DistroMap:

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = QFileInfo(QgsApplication.qgisUserDbFilePath()).path() + "/python/plugins/distromap"
        # initialize locale
        localePath = ""
        locale = QSettings().value("locale/userLocale").toString()[0:2]
        
        #self.layerdict = {}

        if QFileInfo(self.plugin_dir).exists():
            localePath = self.plugin_dir + "/i18n/distromap_" + locale + ".qm"

        if QFileInfo(localePath).exists():
            self.translator = QTranslator()
            self.translator.load(localePath)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = DistroMapDialog()

    def initGui(self):
        # Create action that will start plugin configuration
        self.action = QAction(
            QIcon(":/plugins/distromap/icon.png"),
            u"Distribution Map Creator...", self.iface.mainWindow())
        # connect the action to the run method
        QObject.connect(self.action, SIGNAL("triggered()"), self.run)

        # Add toolbar button and menu item
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu(u"&Distribution Map Creator", self.action)

    def unload(self):
        # Remove the plugin menu item and icon
        self.iface.removePluginMenu(u"&Distribution Map Creator", self.action)
        self.iface.removeToolBarIcon(self.action)
    
    def loadTaxonFields(self):
        self.dlg.ui.comboTaxonField.clear()
        #QMessageBox.information(self.iface.mainWindow(),'Current Item Data', str(self.dlg.ui.comboLocalities.currentItemData()), QMessageBox.Ok) #DEBUG
        try:
            layer=getLayerFromId(self.dlg.ui.comboLocalities.currentItemData())
        except: #Crashes without valid shapefiles
            return
        provider=layer.dataProvider()
        try: # this function will crash on raster layers
            fieldmap=provider.fieldNameMap()
        except:
            return
        for (name,index) in fieldmap.iteritems():
            self.dlg.ui.comboTaxonField.addItem(name)

    def loadOutDir(self):
        newname = QFileDialog.getExistingDirectory(None, QString.fromLocal8Bit("Output Maps Directory"),
            self.dlg.ui.leOutDir.displayText())

        if newname != None:
            self.dlg.ui.leOutDir.setText(QString(newname))


    # run method that performs all the real work
    def run(self):
       
        # first clear combo boxes so they don't get duplicate entries:
        self.dlg.ui.comboBase.clear()
        self.dlg.ui.comboSecondary.clear()
        self.dlg.ui.comboSurface.clear()
        self.dlg.ui.comboLocalities.clear()
        self.dlg.ui.comboGrid.clear()
        
        # populate combo boxes:
        self.dlg.ui.comboSecondary.addItem("None")
        self.dlg.ui.comboSurface.addItem("None")
        for layer in self.iface.mapCanvas().layers():
            self.dlg.ui.comboBase.addItem(layer.name(),QVariant(layer.id()))
            self.dlg.ui.comboSecondary.addItem(layer.name(),QVariant(layer.id()))
            self.dlg.ui.comboSurface.addItem(layer.name(),QVariant(layer.id()))
            #vector only layers:
            if type(layer).__name__ == "QgsVectorLayer":
                self.dlg.ui.comboLocalities.addItem(layer.name(),QVariant(layer.id()))
                self.dlg.ui.comboGrid.addItem(layer.name(),QVariant(layer.id()))
        self.loadTaxonFields()
        
        # define the signal connectors
        QObject.connect(self.dlg.ui.comboLocalities,SIGNAL('currentIndexChanged (int)'),self.loadTaxonFields)
        QObject.connect(self.dlg.ui.btnBrowse,SIGNAL('clicked()'),self.loadOutDir)
        
        # actions
 
        # show the dialog
        self.dlg.show()       
        
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result == 1:
            # do something useful (delete the line containing pass and
            # substitute with your code)
            pass
