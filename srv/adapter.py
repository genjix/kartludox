from twisted.internet import reactor
import re
import json
import table
import script

class Schedule:
    def __init__(self, send_json):
        self.started = False
        self.send_json = send_json
    def callback(self, functor, secs):
        # If already scheduled then make sure not to schedule event twice.
        if not self.started:
            msg = 'A new game will begin in %d seconds.'%secs
            self.send_json({'update': 'new game', 'message': msg})
        started = True
        reactor.callLater(secs, functor)
    def clear(self):
        print('Cancelled callback.')

class Handler:
    """When the game starts then the table notifies this handler."""
    def __init__(self, adapter):
        self.adapter = adapter
        self.stop()

    def start(self, script_obj):
        self.running = True
        self.script = script_obj
        self.actIter = script_obj.run()

        self.send_json({'update': 'new hand',
                                       'message': '989332122236'})
        self.adapter.show_table()

        while not isinstance(self.current_action, script.Action):
            try:
                self.current_action = self.actIter.next()
            except StopIteration:
                emptyscript = {'internal error': 'empty script',
                               'message': "script didn't do anything!"}
                self.send_json(emptyscript)
            else:
                self.display_action()

    def privmsg_hands(self, cardsDealt):
        players = cardsDealt.players
        for player in players:
            c = cardsDealt.get_player_hand(player)
            self.adapter.privmsg(player.nickname, {'cards': c})

    def display_action(self):
        if isinstance(self.current_action, script.CardsDealt):
            self.privmsg_hands(self.current_action)
        else:
            self.send_json(self.current_action.notation())

    def update(self, player, response):
        if not self.running:
            return
        if player is None:
            # Only valid for debugging!
            noplay = {'error': 'no player',
                      'message': "You didnt't specify a player."}
            self.send_json(noplay)
            return
        elif (isinstance(self.current_action, script.Action) and
              player != self.current_action.player.nickname):
            # People are allowed to sit out, out of turn
            if (response[0] != script.Action.SIT_OUT and
                response[0] != script.Action.AUTOPOST_BLINDS):
                outturn = {'error': 'not your turn',
                           'message': "Don't act out of turn."}
                self.send_json(outturn)
                return
        if response[0] not in self.current_action.action_names():
            invalidact = {'error': 'invalid action',
                          'message': 'Invalid action specified.'}
            self.send_json(invalidact)
            return
        # Check that passed argument is a valid size if it exists
        selected = self.current_action.find(response[0])
        if len(selected) == 3:   # actname, minsize, maxsize
            assert(len(response) > 1)
            if response[1] < selected[1]:
                toosmall = {'error': 'invalid small arg',
                            'message': 'Argument size is too small.',
                            'min': selected[1], 'arg': response[1]}
                self.send_json(toosmall)
                return
            elif response[1] > selected[2]:
                toobig = {'error': 'invalid big arg',
                          'message': 'Argument size is too big.',
                          'min': selected[2], 'arg': response[1]}
                self.send_json(toobig)
                return
        try:
            self.current_action = self.actIter.send(response)
            # handle cards dealt .etc here
            while not isinstance(self.current_action, script.Action):
                self.display_action()
                self.current_action = self.actIter.next()
            self.display_action()
        except StopIteration:
            # if adapter stops then this becomes none.
            if self.script is not None:
                # restart next hand.
                self.start(self.script)

    def stop(self):
        self.running = False
        self.script = None
        self.actIter = None
        self.current_action = None
        # award pot to remaining player sitting in.
        gamestopped = {'update': 'game stopped',
                       'message': 'Game halted.'}
        self.send_json(gamestopped)

    def send_json(self, notation):
        self.adapter.send_json(notation)

class NoParameter(Exception):
    def __init__(self, nickname, command):
        self.nickname = nickname
        self.command = command
    def notation(self):
        return {'command': self.command, 'player': self.nickname}
    def __str__(self):
        return "Command '%s' requires an argument"

