import itertools

class AllIn:
    def __init__(self, bettor):
        self.bettor = bettor
    def __repr__(self):
        b = self.bettor
        return '%s is all-in for %d'%(b.parent.nickname, b.bet)

class IllegalRaise:
    def __init__(self, bettor):
        self.bettor = bettor
    def __repr__(self):
        return 'Non-allowed raise for:\n%s'%self.bettor

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
        srep = '%s %d (%d, %d) active=%s'%(self.parent.nickname,
                                           self.parent.stack, self.bet,
                                           self.darkbet, self.active)
        srep += '\nraise %s from %d to %d'%(self.can_raise, self.min_raise,
                                            self.max_raise)
        srep += '\ncall = %d'%self.call_price
        return srep

class Rotator:
    BettingOpen = 0
    BettingCapped = 1
    BettingClosed = 2
    BettingFinished = 3

    def __init__(self, active_players, current_bet):
        self.players = active_players
        [BettingPlayer(p) for p in self.players]

        self.last_bettor = None
        self.cap_bettor = None
        self.state = Rotator.BettingOpen
        # For the first round at least, current_bet != last_bettor.bet
        self.current_bet = current_bet
        self.last_raise = self.current_bet
        # Stop flag
        self.stop = False

    def run(self):
        for player in itertools.cycle(self.players):
            bettor = player.betpart
            if self.state == Rotator.BettingOpen:
                if self.prompt_open(bettor):
                    yield bettor
            elif self.state == Rotator.BettingCapped:
                if self.prompt_capped(bettor):
                    yield bettor

            if self.stop:
                break

    def prompt_open(self, bettor):
        if not bettor.active or bettor.stack() == 0:
            return False
        elif bettor == self.last_bettor:
            self.stop = True
            return False

        if not self.last_bettor:
            self.last_bettor = bettor

        bettor.can_raise = True
        bettor.min_raise = self.current_bet + self.last_raise
        bettor.max_raise = bettor.stack()
        bettor.call_price = self.current_bet
        print '--------'
        print bettor
        return True

    def prompt_capped(self):
        print 'Unimplemented'
        return False

    def fold(self, bettor):
        bettor.fold()
        num_bettors = len([p for p in self.players if p.betpart.active])
        if num_bettors < 2:
            self.stop = True

    def call(self, bettor):
        bettor.call(self.current_bet)

    def raiseto(self, bettor, amount):
        if (not bettor.min_raise <= amount <= bettor.max_raise or
            not bettor.can_raise):
            raise IllegalRaise(bettor)
        try:
            bettor.raiseto(amount)
        except AllIn as allin:
            print allin
        finally:
            self.last_bettor = bettor
            self.last_raise = bettor.bet - self.current_bet
            self.current_bet = bettor.bet
            print 'Raise by %s'%self.last_bettor.parent.nickname
            print '  by %d to %d'%(self.last_raise, self.current_bet)

if __name__ == '__main__':
    class P:
        def __init__(self, n, s):
            self.nickname = n
            self.stack = s
        def __repr__(self):
            return self.nickname

    players = [P('a', 900), P('b', 200), P('c', 800), P('d', 150), P('e', 800)]
    rotator = Rotator(players, 1)
    for b in rotator.run():
        cc = raw_input()
        if cc[0] == 'f':
            rotator.fold(b)
        elif cc[0] == 'c':
            rotator.call(b)
        elif cc[0] == 'r':
            rotator.raiseto(b, int(cc[1:]))
        print b

    for b in [p.betpart for p in players]:
        print b
