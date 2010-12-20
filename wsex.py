from PySide.QtCore import *
from PySide.QtGui import *
import sys

app = QApplication(sys.argv)

from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
from twisted.python import log

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

class Adapter(irc.IRCClient):        
    @property
    def nickname(self):
        return self.factory.nickname
    @property
    def channel(self):
        return self.factory.channel

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
       
    def privmsg(self, user, channel, msg):
        """Called when we receive a message."""
        if channel == self.channel:
            self.send_message('hello')

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

        textedit = QTextEdit()
        self.setCentralWidget(textedit)
        self.show()

    def process(self):
        app.processEvents()
        reactor.callLater(0, self.process)

    def closeEvent(self, event):
        print('Attempting to close the main window!')
        reactor.stop()
        event.accept()

if __name__ == '__main__':
    table = TableWindow()
    reactor.callLater(0, table.process)
    reactor.run()
