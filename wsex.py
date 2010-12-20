from PySide.QtCore import *
from PySide.QtGui import *
import sys
import json

app = QApplication(sys.argv)

from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
from twisted.python import log

import common

dealername = 'donisto'

class ConnectionDialog(QDialog):
    def __init__(self, parent):
        super(ConnectionDialog, self).__init__()
        self.line_network = QLineEdit('irc.freenode.org')
        self.line_channel = QLineEdit('#pokerface')
        self.line_nick = QLineEdit('prava')
        confirm = QPushButton('OK')
        confirm.clicked.connect(self.accept)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.line_network)
        main_layout.addWidget(self.line_channel)
        main_layout.addWidget(self.line_nick)
        main_layout.addWidget(confirm)
        self.setLayout(main_layout)

class NumberDialog(QDialog):
    def __init__(self, parent):
        super(NumberDialog, self).__init__()
        self.number_edit = QLineEdit('0')
        confirm = QPushButton('OK')
        confirm.clicked.connect(self.accept)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.number_edit)
        main_layout.addWidget(confirm)
        self.setLayout(main_layout)
    
    @property
    def number(self):
        return int(self.number_edit.text())

class Adapter(irc.IRCClient):        
    @property
    def nickname(self):
        return self.factory.nickname
    @property
    def channel(self):
        return self.factory.channel
    @property
    def window(self):
        return self.factory.window

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)
        self.adapter = {}

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)

    def signedOn(self):
        self.join(self.channel)

    def joined(self, channel):
        if channel != self.channel:
            raise Exception('In wrong channel!')
        self.send_message('!show')
        self.window.protocol = self
       
    def privmsg(self, user, channel, msg):
        """Called when we receive a message."""
        user = user.split('!', 1)[0]
        if channel == self.channel:
            if dealername == user:
                dealmsg = json.loads(msg)
                if 'table' in dealmsg:
                    self.window.set_table(dealmsg)
                elif 'error' in dealmsg:
                    self.window.report_error(dealmsg)
                else:
                    print dealmsg
            else:
                if msg[0] == '!':
                    pass
                else:
                    self.window.chat_message(user, msg)

    def send_message(self, msg):
        self.msg(self.channel, msg)

    def action(self, user, channel, msg):
        """Called when someone does a /me action."""
        user = user.split('!', 1)[0]
        print("* %s %s" % (user, msg))

    # irc callbacks
    def irc_NICK(self, prefix, params):
        """Called when a user changes their nickname."""
        old_nick = prefix.split('!')[0]
        new_nick = params[0]
        print("%s is now known as %s" % (old_nick, new_nick))

    def irc_PART(self, prefix, params):
        print prefix, "---", params

    def alterCollidedNick(self, nickname):
        return nickname + '0'

class AdapterFactory(protocol.ClientFactory):
    protocol = Adapter

    def __init__(self, window):
        self.window = window
        protocol.nickname = self.window.nickname

    @property
    def nickname(self):
        return self.window.nickname
    @property
    def channel(self):
        return self.window.channel_name

    def clientConnectionLost(self, connector, reason):
        print reason
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print reason
        reactor.stop()

