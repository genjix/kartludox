import itertools

class Player:
    def __init__(self, playerObj):
        self.betPlaced = 0
        self.stillActive = True
        self.isAllIn = False
        self.playerObj = playerObj
        self.repeatAction = False
    def __repr__(self):
        return self.playerObj.nickname

class Rotator:
    def __init__(self, seats):
        # First player to act should always be first in this list
        self.seats = [(s and Player(s) or None) for s in seats]
        self.lastBettor = None
        self.lastBet = 0
        self.lastRaise = 0
        self.capBettor = None
        # This is both regular bets and all-in capped bets
        self.currentBet = 0
    def setSeatBetPlaced(self, pos, betSize):
        """Used for the blinds & posters which have to place forced bets."""
        self.seats[pos].betPlaced = betSize
    def setBetSize(self, bet):
        self.lastBet = bet
        self.lastRaise = bet

    def run(self):
        bettingFinished = False
        reOpenBetting = False
        bettingClosed = False

        players = [p for p in self.seats if p != None]
        assert(len(players) > 0)

        while not bettingFinished:
            for player in players:
                if not player.stillActive:
                    continue
                if player.isAllIn:
                    if bettingClosed and reOpenBetting:
                        bettingFinished = True
                        break
                    continue

                if not self.lastBettor:
                    self.lastBettor = player
                elif self.lastBettor == player:
                    bettingClosed = True
                    if self.capBettor and not reOpenBetting:
                        reOpenBetting = True
                    else:
                        bettingFinished = True
                        break

                if bettingClosed and reOpenBetting:
                    self.currentBet = self.capBettor.betPlaced
                    yield player, True
                    if player.betPlaced != self.currentBet:
                        player.stillActive = False
                    continue

                self.currentBet = self.lastBet
                if self.capBettor:
                    assert(self.capBettor.betPlaced > self.lastBet)
                    self.currentBet = self.capBettor.betPlaced

                yield player, False

                if player.betPlaced > self.lastBet:
                    # Raise
                    raiseAmount = player.betPlaced - self.lastBet

                    if raiseAmount < self.lastRaise:
                        # Player went all-in for less than a raise
                        # Caps betting
                        if not self.capBettor or \
                          self.currentBet < player.betPlaced:
                            self.capBettor = player
                            player.isAllIn = True
                    else:
                        if self.capBettor:
                            assert(raiseAmount >= 2*self.lastRaise)
                        self.capBettor = None

                        self.lastRaise = raiseAmount
                        self.lastBet = player.betPlaced
                        self.lastBettor = player
                elif player.betPlaced == self.currentBet:
                    # Call
                    pass
                elif player.betPlaced < self.lastBet:
                    # Fold
                    player.stillActive = False
                    if self.lastBettor == player:
                        self.lastBettor = None
                else:
                    # Something's wrong!
                    assert(False)
                    pass

                numActivePlayers = \
                    len([p for p in players if p.stillActive])
                if numActivePlayers < 2:
                    bettingFinished = True
                    break

    def minRaise(self):
        if self.capBettor:
            return self.lastBet + 2*self.lastRaise
        return self.lastBet + self.lastRaise

if __name__ == '__main__':
    class P:
        def __init__(self, s):
            self.nickname = s
    seats = [P('a'), P('b'), P('c'), P('d'), P('e'), P('SB'), P('BB')]
    r = Rotator(seats)
    r.setSeatBetPlaced(-2, 1)
    r.setSeatBetPlaced(-1, 2)
    r.setBetSize(2)
    for player, capped in r.run():
        print '---------'
        print '%s bet %d to %d'%(r.lastBettor, r.lastRaise, r.lastBet)
        print r.capBettor, r.currentBet, capped
        if not capped:
            print 'call=%d, minraise=%d'%(r.currentBet, r.minRaise())
        else:
            print 'call=%d'%r.currentBet
        print
        print '%s (%d)'%(player, player.betPlaced)
        s = int(raw_input())
        player.betPlaced = s

