from PySide.QtGui import *
from PySide.QtCore import *

"""
Ported from the Okular sidebar code:
http://websvn.kde.org/trunk/KDE/kdegraphics/okular/ui/sidebar.cpp?view=markup
"""

class SidebarItem(QListWidgetItem):
    SidebarItemType = QListWidgetItem.UserType + 1
    def __init__(self, widget, icon, text):
        super(SidebarItem, self).__init__('', None, self.SidebarItemType)
        self.setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)
        self.setIcon(icon)
        self.setText(text)
        self.setToolTip(text)
        self.widget = widget

class SidebarDelegate(QAbstractItemDelegate):
    ITEM_MARGIN_LEFT = 5
    ITEM_MARGIN_TOP = 5
    ITEM_MARGIN_RIGHT = 5
    ITEM_MARGIN_BOTTOM = 5
    ITEM_PADDING = 5
    def __init__(self, parent):
        super(SidebarDelegate, self).__init__(parent)
        self.showText = True
    def setShowText(self, show):
        self.showText = show
    def isTextShown(self):
        return self.showText
    # from QAbstractItemDelegate
    def paint(self, painter, option, index):
        backBrush = QBrush()
        foreColor = QColor()
        disabled = False
        hover = False
        if not (option.state & QStyle.State_Enabled):
            backBrush = option.palette.brush(QPalette.Disabled, QPalette.Base)
            foreColor = option.palette.color(QPalette.Disabled, QPalette.Text)
            disabled = True
        elif option.state & (QStyle.State_HasFocus|QStyle.State_Selected):
            backBrush = option.palette.brush(QPalette.Highlight)
            foreColor = option.palette.color(QPalette.HighlightedText)
        elif option.state & (QStyle.State_MouseOver):
            backBrush = option.palette.color(QPalette.Highlight).lighter(115)
            foreColor = option.palette.color(QPalette.HighlightedText)
            hover = True
        else: # if ( option.state & QStyle::State_Enabled )
            backBrush = option.palette.brush(QPalette.Base)
            foreColor = option.palette.color(QPalette.Text)
        style = QApplication.style()
        opt = QStyleOptionViewItemV4(option)
        if not style.inherits('KStyle') and hover:
            bs = opt.backgroundBrush.style()
            if bs > Qt.NoBrush and bs < Qt.TexturePattern:
                opt.backgroundBrush = opt.backgroundBrush.color().light(115)
            else:
                opt.backgroundBrush = backBrush
        painter.save()
        style.drawPrimitive(QStyle.PE_PanelItemViewItem, opt, painter, None)
        painter.restore()
        icon = QIcon(index.data(Qt.DecorationRole))
        if not icon.isNull():
            iconpos = QPoint(
                (option.rect.width() - option.decorationSize.width()) / 2,
                self.ITEM_MARGIN_TOP)
            iconpos += QPoint(8, 12)
            iconpos += option.rect.topLeft()
            iconmode = disabled and QIcon.Disabled or QIcon.Normal
            painter.drawPixmap(iconpos, icon.pixmap(option.decorationSize, iconmode))
        if self.showText:
            text = index.data(Qt.DisplayRole)
            fontBoundaries = QFontMetrics(option.font).boundingRect(text)
            textPos = QPoint(
                self.ITEM_MARGIN_LEFT + (option.rect.width() - self.ITEM_MARGIN_LEFT - self.ITEM_MARGIN_RIGHT - fontBoundaries.width()) / 2,
                self.ITEM_MARGIN_TOP + option.decorationSize.height() + self.ITEM_PADDING)
            fontBoundaries.translate(-fontBoundaries.topLeft())
            fontBoundaries.translate(textPos)
            fontBoundaries.translate(option.rect.topLeft())
            painter.setPen(foreColor)
            ### hack for text being cut off
            fontBoundaries.setWidth(fontBoundaries.width()+1)
            painter.drawText(fontBoundaries, Qt.AlignCenter, text)

    def sizeHint(self, option, index):
        baseSize = QSize(option.decorationSize.width(),
            option.decorationSize.height())
        if self.showText:
            fontBoundaries = \
                QFontMetrics(option.font).boundingRect(index.data(Qt.DisplayRole))
            baseSize.setWidth(max(fontBoundaries.width(), baseSize.width()))
            baseSize.setHeight(baseSize.height() + fontBoundaries.height() +
                self.ITEM_PADDING)
        return baseSize + QSize(self.ITEM_MARGIN_LEFT + self.ITEM_MARGIN_RIGHT,
            self.ITEM_MARGIN_TOP + self.ITEM_MARGIN_BOTTOM)

