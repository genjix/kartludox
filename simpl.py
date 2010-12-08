from PySide.QtCore import *
from PySide.QtGui import *
from PySide import QtWebKit
import hand2
import common

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

        """button = QPushButton('Hello')
        buttonItem = QTreeWidgetItem(['Hello'])
        buttonSubItem = QTreeWidgetItem()
        buttonSubItem.setItemWidget(button)
        buttonItem.addChild(buttonSubItem)
        players.append(buttonItem)"""

        playerList.addTopLevelItems(players)

        playerNotesSplitter = QSplitter()
        playerNotesSplitter.setOrientation(Qt.Vertical)
        playerNotesSplitter.addWidget(playerList)

        notesSection = QWidget()
        notesVbox = QVBoxLayout(notesSection)
        notesVbox.addWidget(QLabel('DrawingFishe'))
        notes = QTextEdit()
        notes.setHtml('This player is a <i>real</i> <b>donk</b>!<br /><h1>NEVER BLUFF HIM!!</h1>')
        notesVbox.addWidget(notes)
        playerNotesSplitter.addWidget(notesSection)

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
        image = QImage('data/gfx/cards/nobus/51.png')
        card.setPixmap(QPixmap.fromImage(image))
        hbox.addWidget(card)
        card = QLabel()
        image = QImage('data/gfx/cards/nobus/25.png')
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
        self.setCentralWidget(mainPanelSplitter)
        self.show()

        sb = handhist.verticalScrollBar()
        sb.setSliderPosition(sb.maximum())

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    table = TableWindow()
    sys.exit(app.exec_())
