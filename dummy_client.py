from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
import curses
import json

class Adapter(irc.IRCClient):
    @property
    def nickname(self):
        return self.factory.nickname

    @property
    def channel(self):
        return self.factory.channel

    @property
    def screen(self):
        return self.factory.screen

    @property
    def dealer_name(self):
        return 'donisto'

    def gather_input(self):
        return ''

    def signedOn(self):
        """Called when bot has succesfully signed on to server."""
        self.join(self.channel)

    def joined(self, channel):
        if channel != self.channel:
            return
        self.screen.set_adapter(self)

    def format_json(self, frame):
        output_strs = json.dumps(frame, indent=4).split('\n')
        if not output_strs:
            raise StopIteration
        is_first = True
        for s in output_strs:
            if not any(c in s for c in '{}'):
                s = s.replace('"', '')
                s = s.replace(',', '')
                s = s.replace('[', '')
                s = s.replace(']', '')
                if not s.strip():
                    continue
                yield is_first, s
                if is_first:
                    is_first = False

    def load_json(self, msg):
        try:
            frame = json.loads(msg)
        except ValueError:
            errorcol = self.screen.Error
            self.screen.add_line(errorcol, 'BAD DEALER MESSAGE -----')
            self.screen.add_line(errorcol, msg)
            self.screen.add_line(errorcol, '------------------------')
            return None
        else:
            return frame

    def privmsg(self, user, channel, msg):
        user = user.split('!', 1)[0]
        if channel != self.channel:
            if self.nickname == channel and user == self.dealer_name:
                frame = self.load_json(msg)
                if frame:
                    tablename = frame['table']
                    c = frame['cards']
                    line = 'Dealt on %s [%s %s]'%(tablename, c[0], c[1])
                    coltype = self.screen.Private
                    self.screen.add_line(coltype, line)
            else:
                msg = '%s <%s> %s'%(channel, user, msg)
                self.screen.add_line(self.screen.Normal, msg)
                self.screen.redisplay()
            return
        if user == self.dealer_name:
            frame = self.load_json(msg)
            if frame:
                for is_first, line in self.format_json(frame):
                    if is_first:
                        self.screen.add_line(self.screen.DealerSpecial, line)
                    else:
                        self.screen.add_line(self.screen.Dealer, line)
                if 'actions' in frame and frame['player'] == self.nickname:
                    response = self.gather_input()
                    self.speak(response)
                    self.screen.add_line(self.screen.Action, '> %s'%response)
        else:
            if msg[0] == '!':
                self.screen.add_line(self.screen.Action, 
                                     '%s: %s'%(user, msg[1:]))
            else:
                self.screen.add_line(self.screen.Speech,
                                     '%s says: %s'%(user, msg))
        self.screen.redisplay()

    def speak(self, msg):
        self.say(self.channel, msg)

    def alterCollidedNick(self, nickname):
        return nickname + '_'

class AdapterFactory(protocol.ClientFactory):
    protocol = Adapter

    def __init__(self, channel, nickname, screen):
        self.channel = channel
        self.nickname = nickname
        self.screen = screen

    def clientConnectionLost(self, connector, reason):
        """If we get disconnected, reconnect to server."""
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "connection failed:", reason
        reactor.stop()

class Screen:
    def fileno(self):   return 0
    def logPrefix(self): return 'CursesClient'

    @property
    def rows(self):
        return self.stdscr.getmaxyx()[0]

    @property
    def columns(self):
        return self.stdscr.getmaxyx()[1]

    Normal = 1
    Speech = 2
    Dealer = 3
    DealerSpecial = 4
    Action = 5
    Error = 6
    Private = 7

    def __init__(self, stdscr):
        self.stdscr = stdscr

        # screen attributes
        curses.cbreak()
        curses.curs_set(0)
        self.stdscr.nodelay(1)
        self.stdscr.keypad(1)

        self.lines = []
        self.input_text = ''
        self.adapter = None
        self.offset = 0

        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(self.Normal, curses.COLOR_BLACK, -1)
        curses.init_pair(self.Speech, curses.COLOR_GREEN, -1)
        curses.init_pair(self.Dealer, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(self.DealerSpecial,
                         curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(self.Action, curses.COLOR_MAGENTA, -1)
        curses.init_pair(self.Error, curses.COLOR_RED, -1)
        curses.init_pair(self.Private,
                         curses.COLOR_BLACK, curses.COLOR_WHITE)

        self.redisplay()

    def set_adapter(self, adapter):
        self.adapter = adapter
    
    def add_line(self, colour, text):
        colour = curses.color_pair(colour)
        self.lines.append((colour, text))

    def redisplay(self):
        self.stdscr.clear()
        self.stdscr.border(0)
        window_rows = self.rows - 3
        for i in range(window_rows):
            lindex = i + self.offset
            if len(self.lines) > window_rows:
                lindex += len(self.lines) - window_rows
            if lindex >= len(self.lines):
                break
            elif lindex < 0:
                self.stdscr.addstr(i + 1, 1, '', self.Normal)
            else:
                col, line = self.lines[lindex]
                self.stdscr.addstr(i + 1, 1, line, col)
        self.redisplay_input()
        self.stdscr.refresh()

    def redisplay_input(self):
        # paint grey background box
        remainlen = self.columns - len(self.input_text) - 3
        rowtext = self.input_text + remainlen * ' '
        self.stdscr.addstr(self.rows - 2, 1, rowtext)
        self.stdscr.move(self.rows - 2, len(self.input_text))
        self.stdscr.refresh()

    def doRead(self):
        curses.noecho()
        c = self.stdscr.getch()
        if c == curses.KEY_BACKSPACE:
            if self.input_text:
                self.input_text = self.input_text[:-1]
        elif (c == curses.KEY_ENTER or c == 10):
            if self.input_text and self.adapter is not None:
                if self.input_text[0] == '!':
                    heroact = self.input_text[1:]
                    self.add_line(self.Action, 'Hero: %s'%heroact)
                else:
                    speech = 'Hero says: %s'%self.input_text
                    self.add_line(self.Speech, speech)
                self.adapter.speak(self.input_text)
                self.input_text = ''
        elif c == curses.KEY_DOWN:
            self.offset += 1
        elif c == curses.KEY_UP:
            self.offset -= 1
        elif c == curses.KEY_PPAGE:
            self.offset -= 10
        elif c == curses.KEY_NPAGE:
            self.offset += 10
        elif c > 256:
            return
        else:
            if len(self.input_text) < self.columns - 3:
                self.input_text += chr(c)
        self.redisplay()

    def connectionLost(self, reason):
        self.close()

    def close(self):
        curses.nocbreak()
        self.stdscr.keypad(0)
        curses.echo()
        curses.endwin()

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        nickname = sys.argv[1]
    else:
        nickname = 'zipio'
    stdscr = curses.initscr()
    screen = Screen(stdscr)
    stdscr.refresh()
    factory = AdapterFactory('#pangaea', nickname, screen)
    reactor.addReader(screen)
    reactor.connectTCP('irc.freenode.org', 6667, factory)
    reactor.run()
    screen.close()
