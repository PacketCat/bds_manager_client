# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'PackWidget.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(274, 71)
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setContentsMargins(2, 2, 2, 2)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.packName = QtWidgets.QLabel(Form)
        self.packName.setObjectName("packName")
        self.verticalLayout.addWidget(self.packName)
        self.packVer = QtWidgets.QLabel(Form)
        self.packVer.setTextFormat(QtCore.Qt.RichText)
        self.packVer.setObjectName("packVer")
        self.verticalLayout.addWidget(self.packVer)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.action = QtWidgets.QPushButton(Form)
        self.action.setMinimumSize(QtCore.QSize(10, 0))
        self.action.setFlat(True)
        self.action.setObjectName("action")
        self.horizontalLayout.addWidget(self.action)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.unimport = QtWidgets.QPushButton(Form)
        self.unimport.setFlat(True)
        self.unimport.setObjectName("unimport")
        self.horizontalLayout.addWidget(self.unimport)
        self.horizontalLayout.setStretch(0, 2)
        self.horizontalLayout.setStretch(1, 7)
        self.horizontalLayout.setStretch(2, 6)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.verticalLayout.setStretch(0, 1)
        self.verticalLayout.setStretch(1, 1)
        self.verticalLayout.setStretch(2, 2)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.packName.setText(_translate("Form", "<html><head/><body><p><span style=\" font-size:11pt; font-weight:600;\">PackName</span></p></body></html>"))
        self.packVer.setText(_translate("Form", "<html><head/><body><p>packVer</p></body></html>"))
        self.action.setText(_translate("Form", ">"))
        self.unimport.setText(_translate("Form", "Remove"))
