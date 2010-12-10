import itertools

class AllIn:
    def __init__(self, bettor):
        self.bettor = bettor
    def __repr__(self):
        b = self.bettor
        return '%s is all-in for %d'%(b.parent.nickname, b.bet)

class BettingPlayer:
    def __init__(self, parent):
        self.parent = parent
        self.bet = 0
        self.darkbet = 0
        self.active = True
        # attach self to parent
        self.parent.betpart = self

        # messages from rotator
        self.can_raise = True
        self.min_raise = 0
        self.max_raise = self.parent.stack
        self.call_price = 0

    def pay(self, charge):
        self.parent.stack -= charge
        self.bet += charge
    def pay_dark(self, charge):
        self.parent.stack -= charge
        self.darkbet += charge

    def stack(self):
        return self.parent.stack

    def fold(self):
        self.active = False

    def call(self, bet):
        price = bet - self.bet
        self.pay(price)

    def raiseto(self, bet):
        price = bet - self.bet
        if price >= self.parent.stack:
            self.pay(self.parent.stack)
            raise AllIn(self)
        self.pay(price)

    def set_prices(self, call, rmin=None, rmax=None):
        if rmin is None:
            self.can_raise = False
        else:
            self.min_raise = rmin
            self.max_raise = rmax
        self.call_price = call

    def __repr__(self):
        return '%s %d (%d, %d) active=%s'%(self.parent.nickname,
                                           self.parent.stack, self.bet,
                                           self.darkbet, self.active)

class Rotator:
    BettingOpen = 0
    BettingCapped = 1
    BettingClosed = 2

    def __init__(self, active_players, current_bet):
        self.players = active_players
        [BettingPlayer(p) for p in self.players]

        self.last_bettor = None
        self.cap_bettor = None
        self.state = Rotator.BettingOpen
        self.last_raise = self.current_bet

    def run(self):
        for player in itertools.cycle(self.players):
            bettor = player.betpart
            if not bettor.active or bettor.stack() == 0:
                continue
            elif bettor == self.last_bettor:
                break

            if not self.last_bettor:
                self.last_bettor = bettor

            print bettor
            yield bettor

            if self.should_stop():
                break

    def should_stop(self):
        num_bettors = len([p for p in self.players if p.betpart.active])
        return num_bettors < 2

    def fold(self, bettor):
        bettor.fold()

    def call(self, bettor):
        bettor.call(self.current_bet)

    def raiseto(self, bettor, amount):
        try:
            bettor.raiseto(amount)
        except AllIn as allin:
            print allin
        else:
            self.last_bettor = bettor

if __name__ == '__main__':
    class P:
        def __init__(self, n):
            self.nickname = n
            self.stack = 1000
        def __repr__(self):
            return self.nickname

    players = [P('a'), P('b'), P('c'), P('d'), P('e')]
    rotator = Rotator(players, 1)
    for b in rotator.run():
        cc = raw_input()
        if cc[0] == 'f':
            rotator.fold(b)
        elif cc[0] == 'c':
            rotator.call(b)
        elif cc[0] == 'r':
            rotator.raiseto(b, int(cc[1:]))

    for b in [p.betpart for p in players]:
        print b
