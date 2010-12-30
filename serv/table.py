import random
import time
random.seed(time.time())
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
        def __init__(self, seatid):
            self.seatid = seatid
        def __str__(self):
            return 'Invalid seat ID %d'%self.seatid

    class SeatTaken(Exception):
        def __init__(self, seatid, otherNickname):
            self.seatid = seatid
            self.otherNickname = otherNickname
        def __str__(self):
            return "Seat %d already taken by player '%s'"%\
                (self.seatid, self.otherNickname)
    class NoSuchPlayer(Exception):
        def __init__(self, nickname):
            self.nickname = nickname
        def __str__(self):
            return "No such nickname '%s'"%self.nickname

    class BuyinNegative(Exception):
        def __init__(self, amount, stackSize):
            self.amount = amount
            self.stackSize = stackSize
        def __str__(self):
            return 'Negative %d to stack size %d is illegal'%\
                (self.amount, self.stackSize)

    class NotBoughtIn(Exception):
        def __init__(self, nickname):
            self.nickname = nickname
        def __str__(self):
            return "Cannot seat player '%s' with zero stack size"%\
                self.nickname

    class BuyinTooSmall(Exception):
        def __init__(self, player, amount, minimum):
            self.nickname = player.nickname
            self.amount = amount
            self.minimum = minimum
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

    def addPlayer(self, nickname, seat):
        """New players are automatically sat out when joining a table,
        and need to buyin first."""
        if seat < 0 or seat >= len(self.seats):
            raise self.InvalidSeat(seat)
        if self.seats[seat] != None:
            raise self.SeatTaken(seat, self.seats[seat].nickname)
        self.seats[seat] = Player(nickname)

    def addMoney(self, player, amount):
        """Remember that amount is in terms of tiny bb, not real money.
        If player is sitting in and playing, it is added to a list
        for until after the current hand is finished.
        returns True when money has been added.
        returns False when money will be added after current hand."""
        # Protect against silliness
        if amount < 0:
            raise Table.BuyinNegative(amount, player.stack)

        # if sitting out or no game running, then buyin
        if player.sitting_out or self.game_state != GameState.RUNNING:
            self.addMoneyPlayer(player, amount)
            return True

        self.rebuys.append((player, amount))
        return False

    def addMoneyPlayer(self, player, amount):
        """Actually do the rebuy and add the money."""

        # When you first sit in you must rebuy to above a minimum
        if player.stack == 0 and amount < self.min_buyin:
            raise Table.BuyinTooSmall(player, amount, self.min_buyin)

        totalStack = player.stack + amount
        if totalStack > self.max_buyin:
            totalStack = self.max_buyin

        self.debitPlayer(player, totalStack - player.stack)

    def debitPlayer(self, player, amount):
        """Moves fund from player account and adds to stack."""
        # If player has relevant funds
        if True:
            player.stack += amount

    def execute_pending_rebuys(self):
        """Called at the end of every hand. Does any pending rebuys."""
        for player, amount in self.rebuys:
            self.addMoneyPlayer(player, amount)
        self.rebuys = []

    def sitIn(self, nickname):
        seat, player = self.lookupPlayer(nickname)
        if player.stack == 0:
            raise Table.NotBoughtIn(nickname)
        player.sitting_out = False
        # schedule new game to start if need be.
        self.checkState()

    def sitOut(self, nickname):
        """Sit player out.
        If seated players drops below 2 then game stops running."""
        seat, player = self.lookupPlayer(nickname)
        self.sit_out_player(player)

    def sit_out_player(self, player):
        """Sit player out.
        Uses player object rather than nickname string."""
        player.sitting_out = True
        self.checkState()

    def setAutopost(self, nickname, autopost):
        """Set autopost blinds on a player."""
        seat, player = self.lookupPlayer(nickname)
        player.settings.autopost = autopost

    def removePlayer(self, nickname):
        seat, player = self.lookupPlayer(nickname)
        self.seats[seat] = None
        self.checkState()

    def lookupPlayer(self, nickname):
        for seat, player in enumerate(self.seats):
            if player != None and player.nickname == nickname:
                return seat, player
        raise Table.NoSuchPlayer(nickname)

    def checkState(self):
        # if a game isn't running yet then lets start one
        # must be at least 2 people sitting in
        seatedPlayers = \
            [p for p in self.seats if p != None and not p.sitting_out]
        if len(seatedPlayers) > 1:
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
        occupiedSeats = \
            [i for i, p in enumerate(self.seats) if p and not p.sitting_out]
        self.dealer = random.choice(occupiedSeats)

        # Let everyone off paying for the first hand!
        # (Except the blinds)
        for player in self.seats:
            if player is not None and not player.sitting_out:
                player.paidState = player.PAID_SB_BB
        # Start the actual game
        scr = script.Script(self)
        if self.handler:
            self.handler.start(scr)

    def next_dealer(self):
        # Get list of indices of the seats
        rotatedSeats = [i for i, p in enumerate(self.seats)]
        # Rotate it around the current dealer position + 1
        rotatedSeats = \
            rotatedSeats[self.dealer+1:] + rotatedSeats[:self.dealer+1]
        # Filter empty seats and sitting out players
        filterSeats = [i for i in rotatedSeats \
            if self.seats[i] is not None and not self.seats[i].sitting_out]
        # Return next suitable candidate
        self.dealer = filterSeats[0]

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
                player.paidState = player.PAID_NOTHING

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
    cash.addPlayer('john', 0)
    cash.addMoney('john', 5000)
    cash.addPlayer('mison', 1)
    cash.addMoney('mison', 10000)
    cash.addPlayer('lorea', 2)
    cash.addMoney('lorea', 10000)
    cash.addPlayer('honn', 3)
    cash.addMoney('honn', 10000)
    cash.sitIn('honn')
    cash.sitIn('lorea')
    print cash
    cash.sitOut('honn')
    cash.sitIn('honn')
    cash.start()
