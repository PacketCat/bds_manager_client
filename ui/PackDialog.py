# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'PackDialog.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(400, 291)
        self.gridLayout = QtWidgets.QGridLayout(Dialog)
        self.gridLayout.setObjectName("gridLayout")
        self.frame_2 = QtWidgets.QFrame(Dialog)
        self.frame_2.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_2.setObjectName("frame_2")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.frame_2)
        self.verticalLayout.setObjectName("verticalLayout")
        self.apply = QtWidgets.QPushButton(self.frame_2)
        self.apply.setObjectName("apply")
        self.verticalLayout.addWidget(self.apply)
        self.discard = QtWidgets.QPushButton(self.frame_2)
        self.discard.setObjectName("discard")
        self.verticalLayout.addWidget(self.discard)
        self.changetype = QtWidgets.QPushButton(self.frame_2)
        self.changetype.setObjectName("changetype")
        self.verticalLayout.addWidget(self.changetype)
        self.Import = QtWidgets.QPushButton(self.frame_2)
        self.Import.setObjectName("Import")
        self.verticalLayout.addWidget(self.Import)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.gridLayout.addWidget(self.frame_2, 1, 1, 1, 1)
        self.frame = QtWidgets.QFrame(Dialog)
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.frame)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.hint = QtWidgets.QLabel(self.frame)
        self.hint.setAlignment(QtCore.Qt.AlignCenter)
        self.hint.setObjectName("hint")
        self.horizontalLayout.addWidget(self.hint)
        self.gridLayout.addWidget(self.frame, 0, 0, 1, 3)
        self.globalPacks = QtWidgets.QListWidget(Dialog)
        self.globalPacks.setObjectName("globalPacks")
        self.gridLayout.addWidget(self.globalPacks, 1, 0, 1, 1)
        self.worldPacks = QtWidgets.QListWidget(Dialog)
        self.worldPacks.setObjectName("worldPacks")
        self.gridLayout.addWidget(self.worldPacks, 1, 2, 1, 1)
        self.gridLayout.setColumnStretch(0, 4)
        self.gridLayout.setColumnStretch(1, 1)
        self.gridLayout.setColumnStretch(2, 4)
        self.gridLayout.setRowStretch(0, 1)
        self.gridLayout.setRowStretch(1, 8)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Packs"))
        self.apply.setText(_translate("Dialog", ">>"))
        self.discard.setText(_translate("Dialog", "<<"))
        self.changetype.setText(_translate("Dialog", "Behavior packs"))
        self.Import.setText(_translate("Dialog", "Import"))
        self.hint.setText(_translate("Dialog", "LEVELNAME - Resource packs"))
