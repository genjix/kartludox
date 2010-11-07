from PySide import QtCore, QtGui, QtWebKit, QtSvg
import common, random

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

class Interactable(QtGui.QGraphicsPixmapItem):
    def __init__(self, pixmap, table):
        super(Interactable, self).__init__(pixmap)
        self.table = table
    def mousePressEvent(self, event):
        super(Interactable, self).mousePressEvent(event)
        print('small cards -----')
        for c in self.table.allCards:
            p = c.pos()
            print(p.x(), p.y())
        print('seats ----------')
        for s in self.table.allSeats:
            p = s.pos()
            print(p.x(), p.y())
        print('--------------')

class MdiTable(QtGui.QMdiSubWindow):
    sequenceNumber = 1

    def __init__(self, parent):
        super(MdiTable, self).__init__(parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle(self.tr('Table titilonius'))
        #self.setWindowFlags(QtCore.Qt.WindowMinimizeButtonHint)
        self.setMinimumHeight(200)

        self.pic = QtGui.QPixmap('./data/gfx/table/default/table.png')
        scene = QtGui.QGraphicsScene(self)
        scene.setBackgroundBrush(parent.mdiArea.background())
        #seat = scene.addPixmap(self.pic)
        seat = Interactable(self.pic, self)
        seat.setTransformationMode(QtCore.Qt.SmoothTransformation)
        scene.addItem(seat)
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

        #self.seat = QtGui.QPixmap('./data/gfx/table/default/seat_empty.png')
        self.seat_boy = QtGui.QPixmap('./data/gfx/table/default/boy.png')
        self.seat_girl = QtGui.QPixmap('./data/gfx/table/default/girl.png')
        self.seat_custom = QtGui.QPixmap('./data/gfx/table/default/custom-avatar.png')
        #positions = [(610, 100), (620, 200), (510, 290), (330, 290), (140, 290), (30, 200), (60, 100), (240, 60), (430, 60)]
        avatarPositions = [(40, 170), (470, 280), (200, 280), (630, 170), (200, 40), (470, 40)]
        self.allSeats = []
        for p in avatarPositions:
            choice = random.randint(0,2)
            if choice == 0:
                seat = scene.addPixmap(self.seat_boy)
            elif choice == 1:
                seat = scene.addPixmap(self.seat_girl)
            else:
                seat = scene.addPixmap(self.seat_custom)
            seat.setTransformationMode(QtCore.Qt.SmoothTransformation)
            seat.setFlags(seat.ItemIsMovable)
            seat.setPos(*p)
            self.allSeats.append(seat)
            #seat = scene.addPixmap(self.seat)
        """seat.setPos(80,220)
        seat.setTransformationMode(QtCore.Qt.SmoothTransformation)
        seat = scene.addPixmap(self.seat)
        seat.setPos(60,30)
        seat.setTransformationMode(QtCore.Qt.SmoothTransformation)
        seat = scene.addPixmap(self.seat)
        seat.setPos(20,120)
        seat.setTransformationMode(QtCore.Qt.SmoothTransformation)
        seat = scene.addPixmap(self.seat)
        seat.setPos(460,120)
        seat.setTransformationMode(QtCore.Qt.SmoothTransformation)"""
        self.other = QtGui.QPixmap('./data/gfx/table/default/other_cards.png')
        #positions = [(610, 120), (620, 200), (510, 290), (330, 290), (140, 290), (100, 210), (120, 120), (280, 110), (480, 110)]
        positions = [(625, 210), (250, 80), (250, 320), (100, 210), (470, 80)]
        self.allCards = []
        for p in positions:
            #other = Interactable(self.other, self)
            other = scene.addPixmap(self.other)
            other.setTransformationMode(QtCore.Qt.SmoothTransformation)
            other.setFlags(other.ItemIsMovable)
            other.setPos(*p)
            self.allCards.append(other)
            #scene.addItem(other)
        """other = scene.addPixmap(self.other)
        other.setPos(80, 130)
        other.setTransformationMode(QtCore.Qt.SmoothTransformation)
        other = scene.addPixmap(self.other)
        other.setPos(120, 200)
        other.setTransformationMode(QtCore.Qt.SmoothTransformation)
        other = scene.addPixmap(self.other)
        other.setPos(440, 120)
        other.setTransformationMode(QtCore.Qt.SmoothTransformation)
        #other = scene.addPixmap(self.other)
        other = Interactable(self.other)
        other.setPos(380, 50)
        other.setTransformationMode(QtCore.Qt.SmoothTransformation)
        scene.addItem(other)"""

        #self.card8 = QtGui.QPixmap('./data/gfx/cards/xanax_card_deck_03/6.png')
        #self.cardK = QtGui.QPixmap('./data/gfx/cards/xanax_card_deck_03/50.png')
        card = QtSvg.QGraphicsSvgItem('./data/gfx/cards/replixanax/6.svg')
        scene.addItem(card)
        #card = scene.addPixmap(self.card8)
        card.setPos(455,290)
        #card.setTransformationMode(QtCore.Qt.SmoothTransformation)
        #card = scene.addPixmap(self.cardK)
        card = QtSvg.QGraphicsSvgItem('./data/gfx/cards/replixanax/48.svg')
        scene.addItem(card)
        card.setPos(515,290)
        #card.setTransformationMode(QtCore.Qt.SmoothTransformation)

        font = QtGui.QFont('Lucida Sans')
        font.setPointSize(10)
        font1 = QtGui.QFont('Lucida Sans')
        font1.setPointSize(10)
        font1.setWeight(QtGui.QFont.Black)
        brush = QtGui.QLinearGradient()
        brush.setColorAt(0, QtCore.Qt.white)
        #brush = QtGui.QBrush()
        #brush.setColor(QtCore.Qt.white)
        pen = QtGui.QPen()
        pen.setWidth(0)
        pen.setStyle(QtCore.Qt.NoPen)
        names = [
            "Tracy",
            "Genjix",
            "derp-derp",
            "KibKibKib",
            "drawingfishe",
            "scribl"]
        stacks = [
            '1200 btc',
            '8000 btc',
            '100 btc',
            '9112 btc',
            '7654 btc',
            '400 btc']
        playbox = QtGui.QPixmap('./data/gfx/table/default/playerbox.png')
        for p in avatarPositions:
            path = QtGui.QPainterPath()
            play = scene.addPixmap(playbox)
            p = p[0], p[1] + 80
            play.setPos(p[0] - 20, p[1] - 4)
            p = p[0], p[1] + 12
            path.addText(QtCore.QPointF(p[0], p[1]), font, names.pop())
            p = p[0], p[1] + 20
            path.addText(QtCore.QPointF(p[0], p[1]), font1, stacks.pop())
            scene.addPath(path, pen, brush)

        self.wgt = QtGui.QWidget()
        hbox = QtGui.QHBoxLayout()
        hbox.addStretch()
        fold = QtGui.QPushButton('Fold')
        fold.setObjectName('FoldBtn')
        #fold.setStyleSheet('background-color: #1169a4; width: 80px; font-size: 10pt; font-weight: bold; color: white;')
        fold.setCheckable(True)
        fold.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Minimum)
        hbox.addWidget(fold)
        call = QtGui.QPushButton('Call\n$1')
        call.setObjectName('CallBtn')
        #call.setStyleSheet('background-color: #1169a4; width: 80px; font-size: 10pt; font-weight: bold; color: white;')
        call.setCheckable(True)
        call.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Minimum)
        hbox.addWidget(call)
        hbox.addSpacing(20)
        rai = QtGui.QPushButton('Raise\n$2')
        rai.setObjectName('RaiseBtn')
        #rai.setStyleSheet('background-color: #1169a4; color: #ddf; width: 80px; height: 50px; font-size: 10pt; font-weight: bold;')
        rai.setCheckable(True)
        rai.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Minimum)
        hbox.addWidget(rai)
        self.edit = QtGui.QLineEdit()
        self.edit.setValidator(QtGui.QDoubleValidator(0.0, -1.0, 2, self.edit))
        self.edit.setMaximumSize(60,28)
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
        self.wgt.setAttribute(QtCore.Qt.WA_NoSystemBackground)
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
        vbox.addLayout(hbox)
        size = self.pic.size()
        self.wgt.resize(size.width(), size.height())
        if QtCore.QDir.setCurrent('./data/gfx/table/default/'):
            self.wgt.setStyleSheet(common.loadStyleSheet('style.css'))
        QtCore.QDir.setCurrent('../../../../')
        scene.addWidget(self.wgt)
        self.view.setRenderHints(QtGui.QPainter.Antialiasing|QtGui.QPainter.SmoothPixmapTransform)
        #self.chat = QtGui.QTextEdit(self.view)
        #item = scene.addWidget(self.wgt)
        #self.view.setLayout(vbox)
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
        size = self.contentsRect().size()

        #newpic = self.pic.scaled(size, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        #self.view.centerOn(1.0, 1.0)
        #self.disppic.setPixmap(newpic)

        curr_aspect = float(size.width()) / size.height()
        w = self.pic.size()
        aspect = float(w.width()) / w.height()
        if abs(curr_aspect - aspect) > 0.00000001 and not self.isMaximized():
            margins = self.contentsMargins()
            self.resize(aspect * size.height() + margins.left() + margins.right(),
                size.height() + margins.top() + margins.bottom())

        winSize = self.contentsRect().size()
        winw, winh = winSize.width(), winSize.height()
        picSize = self.pic.size()
        picw, pich = picSize.width(), picSize.height()
        scale = winw / float(picw)
        scale2 = winh / float(pich)
        scale = scale < scale2 and scale or scale2
        trans = QtGui.QTransform()
        trans.scale(scale, scale)
        self.view.setTransform(trans)
        self.view.repaint()
        #self.chat.resize(winw*0.5, winh*0.5)
        #self.chat.move(10,winh*0.5 - 10)
    def sliderMoved(self, value):
        # should round to the nearest number of big blinds
        self.edit.setText('%.0f'%(1 + 100*value/100.0))
    def textChanged(self, value):
        self.slider.setValue(round(float(value)) - 1)
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

        """import irc
        from twisted.internet import reactor
        irc.log.startLogging(sys.stdout)
        self.f = irc.LogBotFactory('#pangaea', '/tmp/foo')
        reactor.connectTCP("irc.freenode.net", 6667, self.f)
        reactor.runReturn()"""

        self.mdiArea = QtGui.QMdiArea()
        self.mdiArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.mdiArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

        import sidebar
        self.document = sidebar.Sidebar()
        self.document.setMainWidget(self.mdiArea)
        self.setCentralWidget(self.document)
        #self.setCentralWidget(self.mdiArea)

        self.createActions()
        #self.createDockWidgets()
        self.createSidebarItems()
        self.createMenus()
        self.createToolBars()
        #self.createStatusBar()
        #self.updateMenus()

        layout = QtGui.QHBoxLayout()
        """self.showtoolbox = QtGui.QPushButton('>')
        self.showtoolbox.setMaximumWidth(20)
        self.showtoolbox.setFlat(True)
        self.showtoolbox.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Ignored)
        layout.addWidget(self.showtoolbox)"""
        """layout.addWidget(self.mdiArea)
        layout.addWidget(self.toolCont)

        self.widget = QtGui.QWidget()
        self.widget.setLayout(layout)
        self.setCentralWidget(self.widget)"""

        #self.splitter = QtGui.QSplitter()
        #self.splitter.addWidget(self.mdiArea)
        #self.splitter.addWidget(self.toolBox)
        #self.setCentralWidget(self.splitter)


        #v = autohide_dock.QAutoHideDockWidgets(QtCore.Qt.LeftDockWidgetArea, self)

        self.setWindowTitle('Kartludox')
        self.setUnifiedTitleAndToolBarOnMac(True)
        self.showMaximized()
        self.createMdiChild()
    def closeEvent(self, event):
        from twisted.internet import reactor
        print('closing reactor...')
        reactor.stop()
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
        child = MdiTable(self)
        self.mdiArea.addSubWindow(child)
        child.show()
        child.shownInit()
        return child
    def createActions(self):
        self.newTableAct = QtGui.QAction('New Table', self, 
            shortcut=QtGui.QKeySequence.Print, statusTip='Open new table',
            triggered=self.createMdiChild)
        self.loginAct = QtGui.QAction(QtGui.QIcon('./data/gfx/gui/default/new.png'),
            '&Login', self, shortcut=QtGui.QKeySequence.New,
            statusTip='Login to play!', triggered=self.login)
        # ordering
        self.cascadeTablesAct = QtGui.QAction('Cascade Tables', self,
            statusTip='Cascade tables diagonally',
            triggered=self.mdiArea.cascadeSubWindows)
        self.tileTablesAct = QtGui.QAction('Tile Tables', self,
            statusTip='Tiling arrangement',
            triggered=self.mdiArea.tileSubWindows)

        # new tidy items
        # actions can either have an icon or not
        # they must all follow the same format for readability
        icon = lambda s: QtGui.QIcon('./data/gfx/icons/' + s)
        configIcon = icon('configure.png') 

        # file
        # network sub menu
        self.serverListAct = QtGui.QAction(icon('network-server.png'),
            self.tr('Server List...'), self,
            shortcut=self.tr('F2'),
            statusTip=self.tr('List of available servers to connect to'))
        self.confNetsAct = QtGui.QAction(configIcon,
            self.tr('Configure &Networks...'), self,
            statusTip=self.tr('Add, remove and modify the different networks you\'ve configured'))
        self.connNetActs = []
        netNames = ('liquidpoker.net', 'play money')
        disconnIcon = icon('network-disconnect.png')
        for net in netNames:
            self.connNetActs.append(QtGui.QAction(disconnIcon, net, self,
            statusTip=self.tr('Connect to') + ' ' + net))
        # ----
        self.quitAct = QtGui.QAction(icon('application-exit.png'),
            self.tr("&Quit"), self,
            shortcut=QtGui.QKeySequence.Quit,
            statusTip=self.tr('Quit the application'),
            triggered=QtGui.qApp.closeAllWindows)

        # view
        self.showMenuBarAct = QtGui.QAction(icon('show-menu.png'),
            self.tr('Show &Menu Bar'), self, shortcut='CTRL+M',
            statusTip=self.tr('Show the menu bar'), checkable=True, checked=True)
        self.showStatusBarAct = QtGui.QAction(self.tr('Show Status &Bar'), self,
            statusTip=self.tr('Show the status bar'), checkable=True, checked=False)
        self.showMainToolBarAct = QtGui.QAction(self.tr('&Main Toolbar'), self,
            statusTip=self.tr('Show the main toolbar'), checkable=True, checked=True)
        # the various panels
        self.showPanelChatAct = QtGui.QAction(self.tr('Chat'), self,
            statusTip=self.tr('Show the chat window panel'), checkable=True, checked=True)
        self.showPanelHHAct = QtGui.QAction(self.tr('Hand History'), self,
            statusTip=self.tr('Show the hand history panel'), checkable=True, checked=True)
        self.showPanelNotesAct = QtGui.QAction(self.tr('Notes'), self,
            statusTip=self.tr('Show the player notes panel'), checkable=True, checked=True)
        self.showPanelChanceAct = QtGui.QAction(self.tr('Chance'), self,
            statusTip=self.tr('Show the chance and odds panel'), checkable=True, checked=True)
        self.showPanelInfoAct = QtGui.QAction(self.tr('Information'), self,
            statusTip=self.tr('Show the information panel'), checkable=True, checked=True)
        # sidebar pos sub menu
        self.sidebarPosLeftAct = QtGui.QAction(self.tr('&Left', 'View|Sidebar Position'), self,
            statusTip=self.tr('Display the sidebar on the left'), checkable=True, checked=True)
        self.sidebarPosRightAct = QtGui.QAction(self.tr('&Right', 'View|Sidebar Position'), self,
            statusTip=self.tr('Display the sidebar on the right'), checkable=True, checked=False)
        # ----
        self.lockSidebarAct = QtGui.QAction(icon('unlock.png'),
            self.tr('&Lock Sidebar'), self,
            statusTip=self.tr('Lock the sidebar in place and prevent it from moving'),
            checkable=True, checked=False)

        # tools
        self.PT3HUDAct = QtGui.QAction(icon('pokertracker3.png'),
            self.tr('PokerTracker3'), self,
            statusTip=self.tr('Enable the PokerTracker3 Heads-Up Display'))

        # settings
        self.confNotifyAct = QtGui.QAction(icon('preferences-desktop-notification.png'),
            self.tr('&Configure &Notifications...'), self,
            statusTip=self.tr('Configure various notifications'))
        self.confShortcutsAct = QtGui.QAction(icon('configure-shortcuts.png'),
            self.tr('&Configure S&hortcuts...'), self,
            statusTip=self.tr('Configure shortcut keys'))
        self.confToolbarsAct = QtGui.QAction(icon('configure-toolbars.png'),
            self.tr('&Configure Tool&bars...'), self,
            statusTip=self.tr('Configure toolbar contents'))
        self.confAct = QtGui.QAction(configIcon,
            self.tr('&Configure Kartludox...'), self,
            shortcut=QtGui.QKeySequence.Preferences,
            statusTip=self.tr('Configure common application settings'))

        # help
        self.reportBugAct = QtGui.QAction(icon('tools-report-bug.png'),
            self.tr('Report Bug'), self,
            statusTip=self.tr('Make a bug report to help us improve the software!'))
        self.switchLangAct = QtGui.QAction(icon('config-language.png'),
            self.tr('Switch Application Language'), self,
            statusTip=self.tr('Select an alternative language'))
    def createMenus(self):
        menub = self.menuBar()
        fileMenu = menub.addMenu('&File')
        fileMenu.addAction(self.serverListAct)
        networksSubMenu = fileMenu.addMenu(self.tr('&Networks'))
        # has icon
        networksSubMenu.addAction(self.confNetsAct)
        networksSubMenu.addSeparator()
        # has changeable icon for statuses- see Quassel
        for netAct in self.connNetActs:
            networksSubMenu.addAction(netAct)
        fileMenu.addSeparator()
        # has red X icon
        fileMenu.addAction(self.quitAct)

        """requestsMenu = menub.addMenu(self.tr('&Requests'))
        # add menus for each network here
        liquidpokerSubMenu = requestsMenu.addMenu('liquidpoker.net')
        liquidpokerSubMenu.addAction('&Cashier')
        liquidpokerSubMenu.addAction('&Account')
        playmoneySubMenu = requestsMenu.addMenu('play money')
        playmoneySubMenu.addAction('&Cashier')
        playmoneySubMenu.addAction('&Account')
        playmoneySubMenu.setEnabled(False)"""

        viewMenu = menub.addMenu(self.tr('&View'))
        # has icon
        viewMenu.addAction(self.showMenuBarAct)
        viewMenu.addAction(self.showStatusBarAct)
        toolbarsSubMenu = viewMenu.addMenu(self.tr('&Toolbars Shown'))
        toolbarsSubMenu.addAction(self.showMainToolBarAct)
        viewMenu.addSeparator()
        viewMenu.addAction(self.showPanelChatAct)
        viewMenu.addAction(self.showPanelHHAct)
        viewMenu.addAction(self.showPanelNotesAct)
        viewMenu.addAction(self.showPanelChanceAct)
        viewMenu.addAction(self.showPanelInfoAct)
        #viewMenu.addAction(self.infoPanel.toggleViewAction())
        viewMenu.addSeparator()
        sidebarPosSubMenu = viewMenu.addMenu(self.tr('Sidebar &Position'))
        sidebarPosSubMenu.addAction(self.sidebarPosLeftAct)
        sidebarPosSubMenu.addAction(self.sidebarPosRightAct)
        viewMenu.addAction(self.lockSidebarAct)

        toolsMenu = menub.addMenu(self.tr('&Tools'))
        arrangeTablesSubMenu = toolsMenu.addMenu('Arrange Tables')
        arrangeTablesSubMenu.addAction('Tile')
        arrangeTablesSubMenu.addAction('Cascade')
        hudSubMenu = toolsMenu.addMenu('Heads Up Display')
        hudSubMenu.addAction(self.PT3HUDAct)
        toolsMenu.addAction('Auto-Fold')

        # these all have icons
        settingsMenu = menub.addMenu(self.tr('&Settings'))
        settingsMenu.addAction(self.confNotifyAct)
        settingsMenu.addAction(self.confShortcutsAct)
        settingsMenu.addAction(self.confToolbarsAct)
        settingsMenu.addAction(self.confAct)

        # again all have icons
        helpMenu = menub.addMenu(self.tr('&Help'))
        helpMenu.addAction('Kartludox Handbook')
        helpMenu.addAction('What\'s &This?')
        helpMenu.addSeparator()
        helpMenu.addAction(self.reportBugAct)
        helpMenu.addSeparator()
        helpMenu.addAction(self.switchLangAct)
        helpMenu.addSeparator()
        helpMenu.addAction('About Kartludox')
    def createSidebarItems(self):
        icon = lambda s: QtGui.QIcon('./data/gfx/icons/' + s)

        web = QtWebKit.QWebView()
        import hand
        web.setHtml(hand.handhistory)
        stack = QtGui.QStackedWidget()
        stack.addWidget(web)
        naviglayout = QtGui.QHBoxLayout()
        firsthh = QtGui.QPushButton(icon('go-first.png'), '')
        firsthh.setMaximumWidth(30)
        firsthh.setFlat(True)
        naviglayout.addWidget(firsthh)
        prevhh = QtGui.QPushButton(icon('go-previous.png'), '')
        prevhh.setMaximumWidth(30)
        prevhh.setFlat(True)
        naviglayout.addWidget(prevhh)
        naviglayout.addStretch()
        copyclip = QtGui.QPushButton(icon('klipper.png'), 'Copy Text')
        copyclip.setFlat(True)
        naviglayout.addWidget(copyclip)
        naviglayout.addStretch()
        nexthh = QtGui.QPushButton(icon('go-next.png'), '')
        nexthh.setEnabled(False)
        nexthh.setMaximumWidth(30)
        nexthh.setFlat(True)
        firsthh = QtGui.QPushButton(icon('go-last.png'), '')
        firsthh.setEnabled(False)
        firsthh.setMaximumWidth(30)
        firsthh.setFlat(True)
        naviglayout.addWidget(nexthh)
        naviglayout.addWidget(firsthh)
        layout = QtGui.QVBoxLayout()
        lis = QtGui.QComboBox()
        lis.addItem('Genjix - $48.50    15 hands ago')
        lis.addItem('Genjix - $48.50    15 hands ago')
        lis.addItem('Genjix - $48.50    15 hands ago')
        lis.addItem('Genjix - $48.50    15 hands ago')
        lis.addItem('Genjix - $48.50    15 hands ago')
        layout.addWidget(lis)
        layout.addLayout(naviglayout)
        layout.addWidget(stack)
        wgt = QtGui.QWidget()
        wgt.setLayout(layout)
        ###### lazy
        sidebar = self.document
        tex = QtGui.QTextEdit()
        tex.setText('sdsdssdsddssd')
        chatIcon = QtGui.QIcon('./data/gfx/icons/chat.png')
        sidebar.addItem(tex, chatIcon, 'Chat')
        chanceIcon = QtGui.QIcon('./data/gfx/icons/roll.png')
        sidebar.addItem(QtGui.QTextEdit(), chanceIcon, 'Chance')
        hhIcon = QtGui.QIcon('./data/gfx/icons/replay.png')
        sidebar.addItem(wgt, hhIcon, 'Hand')
        notesIcon = QtGui.QIcon('./data/gfx/icons/document-edit.png')
        notesWidget = QtGui.QTextEdit()
        notesFont = QtGui.QFont('monospace')
        notesFont.setPointSize(10)
        notesWidget.setCurrentFont(notesFont)
        sidebar.addItem(notesWidget, notesIcon, 'Notes')
        infoIcon = QtGui.QIcon('./data/gfx/icons/information.png')
        sidebar.addItem(QtGui.QTextEdit(), infoIcon, 'Info')
        sidebar.setCurrentIndex(1)
        sidebar.setCurrentIndex(0)
        ######
    def createDockWidgets(self):
        icon = lambda s: QtGui.QIcon('./data/gfx/icons/' + s)

        self.setTabPosition(QtCore.Qt.AllDockWidgetAreas, QtGui.QTabWidget.North)
        dock = QtGui.QDockWidget(self.tr("Chat Window"))
        dock.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea|QtCore.Qt.RightDockWidgetArea)
        dock.setWidget(QtGui.QTextEdit())
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dock)


        dock2 = QtGui.QDockWidget(self.tr("Hand History"))
        dock2.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea|QtCore.Qt.RightDockWidgetArea)
        dock2.setWidget(wgt)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dock2)
        self.tabifyDockWidget(dock, dock2)

        notes = QtGui.QTextEdit()
        notes.setHtml('This player is a <i>real</i> <b>donk</b>!<br /><h1>NEVER BLUFF HIM!!</h1>')
        dock2 = QtGui.QDockWidget(self.tr("Notes"))
        dock2.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea|QtCore.Qt.RightDockWidgetArea)
        dock2.setWidget(notes)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dock2)
        self.tabifyDockWidget(dock, dock2)
        # built in pokerstove
        dock2 = QtGui.QDockWidget(self.tr("Chance"))
        dock2.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea|QtCore.Qt.RightDockWidgetArea)
        dock2.setWidget(QtGui.QTextEdit())
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dock2)
        self.tabifyDockWidget(dock, dock2)
        dock2 = QtGui.QDockWidget(self.tr("Information"))
        dock2.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea|QtCore.Qt.RightDockWidgetArea)
        dock2.setWidget(QtGui.QTextEdit())
        self.infoPanel = dock2
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dock2)
        self.tabifyDockWidget(dock, dock2)
        #self.toolBox.setStyleSheet('background-color: #ddd;')
        #self.toolBox.setWindowOpacity(1)
        #self.toolBox.setFrameStyle(QtGui.QFrame.StyledPanel)

        """layout = QtGui.QHBoxLayout()
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
        self.toolCont.setLayout(layout)"""
    def createToolBars(self):
        self.fileToolBar = self.addToolBar('File')
        self.fileToolBar.addAction(self.newTableAct)
        self.fileToolBar.addAction(self.loginAct)
        self.fileToolBar.addAction(self.quitAct)

        self.orderToolBar = self.addToolBar('Order')
        self.orderToolBar.addAction(self.cascadeTablesAct)
        self.orderToolBar.addAction(self.tileTablesAct)
    def createStatusBar(self):
        self.statusBar().showMessage("Ready")
    def toggleToolBox(self, checked):
        if checked:
            self.toolBox.show()
        else:
            self.toolBox.hide()
    def login(self):
        from twisted.internet import reactor
        reactor.stop()
        print('foo stub!')

if __name__ == '__main__':
    import sys

    translator = QtCore.QTranslator()
    #translator.load('en_GB')
    translator.load('data/translations/eo_EO')
    app = QtGui.QApplication(sys.argv)
    #qt4reactor.install()
    app.installTranslator(translator)
    appIcon = QtGui.QIcon('./data/gfx/icons/kartludox.png')
    app.setWindowIcon(appIcon)
    mainWin = MainWindow()
    sys.exit(app.exec_())
