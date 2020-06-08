# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'SettingsDialog.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(268, 411)
        self.autoconnect = QtWidgets.QCheckBox(Dialog)
        self.autoconnect.setGeometry(QtCore.QRect(10, 10, 251, 21))
        self.autoconnect.setObjectName("autoconnect")
        self.hint = QtWidgets.QLabel(Dialog)
        self.hint.setGeometry(QtCore.QRect(10, 50, 59, 15))
        self.hint.setObjectName("hint")
        self.saveslist = QtWidgets.QListWidget(Dialog)
        self.saveslist.setGeometry(QtCore.QRect(10, 70, 251, 121))
        self.saveslist.setObjectName("saveslist")
        self.rmbutton = QtWidgets.QPushButton(Dialog)
        self.rmbutton.setGeometry(QtCore.QRect(10, 192, 251, 31))
        self.rmbutton.setObjectName("rmbutton")
        self.image = QtWidgets.QLabel(Dialog)
        self.image.setGeometry(QtCore.QRect(10, 230, 251, 171))
        self.image.setText("")
        self.image.setOpenExternalLinks(True)
        self.image.setObjectName("image")

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.autoconnect.setText(_translate("Dialog", "Skip connect screen"))
        self.hint.setText(_translate("Dialog", "Saves"))
        self.rmbutton.setText(_translate("Dialog", "Remove save"))