class SidebarListWidget(QListWidget):
    def __init__(self, parent):
        super(SidebarListWidget, self).__init__(parent)
        """ These two are used to keep track of the row an initial mousePress-
        Event() occurs on and the row the cursor moves over while the left
        mouse button is pressed, respectively, as well as for event compre-
        ssion, to avoid calling SideBar::itemClicked() multiple times for
        the same item in a row on mouseMoveEvent()'s. This code is written
        under the assumption that the number and positions of items in the
        list won't change while the user interacts with it using the mouse.
        Future work here must see to that this assumption continues to hold
        up, or achieve calling SideBar::itemClicked() differently."""
        self.mousePressedRow = -1
        self.rowUnderMouse = -1
    def mouseDoubleClickEvent(self, event):
        index = self.indexAt(event.pos())
        if index.isValid() and not (index.flags() & Qt.ItemIsSelectable):
            return
        super(QListWidget, self).mouseDoubleClickEvent(event)
    def mouseMoveEvent(self, event):
        index = self.indexAt(event.pos())
        if index.isValid():
            if index.flags() & Qt.ItemIsSelectable:
                if event.buttons() & Qt.LeftButton and \
                  index.row() != self.mousePressedRow and \
                  index.row() != self.rowUnderMouse:
                    self.mousePressedRow = -1
                    self.rowUnderMouse = index.row()
                    self.parent().itemClicked(self.item(index.row()))
            else:
                return
        super(SidebarListWidget, self).mouseMoveEvent(event)
    def mousePressEvent(self, event):
        index = self.indexAt(event.pos())
        if index.isValid():
            if index.flags() & Qt.ItemIsSelectable:
                if event.buttons() & Qt.LeftButton:
                    self.mousePressedRow = index.row()
            else:
                return
        super(SidebarListWidget, self).mousePressEvent(event)
    def mouseReleaseEvent(self, event):
        index = self.indexAt(event.pos())
        if index.isValid():
            if index.flags() & Qt.ItemIsSelectable:
                if event.button() == Qt.LeftButton and \
                  index.row() != self.rowUnderMouse:
                    self.parent().itemClicked(self.item(index.row()))
            else:
                self.mousePressedRow = -1
                self.rowUnderMouse = -1
        self.mousePressedRow = -1
        self.rowUnderMouse = -1
        super(SidebarListWidget, self).mouseReleaseEvent(event)
    def moveCursor(self, cursorAction, modifiers):
        # modifiers unused
        oldindex = self.currentIndex()
        newindex = oldindex
        if cursorAction == QAbstractItemView.MoveUp or \
          cursorAction == QAbstractItemView.MovePrevious:
            row = oldindex.row() - 1
            while row > -1 and \
              not self.model().index(row, 0).flags() & Qt.ItemIsSelectable:
                row -= 1
            if row > -1:
                newindex = self.model().index(row, 0)
        elif cursorAction == QAbstractItemView.MoveDown or \
          cursorAction == QAbstractItemView.MoveNext:
            row = oldindex.row() + 1
            max = self.model().rowCount()
            while row < max and \
              not self.model().index(row, 0).flags() & Qt.ItemIsSelectable:
                row += 1
            if row < max:
                newindex = self.model().index(row, 0)
        elif cursorAction == QAbstractItemView.MoveHome or \
          cursorAction == QAbstractItemView.MovePageUp:
            row = 0
            while row < oldindex.row() and \
              not self.model().index(row, 0).flags() & Qt.ItemIsSelectable:
                row += 1
            if row < oldindex.row():
                newindex = self.model().index(row, 0)
        elif cursorAction == QAbstractItemView.MoveEnd or \
          cursorAction == QAbstractItemView.MovePageDown:
            row = self.model().rowCount() - 1
            while row > oldindex.row() and \
              not self.model().index(row, 0).flags() & Qt.ItemIsSelectable:
                row -= 1
            if row > oldindex.row():
                newindex = self.model().index(row, 0)
        elif cursorAction == QAbstractItemView.MoveLeft or \
          cursorAction == QAbstractItemView.MoveRight:
            pass

        if oldindex != newindex:
            self.itemClicked.emit(newindex)
        return newindex

