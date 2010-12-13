from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
from twisted.python import log

import time, sys
import adapter

class GamerBot(irc.IRCClient):
    nickname = "donisto"

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)
        self.adapter = {}

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)

    # callbacks for events
    def signedOn(self):
        """Called when bot has succesfully signed on to server."""
        self.join(self.factory.channel)

    def joined(self, channel):
        """This will get called when the bot joins the channel."""
        if channel == '#pangaea':
            self.adapter[channel] = adapter.Adapter(self, channel)
        #self.msg(channel, "\x0304red friend =)\x03")
        """self.msg(channel, "\x0303green friend =)\x03")
        self.msg(channel, "\x0302blue friend =)\x03")
        self.msg(channel, "\x0314grey friend =)\x03")
        self.msg(channel, "\x0300,01 black friend =)\x03")"""
        #self.msg(channel, "\x0314[ \x03\x0304Ah\x03\x0314 ] [ \x03\x0303Jc\x03\x0314 ] [ \x03\x03027d\x03\x0314 ] [ \x03\x028s\x0314 ]\x03")

    def privmsg(self, user, channel, msg):
        """This will get called when the bot receives a message."""
        user = user.split('!', 1)[0]

        try:
            if msg == '!release':
                print('releasing')
                del self.adapter[channel]
            elif msg == '!reload':
                reload(adapter)
                self.adapter[channel] = adapter.Adapter(self, channel)
            elif msg.startswith('!exec '):
                exec(msg[len('!exec '):])
            elif msg[0] == '!':
                self.adapter[channel].msg(user, msg[1:])
            else:
                print("%s <%s> %s" % (channel, user, msg))
        except KeyError:
            pass
        
        # Check to see if they're sending me a private message
        if channel == self.nickname:
            msg = "It isn't nice to whisper!  Play nice with the group."
            self.msg(user, msg)
            return

        # Otherwise check to see if it is a message directed at me
        if msg.startswith(self.nickname + ":"):
            msg = "%s: I am a log bot" % user
            self.msg(channel, msg)
            print("<%s> %s" % (self.nickname, msg))

    def action(self, user, channel, msg):
        """This will get called when the bot sees someone do an action."""
        user = user.split('!', 1)[0]
        print("* %s %s" % (user, msg))

    # irc callbacks
    def irc_NICK(self, prefix, params):
        """Called when an IRC user changes their nickname."""
        old_nick = prefix.split('!')[0]
        new_nick = params[0]
        print("%s is now known as %s" % (old_nick, new_nick))

    # For fun, override the method that determines how a nickname is changed on
    # collisions. The default method appends an underscore.
    def alterCollidedNick(self, nickname):
        """
        Generate an altered version of a nickname that caused a collision in an
        effort to create an unused related name for subsequent registration.
        """
        return nickname + '^'

class GamerBotFactory(protocol.ClientFactory):
    """A factory for LogBots.

    A new protocol instance will be created each time we connect to the server.
    """
    # the class of the protocol to build when new connection is made
    protocol = GamerBot

    def __init__(self, channel):
        self.channel = channel

    def clientConnectionLost(self, connector, reason):
        """If we get disconnected, reconnect to server."""
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "connection failed:", reason
        reactor.stop()

if __name__ == '__main__':
    # initialize logging
    #log.startLogging(sys.stdout)
    
    # create factory protocol and application
    f = GamerBotFactory('#pangaea')

    # connect factory to this host and port
    #reactor.connectSSL
    reactor.connectTCP("irc.freenode.org", 6667, f)

    # run bot
    reactor.run()

