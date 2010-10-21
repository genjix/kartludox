from PySide import QtCore, QtGui, QtWebKit

class ScrollEater(QtCore.QObject):
    def __init__(self, par):
        super(ScrollEater, self).__init__(par)
    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.Wheel:
            print('eating wheel')
            return True
        else:
            return super(ScrollEater, self).eventFilter(obj, event)

class NonScrollGraphicsView(QtGui.QGraphicsView):
    def wheelEvent(self, event):
        event.ignore()

class MdiTable(QtGui.QMdiSubWindow):
    sequenceNumber = 1

    def __init__(self):
        super(MdiTable, self).__init__()
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle(self.tr('Table titilonius'))
        self.setWindowFlags(QtCore.Qt.WindowMinimizeButtonHint)
        self.setMinimumHeight(200)

        self.pic = QtGui.QPixmap('./data/images/table.png')
        scene = QtGui.QGraphicsScene(self)
        scene.addPixmap(self.pic)
        self.disppic = scene.items()[0]
        #self.view = QtGui.QGraphicsView()
        self.view = NonScrollGraphicsView()
        self.view.setScene(scene)
        self.view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.view.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.setWidget(self.view)

        #scroll = ScrollEater(self.view)
        #self.view.installEventFilter(scroll)
        #self.view.clearFocus()
        #self.view.setFocusPolicy(QtCore.Qt.NoFocus)

        self.seat = QtGui.QPixmap('./data/images/seat_empty.png')
        seat = scene.addPixmap(self.seat)
        seat.setPos(400,30)
        seat = scene.addPixmap(self.seat)
        seat.setPos(80,220)
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
        other.setPos(120, 200)
        other = scene.addPixmap(self.other)
        other.setPos(440, 120)
        other = scene.addPixmap(self.other)
        other.setPos(380, 50)

        self.card8 = QtGui.QPixmap('./data/decks/xanax_card_deck_03/6.png')
        self.cardK = QtGui.QPixmap('./data/decks/xanax_card_deck_03/50.png')
        card = scene.addPixmap(self.card8)
        card.setPos(340,210)
        card = scene.addPixmap(self.cardK)
        card.setPos(640,330)

        self.wgt = QtGui.QWidget()
        hbox = QtGui.QHBoxLayout()
        fold = QtGui.QPushButton('Fold')
        fold.setStyleSheet('background-color: #856d6d; height: 40px; width: 60px')
        fold.setCheckable(True)
        hbox.addWidget(fold)
        call = QtGui.QPushButton('Call')
        call.setStyleSheet('background-color: #856d6d; height: 40px; width: 60px')
        call.setCheckable(True)
        hbox.addWidget(call)
        hbox.addSpacing(20)
        rai = QtGui.QPushButton('Raise')
        rai.setStyleSheet('background-color: #856d6d; color: white; height: 40px; width: 60px')
        rai.setCheckable(True)
        hbox.addWidget(rai)
        self.edit = QtGui.QLineEdit()
        self.edit.setValidator(QtGui.QDoubleValidator(0.0, -1.0, 2, self.edit))
        self.edit.setMaximumSize(50,28)
        self.edit.setText('1')
        #hbox.addWidget(self.edit, 0.2)
        self.slider = QtGui.QSlider(QtCore.Qt.Vertical)
        self.slider.setTickPosition(self.slider.TicksBelow)
        #self.slider.setStyleSheet('background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #B1B1B1, stop:1 #c4c4c4);')
        self.slider.valueChanged.connect(self.sliderMoved)
        self.edit.textChanged.connect(self.textChanged)
        #hbox.addWidget(self.slider)
        self.wgt.resize(500,100)
        #self.btn = QtGui.QPushButton('play')
        #self.btn.setAttribute(QtCore.Qt.WA_NoSystemBackground)
        #self.wgt.setAttribute(QtCore.Qt.WA_NoSystemBackground)
        hbox2 = QtGui.QHBoxLayout()
        hbox2.addStretch()
        hbox2.addLayout(hbox)
        vboxnum = QtGui.QVBoxLayout()
        vboxnum.addStretch()
        vboxnum.addWidget(self.edit)
        hboxslider = QtGui.QHBoxLayout()
        hboxslider.addStretch()
        hboxslider.addLayout(vboxnum)
        hboxslider.addWidget(self.slider)
        vbox = QtGui.QVBoxLayout(self.wgt)
        #vbox.addStretch()
        vbox.addLayout(hboxslider)
        vbox.addLayout(hbox2)
        #item = scene.addWidget(self.wgt)
        self.view.setLayout(vbox)
        #item.setZValue(1)
        #item.setPos(100,100)
        #item.setVisible(True)
    def shownInit(self):
        w = self.pic.size()
        aspect = float(w.width()) / w.height()
        self.adjustSize()
        #self.resize(400, 400)
        #self.view.scale(0.5, 0.5)
    def resizeEvent(self, event):
        super(MdiTable, self).resizeEvent(event)
        return
        size = self.contentsRect().size()

        #newpic = self.pic.scaled(size, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        #self.view.centerOn(1.0, 1.0)
        #self.disppic.setPixmap(newpic)

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
    def wheelEvent(self, event):
        #event.accept()
        # hack to workaround Qt bug
        if self.slider.value() == 0 and event.delta() < 0:
            return
        elif self.slider.value() == 99 and event.delta() > 0:
            return
        pos = QtCore.QPoint(0,0)
        event = QtGui.QWheelEvent(pos, event.delta(), event.buttons(), event.modifiers(), event.orientation())
        QtGui.QApplication.sendEvent(self.slider, event)

