import random, time
random.seed(time.time())

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
    def __init__(self, nickname):
        self.nickname = nickname
        self.stack = 0
        self.paidSB = False
        self.paidBB = False
        self.sitOut = True
        self.cards = None
    def __repr__(self):
        return '%s (%i bb) %s Sitting %s'%(self.nickname, self.stack/100.0, \
            self.cards, self.sitOut and 'Out' or 'In')

class Schedule:
    def __init__(self):
        self.started = False
    def callback(self, functor, ms):
        # If already scheduled then make sure not to schedule event twice.
        if not self.started:
            print('A new game will begin in %d seconds.'%(ms/1000))
        started = True
        #functor()
    def clear(self):
        print('Cancelled callback.')

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
    class BuyinTooSmall(Exception):
        def __init__(self, amount, stackSize, minBuyin):
            self.amount = amount
            self.stackSize = stackSize
            self.minBuyin = minBuyin
        def __str__(self):
            return 'Adding %d to stack size %d less than min buyin of %d'%\
                (self.amount, self.stackSize, self.minBuyin)
    class BuyinTooBig(Exception):
        def __init__(self, amount, stackSize, maxBuyin):
            self.amount = amount
            self.stackSize = stackSize
            self.maxBuyin = maxBuyin
        def __str__(self):
            return 'Adding %d to stack size %d exceeds max buyin of %d'%\
                (self.amount, self.stackSize, self.maxBuyin)

    class NotBoughtIn(Exception):
        def __init__(self, nickname):
            self.nickname = nickname
        def __str__(self):
            return "Cannot seat player '%s' with zero stack size"%\
                self.nickname

    def __init__(self, numPlayers, sb, bb, ante, minBuyin, maxBuyin):
        self.numPlayers = numPlayers
        self.sb = sb
        self.bb = bb
        self.ante = ante
        self.minBuyin = minBuyin
        self.maxBuyin = maxBuyin
        self.seats = [None for x in range(numPlayers)]
        self.dealer = None
        self.gameState = GameState.Stopped
        self.scheduler = None
    def registerScheduler(self, scheduler):
        """The scheduler provides the mechanism to have a function
        called at some later time."""
        self.scheduler = scheduler

    def addPlayer(self, nickname, seat):
        """New players are automatically sat out when joining a table,
        and need to buyin first."""
        if seat < 0 or seat >= len(self.seats):
            raise self.InvalidSeat(seat)
        if self.seats[seat] != None:
            raise self.SeatTaken(seat, self.seats[seat].nickname)
        self.seats[seat] = Player(nickname)

    def addMoney(self, nickname, amount):
        """Remember that amount is in terms of tiny bb, not real money."""
        seat, player = self.lookupPlayer(nickname)
        # Protect against naughter crackers!
        if amount < 0:
            raise Table.BuyinNegative(amount, player.stack)
        # If the player has already won some cash
        # then they cannot add anything as they already exceed maxBuyin
        if player.stack >= self.maxBuyin:
            raise Table.BuyinTooBig(amount, player.stack, self.maxBuyin)
        # A player with stackSize of 0 cannot be sat in
        # ... Normal rules apply
        elif player.stack == 0:
            if amount < self.minBuyin:
                raise Table.BuyinTooSmall(amount, player.stack, self.minBuyin)
            elif amount > self.maxBuyin:
                raise Table.BuyinTooBig(amount, player.stack, self.maxBuyin)
            player.stack = amount
        # Player stack is less than maxBuyin.
        # Can buy in for any amount, even if it still leaves them
        # below the minBuyin but not excees maxBuyin
        else:
            totalStack = player.stack + amount
            # Perfectly fine to buy up to and INCLUDING maxBuyin, but
            # not over it.
            if totalStack > self.maxBuyin:
                raise Table.BuyinTooBig(amount, player.stack, self.maxBuyin)
            player.stack = totalStack

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
        player.sitOut = True
        self.checkState()

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
                    self.scheduler.callback(self.start, 10000)
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
            print('Start game cancelled.')
            return
        self.gameState = GameState.Running
        print('Game started.')
        # select a random dealer
        self.dealer = 0

    def halt(self):
        """Halt the current running game."""
        if self.gameState != GameState.Halting:
            print('Internal Error?')
            return
        self.gameState = GameState.Stopped
        print('Game halted.')

    def __repr__(self):
        s = ''
        if self.dealer:
            s += 'Seat %i is the button\n'%self.dealer
        for seat, player in enumerate(self.seats):
            s += 'Seat %i: %s\n'%(seat, player)
        return s

if __name__ == '__main__':
    cash = Table(9, 0.25, 0.5, 0, 5000, 25000)
    cash.registerScheduler(Schedule())
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
