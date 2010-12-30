from twisted.internet import reactor
import json
import table
import script

debug_oneman = False
debug_nick = 'zipio'

class Schedule:
    def __init__(self, message):
        self.started = False
        self.message = message
    def callback(self, functor, secs):
        # If already scheduled then make sure not to schedule event twice.
        if not self.started:
            msg = 'A new game will begin in %d seconds.'%secs
            self.message(json.dumps({'update': 'newgame', 'message': msg}))
        started = True
        reactor.callLater(secs, functor)
    def clear(self):
        print('Cancelled callback.')

class Handler:
    """When the game starts then the table notifies this handler."""
    def __init__(self, adapter):
        self.adapter = adapter
        self.stop()

    def start(self, scriptObj):
        self.running = True
        self.script = scriptObj
        self.actIter = scriptObj.run()

        self.adapter.reply(json.dumps({'update': 'newhand',
                                       'message': '989332122236'}))
        self.adapter.show_table()

        while not isinstance(self.currentAct, script.Action):
            try:
                self.currentAct = self.actIter.next()
            except StopIteration:
                emptyscript = {'internalerror': 'emptyscript',
                               'message': "script didn't do anything!"}
                self.adapter.reply(json.dumps(emptyscript))
            else:
                self.displayAct()
    def pmHands(self, cardsDealt):
        players = cardsDealt.players
        for player in players:
            c = cardsDealt.get_player_hand(player)
            if not debug_oneman:
                self.adapter.privmsg(player.nickname, {'cards': c})
            else:
                self.adapter.privmsg(debug_nick, {'cards': c})
    def displayAct(self):
        if isinstance(self.currentAct, script.CardsDealt):
            self.pmHands(self.currentAct)
        else:
            self.adapter.reply(json.dumps(self.currentAct.notation()))
    def update(self, player, response):
        if not self.running:
            return
        if player is None:
            # Only valid for debugging!
            noplay = {'error': 'noplayer',
                      'message': "You didnt't specify a player."}
            self.adapter.reply(json.dumps(noplay))
            return
        elif (isinstance(self.currentAct, script.Action) and
              player != self.currentAct.player.nickname):
            # People are allowed to sit out, out of turn
            if (response[0] != script.Action.SitOut and
                response[0] != script.Action.AutopostBlinds):
                outturn = {'error': 'notyourturn',
                           'message': "Don't act out of turn."}
                self.adapter.reply(json.dumps(outturn))
                return
        if response[0] not in self.currentAct.actionNames():
            invalidact = {'error': 'invalidaction',
                          'message': 'Invalid action specified.'}
            self.adapter.reply(json.dumps(invalidact))
            return
        try:
            self.currentAct = self.actIter.send(response)
            # handle cards dealt .etc here
            while not isinstance(self.currentAct, script.Action):
                self.displayAct()
                self.currentAct = self.actIter.next()
            self.displayAct()
        except StopIteration:
            #self.adapter.reply('END!!')
            # if adapter stops then this becomes none.
            if self.script is not None:
                # restart next hand.
                self.start(self.script)
    def stop(self):
        self.running = False
        self.script = None
        self.actIter = None
        self.currentAct = None
        # award pot to remaining player sitting in.
        gamestopped = {'update': 'gamestopped',
                       'message': 'Game halted.'}
        self.adapter.reply(json.dumps(gamestopped))
        print 'stopped'