class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.mdiArea = QtGui.QMdiArea()
        self.mdiArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.mdiArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        #self.setCentralWidget(self.mdiArea)

        self.createActions()
        #self.createMenus()
        self.createToolBox()
        self.createToolBars()
        #self.createStatusBar()
        #self.updateMenus()

        layout = QtGui.QHBoxLayout()
        """self.showtoolbox = QtGui.QPushButton('>')
        self.showtoolbox.setMaximumWidth(20)
        self.showtoolbox.setFlat(True)
        self.showtoolbox.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Ignored)
        layout.addWidget(self.showtoolbox)"""
        layout.addWidget(self.mdiArea)
        layout.addWidget(self.toolCont)

        self.widget = QtGui.QWidget()
        self.widget.setLayout(layout)
        self.setCentralWidget(self.widget)

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
        self.toolBox = QtGui.QToolBox()
        self.toolBox.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Ignored))
        self.toolBox.setMinimumWidth(300)
        self.toolBox.setMinimumHeight(700)
        self.toolBox.addItem(QtGui.QTextEdit(), self.tr("Chat Window"))
        web = QtWebKit.QWebView()
        import hand
        web.setHtml(hand.handhistory)
        stack = QtGui.QStackedWidget()
        stack.addWidget(web)
        naviglayout = QtGui.QHBoxLayout()
        naviglayout.addWidget(QtGui.QPushButton('<-'))
        naviglayout.addStretch()
        naviglayout.addWidget(QtGui.QPushButton('Copy Text to Clipboard'))
        naviglayout.addStretch()
        nexthh = QtGui.QPushButton('->')
        nexthh.setEnabled(False)
        naviglayout.addWidget(nexthh)
        layout = QtGui.QVBoxLayout()
        title = QtGui.QHBoxLayout()
        title.addWidget(QtGui.QLabel('Genjix - $48.50'))
        title.addWidget(QtGui.QLabel('15 hands ago'))
        layout.addLayout(title)
        layout.addLayout(naviglayout)
        layout.addWidget(stack)
        wgt = QtGui.QWidget()
        wgt.setLayout(layout)
        self.toolBox.addItem(wgt, "Hand History")
        notes = QtGui.QTextEdit()
        notes.setHtml('This player is a <i>real</i> <b>donk</b>!<br /><h1>NEVER BLUFF HIM!!</h1>')
        self.toolBox.addItem(notes, self.tr('Player Notes'))
        # built in pokerstove
        self.toolBox.addItem(QtGui.QTextEdit(), "Chance")
        self.toolBox.addItem(QtGui.QTextEdit(), "Information")
        self.toolBox.setAttribute(QtCore.Qt.WA_NoSystemBackground, False)
        self.toolBox.setStyleSheet('background-color: #ddd;')
        #self.toolBox.setWindowOpacity(1)
        #self.toolBox.setFrameStyle(QtGui.QFrame.StyledPanel)

        layout = QtGui.QHBoxLayout()
        self.hidetoolbox = QtGui.QPushButton('<')
        self.hidetoolbox.setMaximumWidth(20)
        self.hidetoolbox.setFlat(True)
        self.hidetoolbox.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Ignored)
        self.hidetoolbox.setCheckable(True)
        self.hidetoolbox.setChecked(True)
        self.hidetoolbox.toggled.connect(self.toggleToolBox)
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self.hidetoolbox)
        layout.addWidget(self.toolBox)

        self.toolCont = QtGui.QWidget()
        self.toolCont.setLayout(layout)
    def createToolBars(self):
        self.fileToolBar = self.addToolBar('File')
        self.fileToolBar.addAction(self.newTableAct)
        self.fileToolBar.addAction(self.loginAct)
        self.fileToolBar.addAction(self.exitAct)

        self.orderToolBar = self.addToolBar('Order')
        self.orderToolBar.addAction(self.cascadeTablesAct)
        self.orderToolBar.addAction(self.tileTablesAct)
    def toggleToolBox(self, checked):
        if checked:
            self.toolBox.show()
        else:
            self.toolBox.hide()
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
