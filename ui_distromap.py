# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_distromap.ui'
#
# Created: Tue Feb 19 15:18:14 2013
#      by: PyQt4 UI code generator 4.9.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_DistroMap(object):
    def setupUi(self, DistroMap):
        DistroMap.setObjectName(_fromUtf8("DistroMap"))
        DistroMap.resize(400, 300)
        self.buttonBox = QtGui.QDialogButtonBox(DistroMap)
        self.buttonBox.setGeometry(QtCore.QRect(30, 240, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))

        self.retranslateUi(DistroMap)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), DistroMap.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), DistroMap.reject)
        QtCore.QMetaObject.connectSlotsByName(DistroMap)

    def retranslateUi(self, DistroMap):
        DistroMap.setWindowTitle(QtGui.QApplication.translate("DistroMap", "DistroMap", None, QtGui.QApplication.UnicodeUTF8))

