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
from __future__ import absolute_import
# Import the PyQt and QGIS libraries
from builtins import str
from builtins import object
from qgis.PyQt.QtCore import (QCoreApplication, QSettings, QTranslator,
                              QFileInfo, QSize)
from qgis.PyQt.QtWidgets import (QMessageBox, QDialog, QFileDialog,
                                 QColorDialog, QAction, QWidget)
from qgis.PyQt.QtGui import (QIcon, QImage, QColor, QPainter)
from qgis.core import (QgsApplication, QgsMessageLog, QgsProject,
                       QgsSpatialIndex, QgsFeature, QgsGeometry,
                       QgsFeatureRequest, QgsRectangle, QgsMapSettings,
                       QgsVectorLayer, QgsMapRendererCustomPainterJob, QgsCsException,
                       QgsExpression)
# Initialize Qt resources from file resources.py
from . import resources_rc
# Import the code for the dialog
from .distromapdialog import DistroMapDialog, Features
import os
import tempfile

log = lambda m: QgsMessageLog.logMessage(m,'Distribution Map Generator')

def getLayerFromId (uniqueId):
    return QgsProject.instance().mapLayer(uniqueId)

class DistroMap(object):

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = QFileInfo(QgsApplication.qgisSettingsDirPath()).path() + "/python/plugins/distromap"
        # initialize locale
        localePath = ""
        locale = QSettings().value("locale/userLocale")[0:2]

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
        self.TAXON_FIELD_INDEX = self.dlg.ui.comboTaxonField.currentItemData()[0]
        self.GRID_LAYER = self.dlg.ui.comboGrid.currentItemData()
        self.X_MIN = float(self.dlg.ui.leMinX.text())
        self.Y_MIN = float(self.dlg.ui.leMinY.text())
        self.X_MAX = float(self.dlg.ui.leMaxX.text())
        self.Y_MAX = float(self.dlg.ui.leMaxY.text())
        self.OUT_WIDTH = self.dlg.ui.spnOutWidth.value()
        self.OUT_HEIGHT = self.dlg.ui.spnOutHeight.value()
        self.OUT_DIR = self.dlg.ui.leOutDir.text()

        try:
            self.getUniqueValues()
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

        self.GRID_INDEX = QgsSpatialIndex()
        for feat in getLayerFromId(self.GRID_LAYER).getFeatures():
            self.GRID_INDEX.insertFeature(feat)

        if reply == QMessageBox.Yes:
            try:
                self.process()
            except QgsCsException:
                return
            except Exception as ex:
                log(ex)
                return
            QMessageBox.information(self.dlg,"Distribution Map Generator",
                "Map processing complete.")
            self.dlg.ui.progressBar.setValue(0)
            QDialog.accept(self.dlg)
        else:
            return

    def initGui(self):
        # Create action that will start plugin configuration
        self.action = QAction(
            QIcon(self.plugin_dir + "/icon.svg"),
            u"Distribution Map Generator...", self.iface.mainWindow())
        # connect the action to the run method
        self.action.triggered.connect(self.run)
        self.dlg.ui.buttonBox.accepted.connect(self.confirm)

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
        except AttributeError: #Crashes without valid shapefiles
            log("Could not access the localities layer. Is it a valid vector layer?")
            return
        try:
            fieldmap=provider.fieldNameMap()
            for (name,index) in fieldmap.items():
                self.dlg.ui.comboTaxonField.addItem(name,index)
        except:
            log("Could not load the field names for the localities layer.")

    def loadOutDir(self):
        #newname = QFileDialog.getExistingDirectory(None, "Output Maps Directory", self.dlg.ui.leOutDir.displayText())
        newname = QFileDialog.getExistingDirectory(None, "Output Maps Directory")

        if newname != None:
            self.dlg.ui.leOutDir.setText(newname)

    def getCurrentExtent(self):
        extent = self.iface.mapCanvas().extent()
        # {"{0:.6f}".format() shows the float with 6 decimal places
        self.dlg.ui.leMinX.setText(str("{0:.6f}".format(extent.xMinimum())))
        self.dlg.ui.leMinY.setText(str("{0:.6f}".format(extent.yMinimum())))
        self.dlg.ui.leMaxX.setText(str("{0:.6f}".format(extent.xMaximum())))
        self.dlg.ui.leMaxY.setText(str("{0:.6f}".format(extent.yMaximum())))

    def getUniqueValues(self):
        layer = getLayerFromId(self.LOCALITIES_LAYER)
        self.UNIQUE_VALUES = layer.dataProvider().uniqueValues(int(self.TAXON_FIELD_INDEX))
        self.UNIQUE_COUNT = len(self.UNIQUE_VALUES)

    def selectByAttribute(self, value):
        layer = getLayerFromId(self.LOCALITIES_LAYER)
        field_index = self.TAXON_FIELD_INDEX
        field_name = layer.fields()[int(field_index)].name()
        selected = []
        filter = QgsExpression.createFieldEqualityExpression(field_name, str(value))
        request = QgsFeatureRequest().setFilterExpression(filter)
        request.setSubsetOfAttributes([])
        for feature in layer.getFeatures(request):
            selected.append(feature.id())
        layer.selectByIds(selected)

    def selectByLocation(self):
        gridLayer = getLayerFromId(self.GRID_LAYER)
        selectLayer = getLayerFromId(self.LOCALITIES_LAYER)
        if gridLayer.crs() != selectLayer.crs():
            QMessageBox.information(self.dlg,"Distribution Map Generator",
                "Localities layer and grid layers must have the same projection.")
            raise QgsCsException("Localities layer and grid layers must have the same projection.")

        selectedSet = []
        feats = selectLayer.selectedFeatures()
        for f in feats:
            geom = QgsGeometry(f.geometry())
            intersects = self.GRID_INDEX.intersects(geom.boundingBox())
            for i in intersects:
                request = QgsFeatureRequest().setFilterFid(i)
                feat = next(gridLayer.getFeatures(request))
                tmpGeom = QgsGeometry( feat.geometry() )
                if geom.intersects(tmpGeom):
                    selectedSet.append(feat.id())
        gridLayer.selectByIds(selectedSet)

    def saveSelected(self):
        gridLayer = getLayerFromId(self.GRID_LAYER)

        # create memory layer
        outputLayer = QgsVectorLayer("Polygon", "taxon", "memory")
        outProvider = outputLayer.dataProvider()

        # add features
        outGrids = gridLayer.selectedFeatures()
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

        # create layer set
        baseLayer = getLayerFromId(self.BASE_LAYER)
        if self.TAXON_GRID_LAYER.crs() != baseLayer.crs():
            QMessageBox.information(self.dlg,"Distribution Map Generator",
                "All layers must have the same projection.")
            raise QgsCsException("All layers must have the same projection.")
        baseCrs = baseLayer.crs()
        if self.SECONDARY_LAYER != "None":
            secondaryLayer = getLayerFromId(self.SECONDARY_LAYER)
            if secondaryLayer.crs() != baseLayer.crs():
                QMessageBox.information(self.dlg,"Distribution Map Generator",
                    "All layers must have the same projection.")
                raise QgsCsException("All layers must have the same projection.")
        else:
            secondaryLayer = None
        if self.SURFACE_LAYER != "None":
            surfaceLayer = getLayerFromId(self.SURFACE_LAYER)
            if surfaceLayer.crs() != baseLayer.crs():
                QMessageBox.information(self.dlg,"Distribution Map Generator",
                    "All layers must have the same projection.")
                raise QgsCsException("All layers must have the same projection.")
        else:
            surfaceLayer = None

        lst = []
        lst.append(self.TAXON_GRID_LAYER)
        if self.SURFACE_LAYER != "None":
            lst.append(surfaceLayer)
        if self.SECONDARY_LAYER != "None":
            lst.append(secondaryLayer)
        lst.append(baseLayer)

        ms = QgsMapSettings()
        ms.setLayers(lst)
        ms.setBackgroundColor(self.BACKGROUND_COLOUR)

        # set extent (xmin,ymin,xmax,ymax)
        rect = QgsRectangle(self.X_MIN,self.Y_MIN,self.X_MAX,self.Y_MAX)
        ms.setExtent(rect)

        # set output size
        outputSize = QSize(self.OUT_WIDTH,self.OUT_HEIGHT)
        ms.setOutputSize(outputSize)

        # create painter
        p = QPainter()
        p.setRenderHint(QPainter.Antialiasing)

        # create image (dimensions 325x299)
        img = QImage(outputSize, QImage.Format_ARGB32_Premultiplied)
        p.begin(img)

        # do the rendering
        r = QgsMapRendererCustomPainterJob(ms, p)

        r.start()
        r.waitForFinished()
        p.end()

        # save image
        outdir = self.OUT_DIR
        img.save(outdir+os.sep+str(str(taxon))+".png","png")

    def process(self):
        self.dlg.ui.progressBar.setMaximum(len(self.UNIQUE_VALUES))
        # process all unique taxa
        getLayerFromId(self.LOCALITIES_LAYER).selectByIds([])
        # use global projection
        #oldValidation = QSettings().value( "/Projections/defaultBehavior", "useGlobal", type=str )
        #QSettings().setValue( "/Projections/defaultBehavior", "useGlobal" )
        for taxon in self.UNIQUE_VALUES:
            self.selectByAttribute(taxon)
            self.selectByLocation()
            self.saveSelected()
            #load newly created memory layer
            QgsProject.instance().addMapLayer(self.TAXON_GRID_LAYER)
            try:
                self.printMap(taxon)
            except QgsCsException:
                #unload memory layer
                QgsProject.instance().removeMapLayers([self.TAXON_GRID_LAYER.id()])
                self.TAXON_GRID_LAYER = None
                getLayerFromId(self.LOCALITIES_LAYER).removeSelection()
                getLayerFromId(self.GRID_LAYER).removeSelection()
                raise
            #unload memory layer
            QgsProject.instance().removeMapLayers([self.TAXON_GRID_LAYER.id()])
            self.TAXON_GRID_LAYER = None
            self.dlg.ui.progressBar.setValue(self.dlg.ui.progressBar.value()+1)
        #restore saved default projection setting
        #QSettings().setValue( "/Projections/defaultBehaviour", oldValidation )
        #clear selection
        getLayerFromId(self.LOCALITIES_LAYER).removeSelection()
        getLayerFromId(self.GRID_LAYER).removeSelection()

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
            self.dlg.ui.comboBase.addItem(layer.name(),layer.id())
            self.dlg.ui.comboSecondary.addItem(layer.name(),layer.id())
            self.dlg.ui.comboSurface.addItem(layer.name(),layer.id())
            #vector only layers:
            if type(layer).__name__ == "QgsVectorLayer":
                self.dlg.ui.comboLocalities.addItem(layer.name(),layer.id())
                self.dlg.ui.comboGrid.addItem(layer.name(),layer.id())
        self.loadTaxonFields()

        # define the signal connectors
        #QObject.connect(self.dlg.ui.comboLocalities,SIGNAL('currentIndexChanged (int)'),self.loadTaxonFields)
        self.dlg.ui.comboLocalities.currentIndexChanged.connect(self.loadTaxonFields)
        #QObject.connect(self.dlg.ui.btnBrowse,SIGNAL('clicked()'),self.loadOutDir)
        self.dlg.ui.btnBrowse.clicked.connect(self.loadOutDir)
        #QObject.connect(self.dlg.ui.btnExtent,SIGNAL('clicked()'),self.getCurrentExtent)
        self.dlg.ui.btnExtent.clicked.connect(self.getCurrentExtent)
        #QObject.connect(self.dlg.ui.btnColour,SIGNAL('clicked()'),self.setBackgroundColour)
        self.dlg.ui.btnColour.clicked.connect(self.setBackgroundColour)

        # show the dialog
        self.dlg.show()

        # Run the dialog event loop
        result = self.dlg.exec_()
