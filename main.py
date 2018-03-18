import sys
import numpy as np
import time
import threading

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import os
import json

import sys, random
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPainter, QColor, QPen
from PyQt5.QtCore import Qt
import copy
from functools import partial


ROOT_DIR = '/Users/dalong/workspace/ECCV2018/materials/2_result'
ANNO_DIR = '/Users/dalong/workspace/ECCV2018/materials/AnnoSystem/annos/2_result'
if not os.path.exists(ANNO_DIR):
	os.makedirs(ANNO_DIR)
PartNames = ["鼻子", "右眼", "右耳", "右肩膀", "右胳膊肘", "右手腕", "右臀", "右膝盖", "右脚踝", "左眼", "左耳", "左肩膀", "左胳膊肘", "左手腕", "左臀", "左膝盖", "左脚踝"]



class Annos():
	def __init__(self):
		self.init()

	def init(self):
		self.imagepath = None
		self.scaleratio = 1.0
		self.keypoints = []
		self.cur_keypoint = np.zeros((17,3), dtype = np.float32)
		self.cur_partID = 0
		self.cur_vis = True

	def newItem(self):
		self.keypoints.append(copy.deepcopy(self.cur_keypoint.reshape(-1).tolist()))
		self.cur_keypoint = np.zeros((17,3), dtype = np.float32)
		self.cur_partID = 0
		self.cur_vis = True

	def savejson(self):
		if self.imagepath:
			if np.sum(self.cur_keypoint) > 0:
				self.newItem()
			if len(self.keypoints) > 0:
				res = {'imagepath': self.imagepath, 'scaleratio': self.scaleratio, 'keypoints':self.keypoints}
				savepath = self.imagepath.replace(ROOT_DIR, ANNO_DIR)+'_annos.json'
				with open(savepath, 'w') as f:
					json.dump(res, f)

	def print(self, log):
		print ('-------------- < %s > ------------'%log)
		print ('imagepath:', self.imagepath)
		print ('scaleratio:', self.scaleratio)
		print ('keypoints:', self.keypoints)
		print ('cur_keypoint:', self.cur_keypoint)
		print ('cur_partID:', self.cur_partID)
		print ('cur_vis:', self.cur_vis)

CurrentAnnos = Annos()

class MyQLabel(QLabel):

	def __init__(self, parent):
		super().__init__(parent)
		self.label_maxw = 1200.0
		self.label_maxh = 700.0
		self.setGeometry(50, 50, self.label_maxw, self.label_maxh) 

		self.pen = QPen()
		self.pen.setWidth(5)
		self.pen.setBrush(Qt.red)

		self.pos = None
		self.png = None

	def paintEvent(self, e):
		qp = QPainter()
		qp.begin(self)
		if self.png:
			qp.drawPixmap(0,0, self.png)
		if self.pos:
			qp.setPen(self.pen)
			qp.drawPoint(self.pos.x(), self.pos.y()) 
		qp.end()

	def mousePressEvent(self, e):
		self.pos = e.pos()
		print ('PRESS: %d,%d'%(self.pos.x(), self.pos.y()))
		self.update() 

		global CurrentAnnos
		if CurrentAnnos.imagepath:
			CurrentAnnos.cur_keypoint[CurrentAnnos.cur_partID, 0] = self.pos.x()
			CurrentAnnos.cur_keypoint[CurrentAnnos.cur_partID, 1] = self.pos.y()
			if CurrentAnnos.cur_vis == True:
				CurrentAnnos.cur_keypoint[CurrentAnnos.cur_partID, 2] = 1
			elif CurrentAnnos.cur_vis == False:
				CurrentAnnos.cur_keypoint[CurrentAnnos.cur_partID, 2] = 2
			CurrentAnnos.print('mousePressEvent')

	def loadimg(self, filename):

		self.pos = None
		png = QPixmap(filename)
		ratio = min( self.label_maxw / png.width(), self.label_maxh / png.height())
		self.png = png.scaled(png.width()*ratio, png.height()*ratio)
		self.update() 

		global CurrentAnnos
		CurrentAnnos.init()
		CurrentAnnos.imagepath = filename
		CurrentAnnos.scaleratio = ratio
		CurrentAnnos.print('loadimg')

