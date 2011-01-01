import random
import time
import script

convFact = 100
def tiny_to_real(tinybb, bigblind):
    """All calculations are done in terms of tiny bb's.
    A tiny bb = 1 bb / 100
    This function converts from tiny bb -> real money"""
    return tinybb * bigblind / float(convFact)
def real_to_tiny(real, bigblind):
    """See tinyToReal."""
    return int(real * convFact / float(bigblind))

class Player(object):
    PaidNothing = 0
    WaitingBB = 1
    PaidBB = 2
    PaidSBBB = 3

    PAID_NOTHING = 0
    WAITING_BB = 1
    PAID_BB = 2
    PAID_SB_BB = 3

    @classmethod
    def paid_repr(cls, state):
        if state == cls.PAID_NOTHING:
            return '-'
        elif state == cls.WAITING_BB:
            return '*'
        elif state == cls.PAID_BB:
            return 'bb'
        elif state == cls.PAID_SB_BB:
            return 'sb/bb'
        raise Exception('Internal Error: No such paid state %i')

    class Settings:
        def __init__(self, parent):
            self.parent = parent
            self.autopost = False

    def __init__(self, nickname):
        self.nickname = nickname
        self.stack = 0
        self.paid_state = Player.PAID_NOTHING
        self.sitting_out = True
        self.cards = None
        # Stores bets and actions by player
        self.bettor = None
        self.settings = self.Settings(self)

    def link(self, bettor):
        self.bettor = bettor
        self.bettor.add_parent(self)

    def __repr__(self):
        if self.cards:
            cards_repr = '[%s %s]'%self.cards
        else:
            cards_repr = '[--]'
        sitout_str = self.sitting_out and 'Out' or 'In'
        paids_str = Player.paid_repr(self.paid_state)
        return '%s (%g bb) %s Sitting %s %s'%(self.nickname, self.stack/100.0,
                                              cards_repr, sitout_str,
                                              paids_str)

class Schedule:
    def __init__(self):
        self.started = False
    def callback(self, functor, secs):
        # If already scheduled then make sure not to schedule event twice.
        if not self.started:
            print('A new game will begin in %d seconds.'%secs)
        started = True
        #functor()
    def clear(self):
        print('Cancelled callback.')

class Handler:
    """When the game starts then the table notifies this handler."""
    def start(self, script):
        print 'hello'
    def stop(self):
        print 'stop'

class GameState:
    STOPPED = 0
    STARTING = 1
    RUNNING = 2
    HALTING = 3

