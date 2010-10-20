from PySide import QtCore, QtGui, QtWebKit

class MdiTable(QtGui.QMdiSubWindow):
    sequenceNumber = 1

    def __init__(self):
        super(MdiTable, self).__init__()
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle(self.tr("Table titilonius"))
        self.setWindowFlags(QtCore.Qt.WindowMinimizeButtonHint)
        self.setMinimumHeight(200)

        self.pic = QtGui.QPixmap('./data/images/table.png')
        scene = QtGui.QGraphicsScene()
        scene.addPixmap(self.pic)
        self.disppic = scene.items()[0]
        self.view = QtGui.QGraphicsView()
        self.view.setScene(scene)
        self.view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.view.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.setWidget(self.view)

        self.seat = QtGui.QPixmap('./data/images/seat_empty.png')
        seat = scene.addPixmap(self.seat)
        seat.setPos(400,30)
        seat = scene.addPixmap(self.seat)
        seat.setPos(400,220)
        seat = scene.addPixmap(self.seat)
        seat.setPos(60,30)
        seat = scene.addPixmap(self.seat)
        seat.setPos(20,120)
        seat = scene.addPixmap(self.seat)
        seat.setPos(460,120)
        self.other = QtGui.QPixmap('./data/images/other_cards.png')
        other = scene.addPixmap(self.other)
        other.setPos(120, 50)
        other = scene.addPixmap(self.other)
        other.setPos(80, 130)
        other = scene.addPixmap(self.other)
        other.setPos(380, 200)
        other = scene.addPixmap(self.other)
        other.setPos(440, 120)
        other = scene.addPixmap(self.other)
        other.setPos(380, 50)

        self.card8 = QtGui.QPixmap('./data/decks/xanax_card_deck_03/6.png')
        self.cardK = QtGui.QPixmap('./data/decks/xanax_card_deck_03/50.png')
        card = scene.addPixmap(self.card8)
        card.setPos(30,220)
        card = scene.addPixmap(self.cardK)
        card.setPos(90,220)

        self.wgt = QtGui.QWidget()
        hbox = QtGui.QHBoxLayout()
        fold = QtGui.QPushButton('Fold')
        fold.setStyleSheet('background-color: #0a0; height: 40px; width: 60px')
        fold.setCheckable(True)
        hbox.addWidget(fold)
        call = QtGui.QPushButton('Call')
        call.setStyleSheet('background-color: #dd0; height: 40px; width: 60px')
        call.setCheckable(True)
        hbox.addWidget(call)
        hbox.addSpacing(20)
        rai = QtGui.QPushButton('Raise')
        rai.setStyleSheet('background-color: #b00; color: white; height: 40px; width: 60px')
        rai.setCheckable(True)
        hbox.addWidget(rai)
        self.edit = QtGui.QLineEdit()
        self.edit.setValidator(QtGui.QDoubleValidator(0.0, -1.0, 2, self.edit))
        self.edit.setMaximumSize(50,28)
        hbox.addWidget(self.edit, 0.2)
        self.slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.slider.setTickPosition(self.slider.TicksBelow)
        self.slider.setStyleSheet('background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #B1B1B1, stop:1 #c4c4c4);')
        self.slider.valueChanged.connect(self.sliderMoved)
        self.edit.textChanged.connect(self.textChanged)
        hbox.addWidget(self.slider)
        self.wgt.resize(500,100)
        #self.btn = QtGui.QPushButton('play')
        #self.btn.setAttribute(QtCore.Qt.WA_NoSystemBackground)
        self.wgt.setAttribute(QtCore.Qt.WA_NoSystemBackground)
        vbox = QtGui.QVBoxLayout(self.wgt)
        vbox.addStretch()
        vbox.addLayout(hbox)
        #item = scene.addWidget(self.wgt)
        self.view.setLayout(vbox)
        #item.setZValue(1)
        #item.setPos(100,100)
        #item.setVisible(True)
    def shownInit(self):
        w = self.pic.size()
        aspect = float(w.width()) / w.height()
        #self.adjustSize()
        #self.resize(400, 400)
        self.resize(400,400)
        #self.view.scale(0.5, 0.5)
    def resizeEvent(self, event):
        super(MdiTable, self).resizeEvent(event)
        #return
        size = self.contentsRect().size()

        newpic = self.pic.scaled(size, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        self.view.centerOn(1.0, 1.0)
        self.disppic.setPixmap(newpic)

        curr_aspect = float(size.width()) / size.height()
        w = self.pic.size()
        aspect = float(w.width()) / w.height()
        if abs(curr_aspect - aspect) > 0.00000001:
            margins = self.contentsMargins()
            self.resize(aspect * size.height() + margins.left() + margins.right(),
                size.height() + margins.top() + margins.bottom())
    def sliderMoved(self, value):
        # should round to the nearest number of big blinds
        self.edit.setText('%.0f'%(1 + 100*value/100.0))
    def textChanged(self, value):
        self.slider.setValue(int(value) - 1)

class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.mdiArea = QtGui.QMdiArea()
        self.mdiArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.mdiArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.setCentralWidget(self.mdiArea)

        self.createActions()
        #self.createMenus()
        self.createToolBox()
        self.createToolBars()
        #self.createStatusBar()
        #self.updateMenus()

        self.setWindowTitle('Hypatia')
        self.setUnifiedTitleAndToolBarOnMac(True)
        self.showMaximized()
        self.createMdiChild()
    def closeEvent(self, event):
        self.mdiArea.closeAllSubWindows()
        if self.activeMdiChild():
            event.ignore()
        else:
            event.accept()
    def activeMdiChild(self):
        activeSubWindow = self.mdiArea.activeSubWindow()
        if activeSubWindow:
            return activeSubWindow.widget()
        return None
    def createMdiChild(self):
        child = MdiTable()
        self.mdiArea.addSubWindow(child)
        child.show()
        child.shownInit()
        return child
    def createActions(self):
        self.newTableAct = QtGui.QAction('New Table', self, 
            shortcut=QtGui.QKeySequence.Print, statusTip='Open new table',
            triggered=self.createMdiChild)
        self.loginAct = QtGui.QAction(QtGui.QIcon('./data/images/new.png'),
            '&Login', self, shortcut=QtGui.QKeySequence.New,
            statusTip='Login to play!', triggered=self.login)
        self.exitAct = QtGui.QAction("E&xit", self, shortcut="Ctrl+Q",
            statusTip="Exit the application",
            triggered=QtGui.qApp.closeAllWindows)
        # ordering
        self.cascadeTablesAct = QtGui.QAction('Cascade Tables', self,
            statusTip='Cascade tables diagonally',
            triggered=self.mdiArea.cascadeSubWindows)
        self.tileTablesAct = QtGui.QAction('Tile Tables', self,
            statusTip='Tiling arrangement',
            triggered=self.mdiArea.tileSubWindows)
    def createMenus(self):
        self.fileMenu = self.menuBar().addMenu('&File')
        self.fileMenu.addAction(self.newTableAct)
        self.fileMenu.addAction(self.loginAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)
    def createToolBox(self):
        self.toolBox = QtGui.QToolBox(self.mdiArea)
        self.toolBox.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Ignored))
        self.toolBox.setMinimumWidth(300)
        self.toolBox.setMinimumHeight(700)
        self.toolBox.addItem(QtGui.QTextEdit(), "Chat Window")
        web = QtWebKit.QWebView()
        import hand
        web.setHtml(hand.handhistory)
        stack = QtGui.QStackedWidget()
        stack.addWidget(web)
        self.toolBox.addItem(stack, "Hand History")
        # built in pokerstove
        self.toolBox.addItem(QtGui.QTextEdit(), "Chance")
        self.toolBox.addItem(QtGui.QTextEdit(), "Information")
        self.toolBox.setAttribute(QtCore.Qt.WA_NoSystemBackground, False)
        #self.toolBox.setStyleSheet('background-color: grey;')
        self.toolBox.setWindowOpacity(1)
    def createToolBars(self):
        self.fileToolBar = self.addToolBar('File')
        self.fileToolBar.addAction(self.newTableAct)
        self.fileToolBar.addAction(self.loginAct)
        self.fileToolBar.addAction(self.exitAct)

        self.orderToolBar = self.addToolBar('Order')
        self.orderToolBar.addAction(self.cascadeTablesAct)
        self.orderToolBar.addAction(self.tileTablesAct)

    def login(self):
        print('foo stub!')

if __name__ == '__main__':
    import sys

    translator = QtCore.QTranslator()
    #translator.load('en_GB')
    translator.load('il8n/eo_EO')
    app = QtGui.QApplication(sys.argv)
    app.installTranslator(translator)
    mainWin = MainWindow()
    sys.exit(app.exec_())
