import script, table
from twisted.internet import reactor

class Schedule:
    def __init__(self):
        self.started = False
    def callback(self, functor, secs):
        # If already scheduled then make sure not to schedule event twice.
        if not self.started:
            print('A new game will begin in %d seconds.'%secs)
        started = True
        reactor.callLater(secs, functor)
    def clear(self):
        print('Cancelled callback.')

class Handler:
    """When the game starts then the table notifies this handler."""
    def __init__(self, adapter):
        self.running = False
        self.adapter = adapter
        self.script = None
        self.actIter = None
        self.currentAct = None
    def start(self, script):
        self.running = True
        self.script = script
        self.actIter = script.run()

        self.currentAct = self.actIter.next()
        self.displayAct()
    def displayAct(self):
        for line in self.currentAct.__repr__().split('\n'):
            self.adapter.reply(line)
    def update(self, player, response):
        if not self.running:
            return
        if player != self.currentAct.player.nickname:
            self.adapter.reply('Don\'t act out of turn!')
        try:
            self.currentAct = self.actIter.send(response)
            # handle cards dealt .etc here
            if isinstance(self.currentAct, script.CardsDealt):
                self.displayAct()
                self.currentAct = self.actIter.next()
            self.displayAct()
        except StopIteration:
            self.adapter.reply('END!!')
    def stop(self):
        self.running = False
        # award pot to remaining player sitting in.
        print 'stopped'

class Adapter:
    def __init__(self, prot, chan):
        reload(script)
        reload(table)
        self.prot = prot
        self.chan = chan
        self.cash = table.Table(9, 0.25, 0.5, 0, 5000, 25000)
        self.cash.registerScheduler(Schedule())
        self.handler = Handler(self)
        self.cash.registerHandler(self.handler)
        self.cash.setStartupDelayTime(1)

        ###
        self.cash.addPlayer('a', 0)
        self.cash.addPlayer('b', 1)
        self.cash.addPlayer('c', 2)
        self.cash.addPlayer('d', 3)
        self.cash.addMoney('a', 5000)
        self.cash.addMoney('b', 7000)
        self.cash.addMoney('c', 6000)
        self.cash.addMoney('d', 8000)
        self.cash.sitIn('a')
        self.cash.sitIn('b')
        self.cash.sitIn('c')
        self.cash.sitIn('d')
    def msg(self, user, message):
        print('%s: %s'%(user, message))
        message = message.split(' ')
        if message[0] == 'reg':
            self.cash.addPlayer(message[1], int(message[2]))
        elif message[0] == 'buyin':
            self.cash.addMoney(message[1], int(message[2]))
        elif message[0] == 'sitin':
            self.cash.sitIn(message[1])
        elif message[0] == 'sitout':
            self.cash.sitOut(message[1])
            self.handler.update(message[1], (script.Action.SitOut,))
        elif message[0] == 'postsb':
            self.handler.update(message[1], (script.Action.PostSB,))
        elif message[0] == 'postbb':
            self.handler.update(message[1], (script.Action.PostBB,))
        elif message[0] == 'postsbbb':
            self.handler.update(message[1], (script.Action.PostSBBB,))
        elif message[0] == 'call':
            self.handler.update(message[1], (script.Action.Call,))
        elif message[0] == 'fold':
            self.handler.update(message[1], (script.Action.Fold,))
        elif message[0] == 'raise':
            self.handler.update(message[1], (script.Action.Raise, \
                int(message[2])))
        elif message[0] == 'show':
            for line in self.cash.__repr__().split('\n'):
                self.reply(line)
            self.reply('Pots: %s'%self.handler.script.pots)
        print self.cash
    def reply(self, message):
        self.prot.msg(self.chan, message)
