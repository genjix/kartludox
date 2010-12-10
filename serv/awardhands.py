import pokereval

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
