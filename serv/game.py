import random

class GameBase:
    def __init__(self):
        pass
    def addPlayer(self, nickname):
        return 0
    def buyin(self, amount):
        pass

class Player:
    def __init__(self, nickname, parent):
        self.nickname = nickname
        self.parent = parent
        self.stack = 0
        self.cards = None
    def __repr__(self):
        return '%s (%.2f btc or %i tb) %s'%(self.nickname,
            (self.stack/float(self.parent.tinyBB)) * self.parent.bb, self.stack,
            self.cards)

class NoSuchPlayer(Exception):
    def __init__(self, nickname):
        self.nickname = nickname
    def __str__(self):
        return "No such nickname '%s'!"%self.nickname

class NLCashScript:
    InvalidSeat = 0
    SeatTaken = 1
    NoSuchPlayer = 2

    tinyBB = 100
    """
    Numerical calculation in this class is done in terms of 1/100 of a bb.
    So a stack size is stored not as 100 btc in a 1/2btc game but as
    50*100 or 5000 tiny bb (1/100 of a bb)
    """

    def __init__(self, numPlayers, sb, bb, ante, minBuyin, maxBuyin):
        self.numPlayers = numPlayers
        self.sb = sb
        self.bb = bb
        self.ante = ante
        self.minBuyin = minBuyin * self.tinyBB
        self.maxBuyin = maxBuyin * self.tinyBB
        self.seats = [None for x in range(numPlayers)]
        self.dealer = random.randint(0, numPlayers - 1)
        self.deck = None

        self.action = []
        self.potSize = 0
    def addPlayer(self, nickname, seat):
        if seat < 0 or seat >= len(self.seats):
            return self.InvalidSeat
        if self.seats[seat] != None:
            return self.SeatTaken
        self.seats[seat] = Player(nickname, self)
    def removePlayer(self, nickname):
        seat, player = self.lookupPlayer(nickname)
        self.seats[seat] = None
    def buyin(self, nickname, amount):
        ### temporary!
        seat, player = self.lookupPlayer(nickname)
        player.stack = amount * self.tinyBB
    def postSB(self, nickname):
        seat, player = self.lookupPlayer(nickname)
        amount = int(round(self.tinyBB * self.sb / self.bb))
        self.potSize += amount
        player.stack -= amount
    def postBB(self, nickname):
        seat, player = self.lookupPlayer(nickname)
        self.potSize += self.tinyBB
        player.stack -= self.tinyBB
    def lookupPlayer(self, nickname):
        for seat, player in enumerate(self.seats):
            if player != None and player.nickname == nickname:
                return seat, player
        raise NoSuchPlayer(nickname)
    def dealCards(self):
        ranks = "23456789TJQKA"
        suits = "hdcs"
        self.deck = [rank + suit for rank in ranks for suit in suits]
        random.shuffle(self.deck)
        for player in self.seats:
            if player != None:
                player.cards = (self.deck.pop(), self.deck.pop())
    def __repr__(self):
        s = ''
        s += 'Seat %i is the button\n'%self.dealer
        for seat, player in enumerate(self.seats):
            s += 'Seat %i: %s\n'%(seat, player)
        s += 'Pot: %i\n'%self.potSize
        return s

    def fold(self, player):
        pass
    def check(self, player):
        pass
    def call(self, player):
        pass
    def raiseAction(self, player, amount):
        pass

if __name__ == '__main__':
    import time
    random.seed(time.time())
    cash = NLCashScript(9, 0.25, 0.5, 0, 50, 250)
    cash.addPlayer('john', 0)
    cash.buyin('john', 50)
    cash.addPlayer('mison', 1)
    cash.buyin('mison', 100)
    cash.addPlayer('lorea', 2)
    cash.buyin('lorea', 100)
    cash.addPlayer('honn', 3)
    cash.buyin('honn', 100)
    print cash
    cash.postSB('lorea')
    cash.postBB('mison')
    cash.dealCards()
    print cash