class Table:
    class InvalidSeat(Exception):
        def __init__(self, nickname, seatid):
            self.nickname = nickname
            self.seatid = seatid
        def notation(self):
            return {'player': self.nickname, 'seatid': self.seatid}
        def __str__(self):
            return 'Invalid seat ID %d'%self.seatid

    class WrongPlayerInSeat(Exception):
        def __init__(self, nickname, other_nickname, seatid):
            self.nickname = nickname
            self.other_nickname = other_nickname
            self.seatid = seat
        def notation(self):
            return {'player': self.nickname, 'seatid': seatid,
                    'other nickname': self.other_nickname}
        def __str__(self):
            return 'Internal Error: %s seated at seat %d claimed by %s'% \
                (self.nickname, self.seatid, self.other_nickname)

    class SeatTaken(Exception):
        def __init__(self, nickname, seatid, other_nickname):
            self.nickname = nickname
            self.seatid = seatid
            self.other_nickname = other_nickname
        def notation(self):
            return {'seatid': self.seatid, 'player': self.nickname,
                    'other player': self.other_nickname}
        def __str__(self):
            return "Seat %d already taken by player '%s'"%(self.seatid,
                                                           self.other_nickname)

    class NoSuchPlayer(Exception):
        def __init__(self, nickname):
            self.nickname = nickname
        def notation(self):
            return {'player': self.nickname}
        def __str__(self):
            return "No such nickname '%s'"%self.nickname

    class BuyinNegative(Exception):
        def __init__(self, nickname, amount, stack_size):
            self.nickname = nickname
            self.amount = amount
            self.stack_size = stack_size
        def notation(self):
            return {'player': self.nickname, 'amount': self.amount,
                    'stacksize': self.stack_size}
        def __str__(self):
            return 'Negative %d to stack size %d is illegal'%(self.amount,
                                                              self.stack_size)

    class NotBoughtIn(Exception):
        def __init__(self, nickname):
            self.nickname = nickname
        def notation(self):
            return {'player': self.nickname}
        def __str__(self):
            return "Cannot seat player '%s' with zero stack size"%\
                self.nickname

    class BuyinTooSmall(Exception):
        def __init__(self, nickname, amount, minimum):
            self.nickname = nickname
            self.amount = amount
            self.minimum = minimum
        def notation(self):
            return {'player': self.nickname, 'amount': self.amount,
                    'minimum': self.minimum}
        def __str__(self):
            tc = convFact
            s = "Buyin from '%s' of %d bb doesn't meet table minimum of %d bb"
            return s%(self.nickname, self.amount / tc, self.minimum / tc)

    def __init__(self, numPlayers, sb, bb, ante, min_buyin, max_buyin):
        self.numPlayers = numPlayers
        # Only the BB is in real money terms.
        self.bb = bb
        # There's no use keeping the SB value in real money terms,
        # so we convert it to tiny bb internally.
        self.sb = real_to_tiny(sb, bb)
        self.ante = real_to_tiny(ante, bb)
        self.min_buyin = min_buyin
        self.max_buyin = max_buyin
        self.seats = [None for x in range(numPlayers)]
        self.dealer = None
        self.game_state = GameState.STOPPED
        self.scheduler = None
        self.handler = None
        # Delay until new game is started to allow
        # players to join a game when a bunch of people sit in
        self.startup_delay_time = 8
        # rebuy list of (player, amount) tuples
        # at end of hand these are added to players stacks
        self.rebuys = []
    def register_scheduler(self, scheduler):
        """The scheduler provides the mechanism to have a function
        called at some later time."""
        self.scheduler = scheduler
    def register_handler(self, handler):
        """The handler is notified when the game starts. It passes
        responses from wherever back to the script."""
        self.handler = handler

    def add_player(self, nickname, seatid):
        """New players are automatically sat out when joining a table,
        and need to buyin first."""
        if seatid < 0 or seatid >= len(self.seats):
            raise self.InvalidSeat(nickname, seatid)
        if self.seats[seatid] != None:
            raise self.SeatTaken(nickname, seatid, self.seats[seatid].nickname)
        self.seats[seatid] = Player(nickname)
        return self.seats[seatid]

    def add_money(self, player, amount):
        """Remember that amount is in terms of tiny bb, not real money.
        If player is sitting in and playing, it is added to a list
        for until after the current hand is finished.
        returns True when money has been added.
        returns False when money will be added after current hand."""
        # Protect against silliness
        if amount < 0:
            raise Table.BuyinNegative(player.nickname, amount, player.stack)

        # if sitting out or no game running, then buyin
        if player.sitting_out or self.game_state != GameState.RUNNING:
            self.perform_buyin(player, amount)
            return True
        else:
            self.rebuys.append((player, amount))
            return False

    def perform_buyin(self, player, amount):
        """Actually do the rebuy and add the money."""
        # When you first sit in you must rebuy to above a minimum
        if player.stack == 0 and amount < self.min_buyin:
            raise Table.BuyinTooSmall(player.nickname, amount, self.min_buyin)

        total_stack = player.stack + amount
        if total_stack > self.max_buyin:
            total_stack = self.max_buyin

        self.debit_player(player, total_stack - player.stack)

    def debit_player(self, player, amount):
        """Moves fund from player account and adds to stack."""
        # If player has relevant funds
        if True:
            player.stack += amount

    def execute_pending_rebuys(self):
        """Called at the end of every hand. Does any pending rebuys."""
        for player, amount in self.rebuys:
            self.perform_buyin(player, amount)
        self.rebuys = []

    def sit_in(self, player):
        if player.stack == 0:
            raise Table.NotBoughtIn(player.nickname)
        player.sitting_out = False
        # schedule new game to start if need be.
        self.check_state()

    def sit_out(self, player):
        """Sit player out.
        If seated players drops below 2 then game stops running."""
        player.sitting_out = True
        self.check_state()

    def empty_seat(self, player, seat):
        nickname = player.nickname
        if seat < 0 or seat >= len(self.seats):
            raise self.InvalidSeat(nickname, seat)
        elif self.seats[seat] != player:
            raise WrongPlayerInSeat(self.seats[seat], nickname)
        self.seats[seat] = None
        self.check_state()

    def set_autopost(self, player, autopost):
        """Set autopost blinds on a player."""
        player.settings.autopost = autopost

    def lookup_player(self, nickname):
        for seat, player in enumerate(self.seats):
            if player != None and player.nickname == nickname:
                return seat, player
        raise Table.NoSuchPlayer(nickname)

    def check_state(self):
        # if a game isn't running yet then lets start one
        # must be at least 2 people sitting in
        seated_players = \
            [p for p in self.seats if p != None and not p.sitting_out]
        if len(seated_players) > 1:
            if (self.game_state == GameState.STOPPED or
                self.game_state == GameState.HALTING):
                # Change state machine to transitioning to new game
                self.game_state = GameState.STARTING
                # schedule new game to start in a few seconds...
                if self.scheduler:
                    self.scheduler.callback(self.start,
                                            self.startup_delay_time)
        else:
            if (self.game_state == GameState.STARTING or
                self.game_state == GameState.RUNNING):
                # State machine status update
                self.game_state = GameState.HALTING
                # Clear scheduler
                self.scheduler.clear()
                # stop the game
                self.halt()

    def start(self):
        """Start the game."""
        if self.game_state != GameState.STARTING:
            if self.game_state == GameState.RUNNING:
                print('Game already running.')
            else:
                print('Start game cancelled.')
            return
        self.game_state = GameState.RUNNING
        print('Game started.')
        # select a random dealer
        occupied_seats = \
            [i for i, p in enumerate(self.seats) if p and not p.sitting_out]
        self.dealer = random.choice(occupied_seats)

        # Let everyone off paying for the first hand!
        # (Except the blinds)
        for player in self.seats:
            if player is not None and not player.sitting_out:
                player.paid_state = player.PAID_SB_BB
        # Start the actual game
        scr = script.Script(self)
        if self.handler:
            self.handler.start(scr)

    def next_dealer(self):
        # Get list of indices of the seats
        rotated_seats = [i for i, p in enumerate(self.seats)]
        # Rotate it around the current dealer position + 1
        rotated_seats = \
            rotated_seats[self.dealer+1:] + rotated_seats[:self.dealer+1]
        # Filter empty seats and sitting out players
        filter_seats = [i for i in rotated_seats \
            if self.seats[i] is not None and not self.seats[i].sitting_out]
        # Return next suitable candidate
        self.dealer = filter_seats[0]

    def halt(self):
        """Halt the current running game."""
        if self.game_state != GameState.HALTING:
            print('Internal Error?')
            return
        self.game_state = GameState.STOPPED
        print('Game halted.')
        if self.handler:
            self.handler.stop()
        for player in self.seats:
            if player is not None:
                player.paid_state = player.PAID_NOTHING

    def __repr__(self):
        s = ''
        if self.dealer != None:
            s += 'Seat %i is the button\n'%self.dealer
        for seat, player in enumerate(self.seats):
            s += 'Seat %i: %s\n'%(seat, player)
        return s

if __name__ == '__main__':
    cash = Table(9, 0.25, 0.5, 0, 5000, 25000)
    cash.register_scheduler(Schedule())
    cash.register_handler(Handler())
    j = cash.add_player('john', 0)
    cash.add_money(j, 5000)
    p = cash.add_player('mison', 1)
    cash.add_money(p, 10000)
    p = cash.add_player(p, 2)
    cash.add_money(p, 10000)
    p = cash.add_player('honn', 3)
    cash.add_money(p, 10000)
    cash.sit_in(p)
    cash.sit_in(j)
    print cash
    cash.sit_out(p)
    cash.sit_in(p)
    cash.start()

