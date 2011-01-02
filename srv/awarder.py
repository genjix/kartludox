import pokereval

class Pots:
    class Abacus:
        """Used for tallying bets off relative to each other."""
        def __init__(self, bettor):
            self.bettor = bettor
            # antes and posted SB's from POST_SB_BB dont count as placed bets
            self.total_bet = bettor.total_placed_bets
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
        return [p for p in self.pots if len(p.contestors) < 2]

    def notation(self):
        return [p.notation() for p in self.pots]

    def __getitem__(self, i):
        return self.pots[i]

    def __len__(self):
        return len(self.pots)

    def __repr__(self):
        s = ''
        for p in self.pots:
            s += '%s\n'%p
        return s

def hand_name(handrank):
    """Gives nice string describing five-card hand like
        two pair, Kings and Queens
        straight, Seven high"""
    return handrank[1][0]

class AwardHands:
    def __init__(self, invested_players, pots, board):
        self.players = invested_players
        self.pots = pots
        self.board = board
        self.pokereval = pokereval.PokerEval()
        self.rankings = {}

    def calculate_rankings(self):
        for player in self.players:
            cards = list(player.cards) + self.board
            self.rankings[player] = self.pokereval.best('hi', cards)
        return self.rankings

    def calculate_winners(self):
        winners = []
        for pot in self.pots:
            winning_bettor = max(pot.contestors,
                                 key=lambda b: self.rankings[b.parent])
            winning_player = winning_bettor.parent
            winners.append((winning_player, pot.size))
        return winners

if __name__ == '__main__':
    def unittest_pots():
        class B:
            class P:
                def __init__(self, nickname):
                    self.nickname = nickname
            def __init__(self, nickname, bet, active):
                self.parent = self.P(nickname)
                self.bet = bet
                self.active = active
            @property
            def total_placed_bets(self):
                return self.bet
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