class Adapter:
    def __init__(self, prot, chan):
        reload(script)
        reload(table)
        self.prot = prot
        self.chan = chan
        self.cash = table.Table(9, 0.25, 0.5, 0, 5000, 25000)
        self.cash.registerScheduler(Schedule(self.reply))
        self.handler = Handler(self)
        self.cash.registerHandler(self.handler)
        self.cash.setStartupDelayTime(0)

        ###
        if debug_oneman:
            self.cash.addPlayer('a', 0)
            self.cash.addPlayer('b', 1)
            self.cash.addPlayer('c', 2)
            self.cash.addPlayer('d', 3)
            self.cash.addMoney('a', 5000)
            self.cash.addMoney('b', 5000)
            self.cash.addMoney('c', 6000)
            self.cash.addMoney('d', 8000)
            self.cash.sitIn('a')
            self.cash.sitIn('b')
            self.cash.sitIn('c')
            self.cash.sitIn('d')
            self.cash.setAutopost('a', True)
            self.cash.setAutopost('b', True)
            self.cash.setAutopost('c', True)
            self.cash.setAutopost('d', True)

    def debug_strip(self, message):
        message = message.split(' ')
        command = message[0]
        if len(message) > 1:
            player = message[1]
            if len(message) > 2:
                param = message[2]
            else:
                param = None
        else:
            player = None
            param = None
        return player, command, param

    def strip_message(self, user, message):
        player = user
        try:
            command, param = message.split(' ')
        except ValueError:
            command = message
            param = None
        return player, command, param

    def msg(self, user, message):
        print('%s: %s'%(user, message))

        if debug_oneman:
            player, command, param = self.debug_strip(message)
        else:
            player, command, param = self.strip_message(user, message)

        if self.cash is not None:
            print self.cash

        # Make command lower case for clumsy users
        command = command.lower()
        try:
            self.runCommand(player, command, param)
        except Exception as e:
            self.reply(json.dumps({'error': e.__class__.__name__,
                                   'message': str(e)}))
            raise

    def show_table(self):
        notate = {'dealer': self.cash.dealer}
        seats = []
        for s in self.cash.seats:
            if s is None:
                seats.append(None)
            else:
                seats.append({'player': s.nickname, 'stack': s.stack,
                              'sittingout': s.sitting_out})
        notate['seats'] = seats
        #notate['table'] = self.chan
        self.reply(json.dumps(notate))

    def runCommand(self, player, command, param):
        if command == 'join':
            seat = int(param)
            self.cash.addPlayer(player, seat)
            joined = {'update': 'playerjoin',
                      'player': player, 'seat': seat}
            self.reply(json.dumps(joined))
        elif command == 'buyin':
            buyin = int(param)
            seat, player_object = self.cash.lookupPlayer(player)
            if not self.cash.addMoney(player_object, buyin):
                buyin = {'update': 'rebuyafterhand', 'player': player,
                         'buyin': buyin}
            else:
                buyin = {'update': 'playerbuyin', 'player': player,
                         'stack': player_object.stack, 'buyin': buyin}
            self.reply(json.dumps(buyin))
        elif command == 'sitin':
            self.cash.sitIn(player)
            sitin = {'update': 'playersitin', 'player': player}
            self.reply(json.dumps(sitin))
        elif command == 'sitout':
            self.cash.sitOut(player)
            self.handler.update(player, (script.Action.SitOut,))
            sitout = {'update': 'playersitout', 'player': player}
            self.reply(json.dumps(sitout))
        elif command == 'autopost':
            self.cash.setAutopost(player, True)
            self.handler.update(player, (script.Action.AutopostBlinds,))
        elif command == 'postsb':
            self.handler.update(player, (script.Action.PostSB,))
        elif command == 'postbb':
            self.handler.update(player, (script.Action.PostBB,))
        elif command == 'postsbbb':
            self.handler.update(player, (script.Action.PostSBBB,))
        elif command == 'call':
            self.handler.update(player, (script.Action.Call,))
        elif command == 'check':
            self.handler.update(player, (script.Action.Check,))
        elif command == 'fold':
            self.handler.update(player, (script.Action.Fold,))
        elif command == 'bet':
            self.handler.update(player, (script.Action.Bet, int(param)))
        elif command == 'raise':
            self.handler.update(player, (script.Action.Raise, int(param)))
        elif command == 'show':
            self.show_table()

    def reply(self, message):
        self.prot.msg(self.chan, message)
    def privmsg(self, user, message):
        message['table'] = self.chan
        self.prot.msg(user, '%s'%json.dumps(message))

