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
 This script initializes the plugin, making it known to QGIS.
"""


def name():
    return "Distribution Map Creator"


def description():
    return "Creates simple distribution maps based on point localities and a polygon grid layer."


def version():
    return "Version 0.1"


def icon():
    return "icon.png"


def qgisMinimumVersion():
    return "1.8"

def author():
    return "Rudi von Staden"

def email():
    return "rudivs@gmail.com"

def classFactory(iface):
    # load DistroMap class from file DistroMap
    from distromap import DistroMap
    return DistroMap(iface)