class Sidebar(QWidget):
    def __init__(self):
        super(Sidebar, self).__init__()
        mainLay = QHBoxLayout(self)
        mainLay.setMargin(0)
        mainLay.setSpacing(0)
        self.setAutoFillBackground(True)

        self.d = self.Private()
        self.d.list = SidebarListWidget(self)
        mainLay.addWidget(self.d.list)
        self.d.list.setMouseTracking(True)
        self.d.list.viewport().setAttribute(Qt.WA_Hover)
        self.d.sideDelegate = SidebarDelegate(self.d.list)
        ######
        self.d.sideDelegate.setShowText(True)
        self.d.list.setItemDelegate(self.d.sideDelegate)
        self.d.list.setUniformItemSizes(True)
        self.d.list.setSelectionMode(QAbstractItemView.SingleSelection)
        ######
        iconsize = 64
        self.d.list.setIconSize(QSize(iconsize, iconsize))
        self.d.list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.d.list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.d.list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.d.list.viewport().setAutoFillBackground(False)
        ########
        #self.d.list.setFont(
        self.d.list.setFont(QFont('sans serif', 8))

        self.d.splitter = QSplitter(self)
        mainLay.addWidget(self.d.splitter)
        self.d.splitter.setOpaqueResize(True)
        self.d.splitter.setChildrenCollapsible(False)

        self.d.sideContainer = QWidget(self.d.splitter)
        self.d.sideContainer.setMinimumWidth(90)
        self.d.sideContainer.setMaximumWidth(600)
        self.d.vlay = QVBoxLayout(self.d.sideContainer)
        self.d.vlay.setMargin(0)

        self.d.sideTitle = QLabel(self.d.sideContainer)
        self.d.vlay.addWidget(self.d.sideTitle)
        tf = self.d.sideTitle.font()
        tf.setBold(True)
        self.d.sideTitle.setFont(tf)
        self.d.sideTitle.setMargin(3)
        self.d.sideTitle.setIndent(3)

        self.d.stack = QStackedWidget(self.d.sideContainer)
        self.d.vlay.addWidget(self.d.stack)
        self.d.sideContainer.hide()

        self.d.list.customContextMenuRequested.connect(self.listContextMenu)
        self.d.splitter.splitterMoved.connect(self.splitterMoved)
    def addItem(self, widget, icon, text):
        if not widget:
            return -1
        newitem = SidebarItem(widget, icon, text)
        self.d.list.addItem(newitem)
        self.d.pages.append(newitem)
        widget.setParent(self.d.stack)
        self.d.stack.addWidget(widget)
        # updating the minimum height of the icon view, so all are visible with no scrolling
        self.d.adjustListSize(False, True)
        return len(self.d.pages) - 1
    def setMainWidget(self, widget):
        self.d.sideWidget = widget
        if widget:
            # setting the splitter as parent for the widget automatically plugs it
            # into the splitter, neat!
            self.d.sideWidget.setParent(self.d.splitter)
            if not self.d.splitterSizesSet:
                ########
                splitterSizes = []
                if len(splitterSizes) == 0:
                    # the first time use 1/4 for the panel and 9/10 for the pageView
                    splitterSizes.append(100)
                    splitterSizes.append(300)
                self.d.splitter.setSizes(splitterSizes)
                self.d.splitterSizesSet = True
    def setBottomWidget(self, widget):
        self.d.bottomWidget = widget
        if widget:
            widget.setParent(self)
            self.d.vlay.addWidget(widget)
    def setItemEnabled(self, index, enabled):
        if index < 0 or index >= len(pages):
            return
        f = self.d.pages[index].flags()
        if enabled:
            f |= Qt.ItemIsEnabled
            f |= Qt.ItemIsSelectable
        else:
            f &= ~Qt.ItemIsEnabled
            f &= ~Qt.ItemIsSelectable
        self.d.pages[index].setFlags(f)
        if not enabled and index == self.currentIndex() and self.isSidebarVisible():
            # find an enabled item and select that one
            for i, page in enumerate(self.d.pages):
                if page.flags() & Qt.ItemIsEnabled:
                    self.setCurrentIndex(i)
                    break
    def isItemEnabled(self, index):
        if index < 0 or index >= len(pages):
            return False
        f = self.d.pages[index].flags()
        return (f & Qt.ItemIsEnabled) == Qt.ItemIsEnabled
    def setCurrentIndex(self, index):
        if index < 0 or index >= len(self.d.pages):
            return
        self.itemClicked(self.d.pages[index])
        modelindex = self.d.list.model().index(index, 0)
        self.d.list.setCurrentIndex(modelindex)
        self.d.list.selectionModel().select(modelindex, QItemSelectionModel.ClearAndSelect)
    def currentIndex(self):
        return self.d.list.currentRow()
    def setSidebarVisibility(self, visible):
        if visible != self.d.list.isHidden():
            return
        ##########
        pass
    def itemClicked(self, item):
        if not item:
            return
        if item.widget == self.d.stack.currentWidget():
            if self.d.sideContainer.isVisible():
                self.d.list.selectionModel().clear()
                self.d.sideContainer.hide()
            else:
                self.d.sideContainer.show()
                self.d.list.show()
        else:
            if self.d.sideContainer.isHidden():
                self.d.sideContainer.show()
                self.d.list.show()
            self.d.stack.setCurrentWidget(item.widget)
            self.d.sideTitle.setText(item.toolTip())
    def splitterMoved(self, pos, index):
        # if the side panel has been resized, save splitter sizes
        if index == 1:
            self.saveSplitterSize()
    def saveSplitterSize(self):
        # save setting
        #self.d.splitter.sizes()
        # write config
        ########
        pass
    def listContextMenu(self, pos):
        pass
    def showTextToggled(self, on):
        self.d.sideDelegate.setShowText(on)
        self.d.adjustListSize(True, on)
        self.d.list.reset()
        self.d.list.update()
        # save settings for sidebar
        ###########
    def iconSizeChanged(self, action):
        ##############
        pass

    class Private:
        def __init__(self):
            self.list = None
            self.splitter = None
            self.stack = None
            self.sideContainer = None
            self.sideTitle = None
            self.vlay = None
            self.sideWidget = None
            self.bottomWidget = None
            self.pages = []
            self.splitterSizesSet = False
            self.itemsHeight = 0
            self.sideDelegate = None
        def adjustListSize(self, recalc, expand):
            bottomElemRect = QRect(QPoint(0, 0), \
                self.list.sizeHintForIndex(self.list.model().index(self.list.count() - 1, 0)))
            if recalc:
                w = 0
                for i in range(self.list.count()):
                    s = self.list.sizeHintForIndex(self.list.model().index(i, 0))
                    if s.width() > w:
                        w = s.width()
                bottomElemRect.setWidth(w)
            bottomElemRect.translate(0, bottomElemRect.height() * (self.list.count() - 1))
            itemsHeight = bottomElemRect.height() * self.list.count()
            self.list.setMinimumHeight(itemsHeight + self.list.frameWidth() * 2)
            curWidth = self.list.minimumWidth()
            newWidth = expand and \
                max(bottomElemRect.width() + self.list.frameWidth() * 2, curWidth) or \
                min(bottomElemRect.width() + self.list.frameWidth() * 2, curWidth)
            self.list.setFixedWidth(newWidth)