class Adapter:
    def __init__(self, prot, chan):
        reload(script)
        reload(table)
        self.prot = prot
        self.chan = chan
        self.cash = table.Table(9, 0.25, 0.5, 0, 5000, 25000)
        self.cash.register_scheduler(Schedule(self.send_json))
        self.handler = Handler(self)
        self.cash.register_handler(self.handler)
        #self.cash.startup_delay_time = 0

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

        player, command, param = self.strip_message(user, message)

        if self.cash is not None:
            print self.cash

        # Make command lower case for clumsy users
        command = command.lower()
        try:
            self.run_cmd(player, command, param)
        except Exception as e:
            if hasattr(e, 'notation'):
                notation = e.notation()
            else:
                notation = {}
            # This block converts BuyinTooSmall -> buyin too small
            replacement = lambda match: ' %s'%match.group(1).lower()
            classname = e.__class__.__name__
            classname = re.sub(r'([A-Z])', replacement, classname)[1:]
            # Use that class name for the error message title.
            notation['error'] = classname
            notation['message'] = str(e)
            self.send_json(notation)
            raise

    def show_table(self):
        notate = {'dealer': self.cash.dealer}
        seats = []
        for s in self.cash.seats:
            if s is None:
                seats.append(None)
            else:
                seats.append({'player': s.nickname, 'stack': s.stack,
                              'sitting out': s.sitting_out})
        notate['seats'] = seats
        #notate['table'] = self.chan
        self.send_json(notate)

    def leave(self, nickname):
        """Make a player leave the table. Called by the protocol."""
        seat, player = self.cash.lookup_player(nickname)
        self.cash.sit_out(player)
        self.cash.empty_seat(player, seat)

    def run_cmd(self, nickname, command, param):
        # Actions not requiring table registration
        if command == 'join':
            if param is None:
                raise NoParameter(nickname, command)
            seatid = int(param)
            self.cash.add_player(nickname, seatid)
            joined = {'update': 'player join', 'player': nickname,
                      'seat': seatid}
            self.send_json(joined)
            return
        elif command == 'show':
            self.show_table()
            return

        # Actions that DO require registration
        seat, player = self.cash.lookup_player(nickname)
        if command == 'leave':
            self.leave(nickname)
        elif command == 'buyin':
            if param is None:
                raise NoParameter(nickname, command)
            buyin = int(param)
            if not self.cash.add_money(player, buyin):
                buyin = {'update': 'rebuy after hand', 'player': nickname,
                         'buyin': buyin}
            else:
                buyin = {'update': 'player buyin', 'player': nickname,
                         'stack': player.stack, 'buyin': buyin}
            self.send_json(buyin)
        elif command == 'sitin':
            self.cash.sit_in(player)
            sitin = {'update': 'player sitin', 'player': nickname}
            self.send_json(sitin)
        elif command == 'sitout':
            # sitting out should always happen before the action itself
            sitout = {'update': 'player sitout', 'player': nickname}
            self.send_json(sitout)
            self.cash.sit_out(player)
            self.handler.update(nickname, (script.Action.SIT_OUT,))
        elif command == 'autopost':
            self.cash.setAutopost(player, True)
            self.handler.update(nickname, (script.Action.AUTOPOST_BLINDS,))
        elif command == 'postsb':
            self.handler.update(nickname, (script.Action.POST_SB,))
        elif command == 'postbb':
            self.handler.update(nickname, (script.Action.POST_BB,))
        elif command == 'postsbbb':
            self.handler.update(nickname, (script.Action.POST_SB_BB,))
        elif command == 'call':
            self.handler.update(nickname, (script.Action.CALL,))
        elif command == 'check':
            self.handler.update(nickname, (script.Action.CHECK,))
        elif command == 'fold':
            self.handler.update(nickname, (script.Action.FOLD,))
        elif command == 'bet':
            if param is None:
                raise NoParameter(nickname, command)
            self.handler.update(nickname, (script.Action.BET, int(param)))
        elif command == 'raise':
            if param is None:
                raise NoParameter(nickname, command)
            self.handler.update(nickname, (script.Action.RAISE, int(param)))

    def send_json(self, notation):
        self.prot.msg(self.chan, json.dumps(notation))

    def privmsg(self, user, message):
        message['table'] = self.chan
        self.prot.msg(user, '%s'%json.dumps(message))

