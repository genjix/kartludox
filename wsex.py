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
                elif 'status' in dealmsg:
                    self.window.report_status(dealmsg)
                elif 'actions' in dealmsg:
                    self.window.allow_actions(dealmsg)
                elif 'flop' in dealmsg:
                    self.window.show_flop(dealmsg)
                elif 'turn' in dealmsg:
                    self.window.show_turn(dealmsg)
                elif 'river' in dealmsg:
                    self.window.show_river(dealmsg)
                elif 'showhands' in dealmsg:
                    self.window.show_hands(dealmsg)
                elif 'showrankings' in dealmsg:
                    self.window.show_rankings(dealmsg)
                elif 'collected' in dealmsg:
                    self.window.show_collected(dealmsg)
                elif 'uncalled' in dealmsg:
                    self.window.show_uncalled(dealmsg)
                else:
                    print dealmsg
            else:
                if msg[0] == '!':
                    self.window.show_action(user, msg[1:])
                else:
                    self.window.chat_message(user, msg)
        elif channel == self.nickname and user == dealername:
            dealmsg = json.loads(msg)
            if 'cards' in dealmsg:
                self.window.show_hand(dealmsg)

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
        self.blank_cards()

        self.fold_button = self.create_action_button('Fold')
        self.fold_button.clicked.connect(self.fold_clicked)
        self.call_button = self.create_action_button('Call')
        self.call_button.clicked.connect(self.call_clicked)
        self.raise_button = self.create_action_button('Raise')
        self.raise_button.clicked.connect(self.raise_clicked)

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
        self.raise_edit_box.textChanged.connect(self.raise_box_changed)
        self.raise_slider.valueChanged.connect(self.raise_slider_changed)

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

        self.hide_actions()

        self.current_actions = None

    def raising_range(self):
        if 'raise' in self.current_actions:
            return self.current_actions['raise']
        return 1, 1

    def raise_box_changed(self, value):
        try:
            value = float(value)
        except ValueError:
            return
        else:
            ra, rb = self.raising_range()
            interval = rb - ra
            if interval == 0:
                value = ra
            else:
                value = 99.0 * (value - ra) / interval
            self.raise_slider.setValue(round(value))

    def raise_slider_changed(self, value):
        # Slider is between 0 and 99.
        ra, rb = self.raising_range()
        interval = rb - ra
        i = value / 99.0
        value = i*interval + ra
        raise_text = '%.0f'%value
        self.raise_edit_box.setText(raise_text)
        self.raise_button.setText('Raise %s'%raise_text)

    def blank_cards(self):
        self.cards[0].setPixmap(self.blank_card)
        self.cards[1].setPixmap(self.blank_card)

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

    def send_command(self, command):
        self.protocol.msg(self.channel_name, '!%s'%command)
        # hack! should never do this!!
        self.protocol.msg(self.channel_name, '!show')
        self.show_action(self.nickname, command)

    def prompt_join(self):
        if self.protocol:
            seat_num = self.get_number_from_user()
            self.send_command('join %d'%seat_num)
            self.buyin_action.setEnabled(True)

    def prompt_buyin(self):
        if self.protocol:
            buyin = self.get_number_from_user()
            self.send_command('buyin %d'%buyin)
            self.sitin_action.setEnabled(True)

    def prompt_sitin(self):
        if self.protocol:
            self.send_command('sitin')
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
        if self.new_hand:
            self.new_hand = False
            for i, seat in enumerate(msg['table']):
                if seat is None:
                    self.add_line('Seat %d: -'%i)
                else:
                    stack = seat['stack']
                    playname = seat['player']
                    if seat['sittingout']:
                        playname = '/%s/'%playname
                    self.add_line('Seat %d: %s (%d BTC)'%(i, playname, stack))
            dealname = msg['table'][msg['dealer']]['player']
            self.add_line('%s is the dealer'%dealname)
        self.player_list.clear()
        self.player_list.addTopLevelItems(players)

    def report_error(self, msg):
        error = msg['error']
        errmsg = msg['message']
        self.add_line('<font color="red">%s: %s</font>'%(error, errmsg))

    def report_status(self, msg):
        status = msg['status']
        stmsg = msg['message']
        self.add_line('<b>%s: %s</b>'%(status, stmsg))
        if status == 'newhand':
            self.new_hand = True
            self.blank_cards()
            self.hide_actions()

    def allow_actions(self, msg):
        self.hide_actions()
        if msg['player'] != self.nickname:
            return
        self.activateWindow()
        self.raise_()
        actions = msg['actions']
        if 'postsb' in actions:
            self.fold_button.setText('SB %d'%actions['postsb'][0])
            self.fold_button.show()
        elif 'postbb' in actions:
            self.fold_button.setText('BB %d'%actions['postbb'][0])
            self.fold_button.show()
        elif 'postsbbb' in actions:
            self.fold_button.setText('SB+BB %d'%actions['postsbbb'][0])
            self.fold_button.show()
        else:
            self.fold_button.setText('Fold')
            self.fold_button.show()
            if 'check' in actions:
                self.call_button.setText('Check')
                self.call_button.show()
            elif 'call' in actions:
                self.call_button.setText('Call %d'%actions['call'][0])
                self.call_button.show()
            if 'raise' in actions:
                raise_range = actions['raise']
                raise_text = str(raise_range[0])
                self.raise_button.setText('Raise %s'%raise_text)
                self.raise_edit_box.setText(raise_text)
                self.raise_button.show()
                self.raise_edit_box.show()
                self.raise_slider.show()
            elif 'bet' in actions:
                ###
                pass
        self.current_actions = actions

    def fold_clicked(self):
        acts = self.current_actions
        if 'postsb' in acts:
            self.send_command('postsb')
        elif 'postbb' in acts:
            self.send_command('postbb')
        elif 'postsbbb' in acts:
            self.send_command('postsbbb')
        elif 'fold' in acts:
            self.send_command('fold')
        else:
            raise Exception('no other fold action with this button!')

    def call_clicked(self):
        acts = self.current_actions
        if 'check' in acts:
            self.send_command('check')
        elif 'call' in acts:
            self.send_command('call')

    def raise_clicked(self):
        acts = self.current_actions
        if 'raise' in acts:
            try:
                bet = int(self.raise_edit_box.text())
            except ValueError:  
                self.send_command('raise %d'%acts['raise'][0])
            else:
                self.send_command('raise %d'%bet)

    def hide_actions(self):
        self.fold_button.hide()
        self.call_button.hide()
        self.raise_button.hide()
        self.raise_edit_box.hide()
        self.raise_slider.hide()

    def chat_message(self, user, msg):
        self.add_line('%s says: %s'%(user, msg))

    def add_line(self, line):
        text = self.action_view.toHtml()
        text = '%s<br />%s'%(text, line)
        self.action_view.setHtml(text)
        sb = self.action_view.verticalScrollBar()
        sb.setSliderPosition(sb.maximum())

    def show_hand(self, msg):
        hand = msg['cards']
        for i, card in enumerate(hand):
            cardpix = self.load_card(card)
            self.cards[i].setPixmap(cardpix)

    def get_html_card(self, cardname):
        return "<img src='data/gfx/cards/nobus/%s.png' />"%cardname

    def show_flop(self, msg):
        c = self.get_html_card
        flop = msg['flop']
        pots = msg['pots']
        total_potsize = 0
        for p in pots:
            total_potsize += p['size']
        self.add_line('<br /><b>Flop</b> (Pot: %d BTC)<br />%s %s %s'%(
            total_potsize, c(flop[0]), c(flop[1]), c(flop[2])))

    def show_turn(self, msg):
        c = self.get_html_card
        flop = msg['turn']
        pots = msg['pots']
        total_potsize = 0
        for p in pots:
            total_potsize += p['size']
        self.add_line('<br /><b>Turn</b> (Pot: %d BTC)<br />%s %s %s %s'%(
            total_potsize, c(flop[0]), c(flop[1]), c(flop[2]), c(flop[3])))

    def show_river(self, msg):
        c = self.get_html_card
        flop = msg['river']
        pots = msg['pots']
        total_potsize = 0
        for p in pots:
            total_potsize += p['size']
        self.add_line('<br /><b>River</b> (Pot: %d BTC)<br />%s %s %s %s %s'%(
            total_potsize, c(flop[0]), c(flop[1]), c(flop[2]), c(flop[3]),
            c(flop[4])))

    def show_action(self, user, msg, hero=False):
        if 'raise' in msg:
            msg = msg.split(' ')
            msg = msg[0], int(msg[1])
            peract = 'raises to %d'%msg[1]
        elif 'call' in msg:
            peract = 'calls'
        elif 'check' in msg:
            peract = 'checks'
        elif 'postsb' in msg:
            peract = 'posts small blind'
        elif 'postbb' in msg:
            peract = 'posts big blind'
        elif 'postsbbb' in msg:
            peract = 'posts small and big blind'
        elif 'fold' in msg:
            peract = 'folds'
        elif ('show' in msg or 'join' in msg or 'buyin' in msg):
            return
        elif 'sitin' in msg:
            peract = 'sits in'
        elif 'sitout' in msg:
            peract = 'sits out'
        elif 'buyin' in msg:
            msg = msg.split(' ')
            msg = msg[0], int(msg[1])
            peract = 'adds %d to the table.'%msg[1]
        else:
            print 'ERROR:', msg
            peract = None
        if peract is not None:
            if hero:
                self.add_line('<font color="green">%s: %s</font>'%(user, peract))
            else:
                self.add_line('%s: %s'%(user, peract))

    def show_hands(self, msg):
        c = self.get_html_card
        for contest in msg['showhands']:
            player = contest['player']
            cards = contest['cards']
            self.add_line('%s shows %s %s'%(player, c(cards[0]), c(cards[1])))

    def show_rankings(self, msg):
        for contest in msg['showrankings']:
            player = contest['player']
            handname = contest['handname']
            self.add_line('%s has %s'%(player, handname))

    def show_collected(self, msg):
        player = msg['player']
        amount = msg['collected']
        self.add_line('%s collected %d BTC from the pot.'%(player, amount))

    def show_uncalled(self, msg):
        player = msg['player']
        uncalled = msg['uncalled']
        self.add_line('Uncalled bet of %d BTC returned to %s.'%(uncalled, player))

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