if __name__ == '__main__':
    class MainWindow(QMainWindow):
        def __init__(self):
            super(MainWindow, self).__init__()
            sidebar = Sidebar()
            tex = QTextEdit()
            tex.setText('sdsdssdsddssd')
            chatIcon = QIcon('./data/gfx/icons/chat.png')
            sidebar.addItem(tex, chatIcon, 'Chat')
            chanceIcon = QIcon('./data/gfx/icons/roll.png')
            sidebar.addItem(QTextEdit(), chanceIcon, 'Chance')
            hhIcon = QIcon('./data/gfx/icons/replay.png')
            sidebar.addItem(QTextEdit(), hhIcon, 'Hand')
            notesIcon = QIcon('./data/gfx/icons/document-edit.png')
            sidebar.addItem(QTextEdit(), notesIcon, 'Notes')
            infoIcon = QIcon('./data/gfx/icons/information.png')
            sidebar.addItem(QTextEdit(), infoIcon, 'Info')
            sidebar.setCurrentIndex(1)
            sidebar.setCurrentIndex(0)
            sidebar.setMainWidget(QTextEdit())
            self.setCentralWidget(sidebar)
            self.showMaximized()

    import sys
    translator = QTranslator()
    translator.load('il8n/eo_EO')
    app = QApplication(sys.argv)
    app.installTranslator(translator)
    mainWin = MainWindow()
    sys.exit(app.exec_())