class TableWindow(QMainWindow):
    def __init__(self):
        super(TableWindow, self).__init__()
        connection_prompt = ConnectionDialog(self)
        connection_prompt.exec_()

        enc = lambda s: s.encode('ascii', 'ignore')
        self.network_name = enc(connection_prompt.line_network.text())
        self.channel_name = enc(connection_prompt.line_channel.text())
        self.nickname = enc(connection_prompt.line_nick.text())

        fact = AdapterFactory(self)
        reactor.connectTCP(self.network_name, 6667, fact)

        self.player_list = QTreeWidget()
        self.player_list.setColumnCount(2)
        self.player_list.setHeaderLabels(['Nickname', 'Stack'])
        player_dock = QDockWidget(self.tr('Players'))
        allowed_areas = Qt.LeftDockWidgetArea|Qt.RightDockWidgetArea
        player_dock.setAllowedAreas(allowed_areas)
        player_dock.setWidget(self.player_list)
        self.addDockWidget(Qt.LeftDockWidgetArea, player_dock)

        notes = QTextEdit()
        notes_dock = QDockWidget(self.tr("Notes"))
        allowed_areas = Qt.LeftDockWidgetArea|Qt.RightDockWidgetArea
        notes_dock.setAllowedAreas(allowed_areas)
        notes_dock.setWidget(notes)
        self.addDockWidget(Qt.LeftDockWidgetArea, notes_dock)

        self.blank_card = self.load_card('flipside_black_simple')
        self.cards = (QLabel(), QLabel())
        self.cards[0].setPixmap(self.blank_card)
        self.cards[1].setPixmap(self.blank_card)

        self.fold_button = self.create_action_button('Fold')
        self.call_button = self.create_action_button('Call')
        self.raise_button = self.create_action_button('Raise')

        bottom_section = QWidget()
        bottom_layout = QHBoxLayout(bottom_section)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.cards[0])
        bottom_layout.addWidget(self.cards[1])
        bottom_layout.addSpacing(20)
        bottom_layout.addWidget(self.fold_button)
        bottom_layout.addWidget(self.call_button)
        bottom_layout.addWidget(self.raise_button)
        self.load_bottom_stylesheet(bottom_section)

        self.raise_edit_box = QLineEdit()
        valid_raise = QDoubleValidator(0.0, -1.0, 2, self.raise_edit_box)
        self.raise_edit_box.setValidator(valid_raise)
        self.raise_edit_box.setMaximumSize(40, 28)
        self.raise_edit_box.setText('1')
        self.raise_slider = QSlider(Qt.Vertical)
        self.raise_slider.setTickPosition(self.raise_slider.TicksBelow)
        slider_layout = QVBoxLayout()
        slider_layout.addWidget(self.raise_slider)
        slider_layout.addWidget(self.raise_edit_box)

        self.action_view = QTextEdit()
        self.action_view.setReadOnly(True)

        top_section = QWidget()
        top_layout = QHBoxLayout(top_section)
        top_layout.addWidget(self.action_view)
        top_layout.addLayout(slider_layout)

        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.addWidget(top_section)
        main_layout.addWidget(bottom_section)

        self.setCentralWidget(main_widget)
        self.create_actions()
        self.create_toolbars()
        self.show()

        # Set by dealer
        self.new_hand = False
        self.connected = False
        self.protocol = None

    def create_actions(self):
        self.join_action = QAction('Join', self, triggered=self.prompt_join)
        self.join_action.setEnabled(False)
        self.buyin_action = QAction('Buyin', self, triggered=self.prompt_buyin)
        self.buyin_action.setEnabled(False)
        self.sitin_action = QAction('Sit in', self,
                                    triggered=self.prompt_sitin)
        self.sitin_action.setEnabled(False)
        self.sitout_action = QAction('Sit out', self,
                                     triggered=self.prompt_sitout)
        self.sitout_action.setEnabled(False)

    def create_toolbars(self):
        self.toolbar = self.addToolBar('TableTool')
        self.toolbar.addAction(self.join_action)
        self.toolbar.addAction(self.buyin_action)
        self.toolbar.addAction(self.sitin_action)
        self.toolbar.addAction(self.sitout_action)

    def get_number_from_user(self):
        prompt = NumberDialog(self)
        prompt.exec_()
        return prompt.number

    def prompt_join(self):
        if self.protocol:
            seat_num = self.get_number_from_user()
            self.protocol.msg(self.channel_name, '!join %d'%seat_num)
            self.buyin_action.setEnabled(True)

    def prompt_buyin(self):
        if self.protocol:
            buyin = self.get_number_from_user()
            self.protocol.msg(self.channel_name, '!buyin %d'%buyin)
            self.sitin_action.setEnabled(True)

    def prompt_sitin(self):
        if self.protocol:
            self.protocol.msg(self.channel_name, '!sitin')
            self.sitin_action.setEnabled(False)
            self.sitout_action.setEnabled(True)

    def prompt_sitout(self):
        if self.protocol:
            self.protocol.msg(self.channel_name, '!sitout')
            self.sitin_action.setEnabled(True)
            self.sitout_action.setEnabled(False)

    def load_bottom_stylesheet(self, bottom_widget):
        if QDir.setCurrent('./data/gfx/table/default/'):
            bottom_widget.setStyleSheet(common.loadStyleSheet('style.css'))
        QDir.setCurrent('../../../../')

    def create_action_button(self, name):
        button = QPushButton(name)
        button.setObjectName(name + 'Button')
        button.setCheckable(True)
        button.setSizePolicy(QSizePolicy.Preferred,
                             QSizePolicy.Minimum)
        return button

    def load_card(self, cardname):
        full_path = 'data/gfx/cards/nobus/%s.png'%cardname
        image = QImage(full_path)
        return QPixmap.fromImage(image)

    def set_table(self, msg):
        if not self.connected:
            self.join_action.setEnabled(True)
            self.connected = True
        players = []
        dealer = msg['dealer']
        for i, seat in enumerate(msg['table']):
            if seat is not None:
                playname = seat['player']
                if seat['sittingout']:
                    playname = '/%s/'%playname
                if dealer == i:
                    playname = '* %s'%playname
                stack = str(seat['stack'])
                treeitem = QTreeWidgetItem([playname, stack])
                players.append(treeitem)
        self.player_list.clear()
        self.player_list.addTopLevelItems(players)

    def report_error(self, msg):
        error = msg['error']
        errmsg = msg['message']
        self.add_line('<font color="red">%s: %s</font>'%(error, errmsg))

    def chat_message(self, user, msg):
        self.add_line('%s says: %s'%(user, msg))

    def add_line(self, line):
        text = self.action_view.toHtml()
        text = '%s\n%s'%(text, line)
        self.action_view.setHtml(text)

    def process(self):
        app.processEvents()
        reactor.callLater(0, self.process)

    def closeEvent(self, event):
        print('Attempting to close the main window!')
        event.accept()
        reactor.stop()

if __name__ == '__main__':
    table = TableWindow()
    reactor.callLater(0, table.process)
    reactor.run()
