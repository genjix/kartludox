import random
import time
random.seed(time.time())
import script

convFact = 100
def tinyToReal(tinybb, bigBlind):
    """All calculations are done in terms of tiny bb's.
    A tiny bb = 1 bb / 100
    This function converts from tiny bb -> real money"""
    return tinybb * bigBlind / float(convFact)
def realToTiny(real, bigBlind):
    """See tinyToReal."""
    return int(real * convFact / float(bigBlind))

class Player:
    class PaidState:
        Nothing = 0
        WaitingBB = 1
        PaidBB = 2
        PaidSBBB = 3

        @classmethod
        def strRepr(cls, state):
            if state == cls.Nothing:
                return '-'
            elif state == cls.WaitingBB:
                return '*'
            elif state == cls.PaidBB:
                return 'bb'
            elif state == cls.PaidSBBB:
                return 'sb/bb'
            raise Exception('Internal Error: No such paid state %i')

    class Bets:
        def __init__(self, parent):
            self.parent = parent
            self.betPlaced = 0
            self.stillActive = True
            self.isAllIn = False
            # Bets not counted in the playing like antes
            self.darkBet = 0

        def pay(self, charge):
            self.parent.stack -= charge
            self.betPlaced += charge
        def payDark(self, charge):
            self.parent.stack -= charge
            self.darkBet += charge

        def __repr__(self):
            return self.parent.nickname

    class Settings:
        def __init__(self, parent):
            self.parent = parent
            self.autopost = False

    def __init__(self, nickname):
        self.nickname = nickname
        self.stack = 0
        self.paidState = Player.PaidState.Nothing
        self.sitOut = True
        self.cards = None
        # Stores bets and actions by player
        self.betPart = None
        self.settings = self.Settings(self)

    def newBetPart(self):
        self.betPart = self.Bets(self)

    def __repr__(self):
        if self.cards:
            cardsRepr = '[%s %s]'%self.cards
        else:
            cardsRepr = '[--]'
        return '%s (%g bb) %s Sitting %s %s'%(self.nickname, self.stack/100.0, \
            cardsRepr, self.sitOut and 'Out' or 'In',
            Player.PaidState.strRepr(self.paidState))

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
    Stopped = 0
    Starting = 1
    Running = 2
    Halting = 3

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
            return "Buyin from '%s' of %d bb doesn't meet table minimum of %d bb"%\
                (self.nickname, self.amount / tc, self.minimum / tc)

    def __init__(self, numPlayers, sb, bb, ante, minBuyin, maxBuyin):
        self.numPlayers = numPlayers
        # Only the BB is in real money terms.
        self.bb = bb
        # There's no use keeping the SB value in real money terms,
        # so we convert it to tiny bb internally.
        self.sb = realToTiny(sb, bb)
        self.ante = realToTiny(ante, bb)
        self.minBuyin = minBuyin
        self.maxBuyin = maxBuyin
        self.seats = [None for x in range(numPlayers)]
        self.dealer = None
        self.gameState = GameState.Stopped
        self.scheduler = None
        self.handler = None
        # Delay until new game is started to allow
        # players to join a game when a bunch of people sit in
        self.gameStartupDelayTime = 8
        # rebuy list of (player, amount) tuples
        # at end of hand these are added to players stacks
        self.rebuys = []
    def registerScheduler(self, scheduler):
        """The scheduler provides the mechanism to have a function
        called at some later time."""
        self.scheduler = scheduler
    def registerHandler(self, handler):
        """The handler is notified when the game starts. It passes
        responses from wherever back to the script."""
        self.handler = handler

    def setStartupDelayTime(self, delay):
        self.gameStartupDelayTime = delay

    def addPlayer(self, nickname, seat):
        """New players are automatically sat out when joining a table,
        and need to buyin first."""
        if seat < 0 or seat >= len(self.seats):
            raise self.InvalidSeat(seat)
        if self.seats[seat] != None:
            raise self.SeatTaken(seat, self.seats[seat].nickname)
        self.seats[seat] = Player(nickname)

    def addMoney(self, nickname, amount):
        """Remember that amount is in terms of tiny bb, not real money.
        If player is sitting in and playing, it is added to a list
        for until after the current hand is finished.
        returns True when money has been added.
        returns False when money will be added after current hand."""
        seat, player = self.lookupPlayer(nickname)
        # Protect against silliness
        if amount < 0:
            raise Table.BuyinNegative(amount, player.stack)

        # if sitting out or no game running, then buyin
        if player.sitOut or self.gameState != GameState.Running:
            self.addMoneyPlayer(player, amount)
            return True

        self.rebuys.append((player, amount))
        return False

    def addMoneyPlayer(self, player, amount):
        """Actually do the rebuy and add the money."""

        # When you first sit in you must rebuy to above a minimum
        if player.stack == 0 and amount < self.minBuyin:
            raise Table.BuyinTooSmall(player, amount, self.minBuyin)

        totalStack = player.stack + amount
        if totalStack > self.maxBuyin:
            totalStack = self.maxBuyin

        self.debitPlayer(player, totalStack - player.stack)

    def debitPlayer(self, player, amount):
        """Moves fund from player account and adds to stack."""
        # If player has relevant funds
        if True:
            player.stack += amount

    def executePendingRebuys(self):
        """Called at the end of every hand. Does any pending rebuys."""
        for player, amount in self.rebuys:
            self.addMoneyPlayer(player, amount)
        self.rebuys = []

    def sitIn(self, nickname):
        seat, player = self.lookupPlayer(nickname)
        if player.stack == 0:
            raise Table.NotBoughtIn(nickname)
        player.sitOut = False
        # schedule new game to start if need be.
        self.checkState()

    def sitOut(self, nickname):
        """Sit player out.
        If seated players drops below 2 then game stops running."""
        seat, player = self.lookupPlayer(nickname)
        self.sitOutPlayer(player)
    def sitOutPlayer(self, player):
        """Sit player out.
        Uses player object rather than nickname string."""
        player.sitOut = True
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
            [p for p in self.seats if p != None and not p.sitOut]
        if len(seatedPlayers) > 1:
            if self.gameState == GameState.Stopped or \
              self.gameState == GameState.Halting:
                # Change state machine to transitioning to new game
                self.gameState = GameState.Starting
                # schedule new game to start in a few seconds...
                if self.scheduler:
                    self.scheduler.callback(self.start,
                        self.gameStartupDelayTime)
        else:
            if self.gameState == GameState.Starting or \
              self.gameState == GameState.Running:
                # State machine status update
                self.gameState = GameState.Halting
                # Clear scheduler
                self.scheduler.clear()
                # stop the game
                self.halt()

    def start(self):
        """Start the game."""
        if self.gameState != GameState.Starting:
            if self.gameState == GameState.Running:
                print('Game already running.')
            else:
                print('Start game cancelled.')
            return
        self.gameState = GameState.Running
        print('Game started.')
        # select a random dealer
        occupiedSeats = \
            [i for i, p in enumerate(self.seats) if p and not p.sitOut]
        self.dealer = random.choice(occupiedSeats)

        # Start the actual game
        scr = script.Script(self)
        if self.handler:
            self.handler.start(scr)
        # Let everyone off paying for the first hand!
        # (Except the blinds)
        for player in self.seats:
            if player is not None and not player.sitOut:
                player.paidState = player.PaidState.PaidSBBB

    def nextDealer(self):
        # Get list of indices of the seats
        rotatedSeats = [i for i, p in enumerate(self.seats)]
        # Rotate it around the current dealer position + 1
        rotatedSeats = \
            rotatedSeats[self.dealer+1:] + rotatedSeats[:self.dealer+1]
        # Filter empty seats and sitting out players
        filterSeats = [i for i in rotatedSeats \
            if self.seats[i] is not None and not self.seats[i].sitOut]
        # Return next suitable candidate
        self.dealer = filterSeats[0]

    def halt(self):
        """Halt the current running game."""
        if self.gameState != GameState.Halting:
            print('Internal Error?')
            return
        self.gameState = GameState.Stopped
        print('Game halted.')
        if self.handler:
            self.handler.stop()
        for player in self.seats:
            if player is not None:
                player.paidState = player.PaidState.Nothing

    def __repr__(self):
        s = ''
        if self.dealer != None:
            s += 'Seat %i is the button\n'%self.dealer
        for seat, player in enumerate(self.seats):
            s += 'Seat %i: %s\n'%(seat, player)
        return s

if __name__ == '__main__':
    cash = Table(9, 0.25, 0.5, 0, 5000, 25000)
    cash.registerScheduler(Schedule())
    cash.registerHandler(Handler())
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
