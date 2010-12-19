from PySide.QtCore import *
from PySide.QtGui import *
from PySide import QtWebKit
import hand2
import common
#testing

class TableWindow(QMainWindow):
    def __init__(self):
        super(TableWindow, self).__init__()

        playerList = QTreeWidget()
        playerList.setColumnCount(2)
        playerList.setHeaderLabels(['Nickname', 'Stack'])
        #playerList.header().hide()
        players = []

        andy = QTreeWidgetItem(['andy', '80'])
        players.append(andy)

        Chisness = QTreeWidgetItem(['Chisness', '112'])
        players.append(Chisness)

        WizardOfAhns = QTreeWidgetItem(['WizardOfAhns', '98'])
        players.append(WizardOfAhns)

        DrawingFishe = QTreeWidgetItem(['DrawingFishe', '120'])
        players.append(DrawingFishe)

        genjix = QTreeWidgetItem(['genjix', '100'])
        players.append(genjix)

        JimiThing34 = QTreeWidgetItem(['Jimithing34', '100'])
        players.append(JimiThing34)
        JimiThing34 = QTreeWidgetItem(['', ''])
        players.append(JimiThing34)
        JimiThing34 = QTreeWidgetItem(['Pot size', '20'])
        players.append(JimiThing34)

        mainpot = QTreeWidgetItem(['Main pot', '15'])
        sidepot = QTreeWidgetItem(['Side pot', '5'])
        JimiThing34.addChild(mainpot)
        JimiThing34.addChild(sidepot)

        playerList.addTopLevelItems(players)

        playerNotesSplitter = QSplitter()
        playerNotesSplitter.setOrientation(Qt.Vertical)
        playerNotesSplitter.addWidget(playerList)

        dock = QDockWidget(self.tr("Players"))
        dock.setAllowedAreas(Qt.LeftDockWidgetArea|Qt.RightDockWidgetArea)
        dock.setWidget(playerList)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)

        notesSection = QWidget()
        notes = QTextEdit()
        notes.setHtml('This player is a <i>real</i> <b>donk</b>!<br /><h1>NEVER BLUFF HIM!!</h1>')

        dock = QDockWidget(self.tr("Notes"))
        dock.setAllowedAreas(Qt.LeftDockWidgetArea|Qt.RightDockWidgetArea)
        dock.setWidget(notes)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)

        #handhist = QtWebKit.QWebView()
        handhist = QTextEdit()
        #handhist.setHtml(hand2.handhistory)
        handhist.setText(hand2.handhistory)
        handhist.setReadOnly(True)
        #handhist.verticalScrollBar().setSliderPosition(handhist.verticalScrollBar().maximum())
        #handhist.setStyleSheet('background-color: #ddd;')

        #-----------------
        self.wgt = QWidget()
        hbox = QHBoxLayout(self.wgt)
        hbox.addStretch()

        card = QLabel()
        image = QImage('data/gfx/cards/nobus/Ad.png')
        card.setPixmap(QPixmap.fromImage(image))
        hbox.addWidget(card)
        card = QLabel()
        image = QImage('data/gfx/cards/nobus/Ac.png')
        card.setPixmap(QPixmap.fromImage(image))
        hbox.addWidget(card)
        hbox.addSpacing(20)

        fold = QPushButton('Fold')
        fold.setObjectName('FoldBtn')
        fold.setCheckable(True)
        fold.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        hbox.addWidget(fold)
        call = QPushButton('Call\n$1')
        call.setObjectName('CallBtn')
        #call.setStyleSheet('background-color: #1169a4; width: 80px; font-size: 10pt; font-weight: bold; color: white;')
        call.setCheckable(True)
        call.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        hbox.addWidget(call)
        hbox.addSpacing(20)
        rai = QPushButton('Raise\n$2')
        rai.setObjectName('RaiseBtn')
        #rai.setStyleSheet('background-color: #1169a4; color: #ddf; width: 80px; height: 50px; font-size: 10pt; font-weight: bold;')
        rai.setCheckable(True)
        rai.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        hbox.addWidget(rai)
        self.edit = QLineEdit()
        self.edit.setValidator(QDoubleValidator(0.0, -1.0, 2, self.edit))
        self.edit.setMaximumSize(40,28)
        self.edit.setText('1')
        if QDir.setCurrent('./data/gfx/table/default/'):
            self.wgt.setStyleSheet(str(common.loadStyleSheet('style.css')))
        QDir.setCurrent('../../../../')
        self.slider = QSlider(Qt.Vertical)
        self.slider.setTickPosition(self.slider.TicksBelow)
        sliderLayout = QVBoxLayout()
        sliderLayout.addWidget(self.slider)
        sliderLayout.addWidget(self.edit)

        sliderhhL = QHBoxLayout()
        sliderhhL.addWidget(handhist)
        sliderhhL.addLayout(sliderLayout)

        mainView = QWidget()
        mainViewLayout = QVBoxLayout(mainView)
        #mainViewLayout.addWidget(handhist)
        mainViewLayout.addLayout(sliderhhL)
        #mainViewLayout.addLayout(sliderLayout)
        mainViewLayout.addWidget(self.wgt)

        mainPanelSplitter = QSplitter(self)
        #mainPanelSplitter.addWidget(QPushButton('Hello'))
        mainPanelSplitter.addWidget(playerNotesSplitter)
        mainPanelSplitter.addWidget(mainView)


        self.setCentralWidget(mainView)
        self.show()

        sb = handhist.verticalScrollBar()
        sb.setSliderPosition(sb.maximum())

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    table = TableWindow()
    sys.exit(app.exec_())
