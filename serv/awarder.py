import pokereval

class Pots:
    class Abacus:
        """Used for tallying bets off relative to each other."""
        def __init__(self, bettor):
            self.bettor = bettor
            self.total_bet = bettor.bet + bettor.darkbet
        def __repr__(self):
            return '%s (%d)'%(self.bettor.parent.nickname, self.total_bet)

    class Pot:
        def __init__(self, bet, potsize, contestors):
            self.bet = bet
            self.size = potsize
            self.contestors = contestors

        def names(self):
            return [c.parent.nickname for c in self.contestors]

        def notation(self):
            return {'bet': self.bet, 'size': self.size,
                    'players': self.names()}

        def __repr__(self):
            return '[%d, %d,  %s]'%(self.bet, self.size, self.names())

    def __init__(self, bettors):
        self.pots = self.compute(bettors)

    def compute(self, bettors):
        """Take a bunch of bettors and compute the various pots
        depending on the bets made."""
        abacuses = [self.Abacus(b) for b in bettors]
        abacuses.sort(key=lambda a: a.total_bet)
        pots = []
        # The current absolute bet size
        current_bet = 0
        for aaba in abacuses:
            if aaba.total_bet == 0:
                continue
            elif aaba.bettor.active:
                current_bet += aaba.total_bet
                remain_bet = aaba.total_bet
                potsize = 0
                contestors = []
                for baba in abacuses:
                    if baba.bettor.active and baba.total_bet > 0:
                        contestors.append(baba.bettor)
                    if baba.total_bet < remain_bet:
                        potsize += baba.total_bet
                        baba.total_bet = 0
                    else:
                        potsize += remain_bet
                        baba.total_bet -= remain_bet
                pots.append(self.Pot(current_bet, potsize, contestors))
        return pots

    def uncontested(self):
        return len(self.pots) == 1 and len(self.pots[0].contestors) == 1

    def notation(self):
        return [p.notation() for p in self.pots]

    def __repr__(self):
        s = ''
        for p in self.pots:
            s += '%s\n'%p
        return s

def handName(handrank):
    """Gives nice string describing five-card hand like
        two pair, Kings and Queens
        straight, Seven high"""
    return handrank[0]

class AwardHands:
    def __init__(self, players, pots, board):
        self.players = players
        self.pots = pots
        self.board = board
        self.pokerEval = pokereval.PokerEval()

    def calculateRankings(self):
        rankings = []
        for playerBet in self.players:
            playerObj = playerBet.parent
            name = playerObj.nickname
            cards = list(playerObj.cards) + self.board
            playerBet.handRanking = self.pokerEval.best('hi', cards)
            assert(playerBet.handRanking)
            rankings.append((name, playerBet.handRanking[1]))
        return rankings

    def award(self):
        award = []
        for pot in self.pots:
            potSize = pot.potSize
            players = pot.contestors
            winner = max(players, key=lambda p: p.handRanking[0])
            winner.parent.stack += potSize
            #award.append((winner.parent.nickname, potSize))
            award.append((winner.parent, potSize))
        return award

if __name__ == '__main__':
    def unittest_pots():
        class B:
            class P:
                def __init__(self, nickname):
                    self.nickname = nickname
            def __init__(self, nickname, bet, active):
                self.parent = self.P(nickname)
                self.bet = bet
                self.darkbet = 0
                self.active = active
            def __repr__(self):
                return '%s(%d)'%(self.parent.nickname, self.bet)

        bettors = [
            B('a', 0, False),
            B('b', 1, False),
            B('c', 3, True),
            B('d', 5, False),
            B('e', 7, True),
            B('f', 9, True)]
        # Above input should output:
        #   betsize  potsize   contestors
        #    3         13        c, e, f
        #    7         10        e, f
        #    9         2         f
        print Pots(bettors)

        bettors = [
            B('a', 2, True),
            B('b', 2, True),
            B('c', 2, True),
            B('d', 3, True)]
        #    2         8         a, b, c, d
        #    3         1         d
        print Pots(bettors)
    unittest_pots()