class ControlWindow(QMainWindow):
	def __init__(self):
		super(ControlWindow, self).__init__()
		self.setGeometry(50, 50, 1400, 800)
		self.setWindowTitle("AnnoSystem")

		self.nextImageAction = QAction("&NextImage", self)
		self.nextImageAction.setShortcut("Q")
		self.nextImageAction.triggered.connect(partial(self.nextImage, +1))
		self.preImageAction = QAction("&PreImage", self)
		self.preImageAction.setShortcut("A")
		self.preImageAction.triggered.connect(partial(self.nextImage, -1))

		self.nextItemAction = QAction("&NextItem", self)
		self.nextItemAction.setShortcut("R")
		self.nextItemAction.triggered.connect(self.nextItem)
		self.nextPartAction = QAction("&NextPart", self)
		self.nextPartAction.setShortcut("W")
		self.nextPartAction.triggered.connect(self.nextPart)
		self.changeVisAction = QAction("&ChangeVisState", self)
		self.changeVisAction.setShortcut("E")
		self.changeVisAction.triggered.connect(self.changeVisState)

		self.mainMenu = self.menuBar()
		self.mainMenu.addAction(self.nextImageAction)
		self.mainMenu.addAction(self.preImageAction)
		self.mainMenu.addAction(self.nextItemAction)
		self.mainMenu.addAction(self.changeVisAction)
		self.mainMenu.addAction(self.nextPartAction)

		self.currentID = -1
		self.imagelist = os.listdir(ROOT_DIR)
		self.imagelist.sort(key=lambda x:int(x[:-4]))

		self.qlabel = MyQLabel(self)

		BodyPartBox = QWidget(self)
		BodyPartBoxlayout = QVBoxLayout()
		self.buttonlist = []
		for i in range(17):
			button = QRadioButton(PartNames[i])
			button.clicked.connect(partial(self.changePart, i))
			self.buttonlist.append(button)
			BodyPartBoxlayout.addWidget(button)

		self.buttonlist[0].setChecked(True)
		self.buttonlist[0].setStyleSheet("background-color: red")
		BodyPartBox.setLayout(BodyPartBoxlayout)
		BodyPartBox.setGeometry(1270, 50, 100, 600) 

		self.hintbox = QLabel(self)
		self.hintbox.setGeometry(0, 0, 1000, 50)
		self.hintbox.setText('下一张／上一张图： Q／A     本图下一个人：R      下一个部位：W   【进入下一张图时候（Q）本图结果自动保存。】') 


	def nextImage(self, direction):
		global CurrentAnnos
		CurrentAnnos.savejson()
		self.currentID += direction
		self.currentID = min(max(self.currentID, 0), len(self.imagelist)-1)
		self.currentPath = '%s/%s'%(ROOT_DIR, self.imagelist[self.currentID])
		self.qlabel.loadimg(self.currentPath)
		
		self.buttonlist[CurrentAnnos.cur_partID].setChecked(True)
		for bt in self.buttonlist:
			bt.setStyleSheet("background-color: None")
		self.buttonlist[CurrentAnnos.cur_partID].setStyleSheet("background-color: red")
		CurrentAnnos.print('nextImage')

	def nextItem(self):
		global CurrentAnnos
		CurrentAnnos.newItem()
		CurrentAnnos.print('nextItem')

	def nextPart(self):
		global CurrentAnnos
		CurrentAnnos.cur_partID += 1
		CurrentAnnos.cur_partID = CurrentAnnos.cur_partID % 17
		CurrentAnnos.cur_vis = True
		self.buttonlist[CurrentAnnos.cur_partID].setChecked(True)
		for bt in self.buttonlist:
			bt.setStyleSheet("background-color: None")
		self.buttonlist[CurrentAnnos.cur_partID].setStyleSheet("background-color: red")
		CurrentAnnos.print('nextPart')

	def changePart(self, id):
		global CurrentAnnos
		CurrentAnnos.cur_partID = id
		CurrentAnnos.cur_vis = True
		self.buttonlist[CurrentAnnos.cur_partID].setChecked(True)
		for bt in self.buttonlist:
			bt.setStyleSheet("background-color: None")
		self.buttonlist[CurrentAnnos.cur_partID].setStyleSheet("background-color: red")
		CurrentAnnos.print('changePart')

	def changeVisState(self):
		global CurrentAnnos
		CurrentAnnos.cur_vis = bool((CurrentAnnos.cur_vis + 1) % 2)
		CurrentAnnos.print('changeVisState')





if __name__ == '__main__':
	app = QApplication(sys.argv)
	window = ControlWindow()
	#window.showMaximized()
	window.show()
	sys.exit(app.exec_())


