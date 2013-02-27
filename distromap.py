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
from distromapdialog import DistroMapDialog, Features
import os
import tempfile

def getLayerFromId (uniqueId):
    return QgsMapLayerRegistry.instance().mapLayer(uniqueId)

def features(layer):
    return Features(layer)

class DistroMap:

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = QFileInfo(QgsApplication.qgisUserDbFilePath()).path() + "/python/plugins/distromap"
        # initialize locale
        localePath = ""
        locale = QSettings().value("locale/userLocale").toString()[0:2]

        if QFileInfo(self.plugin_dir).exists():
            localePath = self.plugin_dir + "/i18n/distromap_" + locale + ".qm"

        if QFileInfo(localePath).exists():
            self.translator = QTranslator()
            self.translator.load(localePath)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = DistroMapDialog()

    def confirm(self):
        # runs when OK button is pressed
        # initialise input parameters
        self.BASE_LAYER = self.dlg.ui.comboBase.currentItemData()
        self.SECONDARY_LAYER = self.dlg.ui.comboSecondary.currentItemData()
        self.SURFACE_LAYER = self.dlg.ui.comboSurface.currentItemData()
        self.LOCALITIES_LAYER = self.dlg.ui.comboLocalities.currentItemData()
        self.TAXON_FIELD_INDEX = self.dlg.ui.comboTaxonField.currentItemData().toInt()[0]
        self.GRID_LAYER = self.dlg.ui.comboGrid.currentItemData()
        self.X_MIN = self.dlg.ui.leMinX.text().toFloat()[0]
        self.Y_MIN = self.dlg.ui.leMinY.text().toFloat()[0]
        self.X_MAX = self.dlg.ui.leMaxX.text().toFloat()[0]
        self.Y_MAX = self.dlg.ui.leMaxY.text().toFloat()[0]
        self.OUT_WIDTH = self.dlg.ui.spnOutWidth.value()
        self.OUT_HEIGHT = self.dlg.ui.spnOutHeight.value()
        self.OUT_DIR = self.dlg.ui.leOutDir.text()
        
        # get list of unique values
        try:
            self.getUniqueValues()  #output is of type QVariant: use value.toString() to process
        except:
            message =  "Could not get unique values from localities layer. "
            message += "Check that the localities layer and taxon identifier "
            message += "field are properly specified."
            QMessageBox.information(self.dlg,"Distribution Map Generator",
                message)
            return

        question =  "This will generate " + str(self.UNIQUE_COUNT)
        question += " maps. Are you sure you want to continue?"
        reply = QMessageBox.question(self.dlg,'Distribution Map Generator', 
            question, 
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)

        if reply == QMessageBox.Yes:
            self.process()
            QMessageBox.information(self.dlg,"Distribution Map Generator",
                "Map processing complete.")
            self.dlg.ui.progressBar.setValue(0)
            QDialog.accept(self.dlg)
        else:
            return

    def initGui(self):
        # Create action that will start plugin configuration
        self.action = QAction(
            QIcon(":/plugins/distromap/icon.png"),
            u"Distribution Map Generator...", self.iface.mainWindow())
        # connect the action to the run method
        QObject.connect(self.action, SIGNAL("triggered()"), self.run)
        QObject.connect(self.dlg.ui.buttonBox, SIGNAL("accepted()"), self.confirm)

        # Add toolbar button and menu item
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu(u"&Distribution Map Generator", self.action)
        
        # Set colour for output background colour chooser:
        self.BACKGROUND_COLOUR = QColor(192,192,255)
        self.dlg.ui.frmColour.setStyleSheet("QWidget { background-color: %s }" 
            % self.BACKGROUND_COLOUR.name())

    def unload(self):
        # Remove the plugin menu item and icon
        self.iface.removePluginMenu(u"&Distribution Map Generator", self.action)
        self.iface.removeToolBarIcon(self.action)
    
    def loadTaxonFields(self):
        self.dlg.ui.comboTaxonField.clear()
        try:
            layer=getLayerFromId(self.dlg.ui.comboLocalities.currentItemData())
            provider=layer.dataProvider()
        except: #Crashes without valid shapefiles
            print "Could not access the localities layer. Is it a valid vector layer?"
            return
        try:
            fieldmap=provider.fieldNameMap()
            for (name,index) in fieldmap.iteritems():
                self.dlg.ui.comboTaxonField.addItem(name,index)
        except:
            print "Could not load the field names for the localities layer."

    def loadOutDir(self):
        newname = QFileDialog.getExistingDirectory(None, QString.fromLocal8Bit("Output Maps Directory"),
            self.dlg.ui.leOutDir.displayText())

        if newname != None:
            self.dlg.ui.leOutDir.setText(QString(newname))

    def getCurrentExtent(self):
        extent = self.iface.mapCanvas().extent()
        # {"{0:.6f}".format() shows the float with 6 decimal places
        self.dlg.ui.leMinX.setText(str("{0:.6f}".format(extent.xMinimum())))
        self.dlg.ui.leMinY.setText(str("{0:.6f}".format(extent.yMinimum())))
        self.dlg.ui.leMaxX.setText(str("{0:.6f}".format(extent.xMaximum())))
        self.dlg.ui.leMaxY.setText(str("{0:.6f}".format(extent.yMaximum())))
            
    def getUniqueValues(self):
        layer = getLayerFromId(self.LOCALITIES_LAYER)
        self.UNIQUE_VALUES = layer.dataProvider().uniqueValues(self.TAXON_FIELD_INDEX)
        self.UNIQUE_COUNT = len(self.UNIQUE_VALUES)
    
    def selectByAttribute(self, value):
        layer = getLayerFromId(self.LOCALITIES_LAYER)
        selectindex = self.TAXON_FIELD_INDEX

        readcount = 0
        selected = []
        for feature in layer.getFeatures():
            if unicode(feature.attributes()[selectindex].toString()) == unicode(value.toString()):
                selected.append(feature.id())
        layer.setSelectedFeatures(selected)
        
    def selectByLocation(self):
        inputLayer = getLayerFromId(self.GRID_LAYER)
        selectLayer = getLayerFromId(self.LOCALITIES_LAYER)
        inputProvider = inputLayer.dataProvider()

        index = QgsSpatialIndex()
        feat = QgsFeature()
        for feat in inputLayer.getFeatures():        
            index.insertFeature(feat)
     
        infeat = QgsFeature()
        geom = QgsGeometry()
        selectedSet = []        
        feats = features(selectLayer)
        for feat in feats:
            geom = QgsGeometry(feat.geometry())
            intersects = index.intersects(geom.boundingBox())
            for i in intersects:
                inputLayer.featureAtId(i, infeat, True)
                tmpGeom = QgsGeometry( infeat.geometry() )
                if geom.intersects(tmpGeom):
                    selectedSet.append(infeat.id())
        inputLayer.setSelectedFeatures(selectedSet)
    
    def saveSelected(self):
        inputLayer = getLayerFromId(self.GRID_LAYER)
        provider = inputLayer.dataProvider()

        # create layer
        outputLayer = QgsVectorLayer("Polygon", "taxon", "memory")
        outProvider = outputLayer.dataProvider()

        # add features
        outGrids = features(inputLayer)
        for grid in outGrids:
            outProvider.addFeatures([grid])
        outputLayer.updateExtents()
        self.TAXON_GRID_LAYER = outputLayer

    def setBackgroundColour(self):
        col = QColorDialog.getColor()

        if col.isValid():
            self.BACKGROUND_COLOUR = col
            self.dlg.ui.frmColour.setStyleSheet("QWidget { background-color: %s }"
                % self.BACKGROUND_COLOUR.name())

    def printMap(self,taxon):
        # copy style from grid layer to output layer
        outstyle = tempfile.gettempdir() + os.sep + "output.qml"
        getLayerFromId(self.GRID_LAYER).saveNamedStyle(outstyle)
        self.TAXON_GRID_LAYER.loadNamedStyle(outstyle)
        
        # create image (dimensions 325x299)
        img = QImage(QSize(self.OUT_WIDTH,self.OUT_HEIGHT), QImage.Format_ARGB32_Premultiplied)

        # set image's background color
        color = self.BACKGROUND_COLOUR
        img.fill(color.rgb())

        # create painter
        p = QPainter()
        p.begin(img)
        p.setRenderHint(QPainter.Antialiasing)

        render = QgsMapRenderer()

        # create layer set
        baseLayer = getLayerFromId(self.BASE_LAYER)
        if self.SECONDARY_LAYER != None:
            secondaryLayer = getLayerFromId(self.SECONDARY_LAYER)
        else:
            secondaryLayer = None
        if self.SURFACE_LAYER != None:
            surfaceLayer = getLayerFromId(self.SURFACE_LAYER)
        else:
            surfaceLayer = None
        
        lst = []
        lst.append(self.TAXON_GRID_LAYER.id())
        if self.SURFACE_LAYER != unicode(""):
            lst.append(self.SURFACE_LAYER)
        if self.SECONDARY_LAYER != unicode(""):
            lst.append(self.SECONDARY_LAYER)
        lst.append(self.BASE_LAYER)
        
        render.setLayerSet(lst)

        # set extent (xmin,ymin,xmax,ymax)
        rect = QgsRectangle(self.X_MIN,self.Y_MIN,self.X_MAX,self.Y_MAX)
        render.setExtent(rect)

        # set output size
        render.setOutputSize(img.size(), img.logicalDpiX())

        # do the rendering
        render.render(p)
        p.end()
        
        # save image
        outdir = self.OUT_DIR
        img.save(outdir+os.sep+unicode(taxon.toString())+".png","png")

    def process(self):        
        self.dlg.ui.progressBar.setMaximum(len(self.UNIQUE_VALUES))
        # process all unique taxa
        getLayerFromId(self.LOCALITIES_LAYER).setSelectedFeatures([])
        for taxon in self.UNIQUE_VALUES:
            self.selectByAttribute(taxon)
            self.selectByLocation()
            self.saveSelected()
            #load newly created memory layer
            QgsMapLayerRegistry.instance().addMapLayer(self.TAXON_GRID_LAYER)
            self.printMap(taxon)
            #unload memory layer
            QgsMapLayerRegistry.instance().removeMapLayers([self.TAXON_GRID_LAYER.id()])
            self.TAXON_GRID_LAYER = None
            self.dlg.ui.progressBar.setValue(self.dlg.ui.progressBar.value()+1)        

    # run method that performs all the real work
    def run(self):
       
        # first clear combo boxes so they don't get duplicate entries:
        self.dlg.ui.comboBase.clear()
        self.dlg.ui.comboSecondary.clear()
        self.dlg.ui.comboSurface.clear()
        self.dlg.ui.comboLocalities.clear()
        self.dlg.ui.comboGrid.clear()
        
        # populate combo boxes:
        self.dlg.ui.comboSecondary.addItem("None",None)
        self.dlg.ui.comboSurface.addItem("None",None)
        
       
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
        QObject.connect(self.dlg.ui.btnExtent,SIGNAL('clicked()'),self.getCurrentExtent)
        QObject.connect(self.dlg.ui.btnColour,SIGNAL('clicked()'),self.setBackgroundColour)
        
        # show the dialog
        self.dlg.show()       
        
        # Run the dialog event loop
        result = self.dlg.exec_()
                    
