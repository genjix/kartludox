import itertools

class AllIn:
    """Exception for when a player is all-in."""
    def __init__(self, bettor):
        self.bettor = bettor
    def __repr__(self):
        b = self.bettor
        return '%s is all-in for %d'%(b.parent.nickname, b.bet)

class IllegalRaise:
    """Exception for an illegal raise size. Either:
      - Not allowed to raise.
      - Raise below the minimum.
      - Or above the maximum."""
    def __init__(self, bettor, rsize):
        self.bettor = bettor
        self.rsize = rsize
    def __repr__(self):
        return 'Non-allowed raise %d for:\n%s'%(self.rsize, self.bettor)

class BettingPlayer:
    """ Represents the betting 'part' of a player.
    Is non static and changes between hands."""
    def __init__(self):
        # The current bet placed.
        self.bet = 0
        # Dark pool bets are not counted as part of the current bet
        # e.g antes
        self.darkbet = 0
        # Folded players are set inactive.
        self.active = True

        # Messages from rotator
        self.can_raise = True
        self.min_raise = 0
        self.max_raise = 0
        self.call_price = 0

    def add_parent(self, parent):
        self.parent = parent
        self.new_street()

    def new_street(self):
        """Called at the beginning of each new betting street.
        Places the current bet in the darkpool and resets itself."""
        self.begin_stack = self.parent.stack
        self.darkbet += self.bet
        self.bet = 0

    def pay(self, charge):
        assert(not charge < 0)
        self.parent.stack -= charge
        self.bet += charge
    def pay_dark(self, charge):
        assert(not charge < 0)
        self.parent.stack -= charge
        self.darkbet += charge

    @property
    def stack(self):
        return self.parent.stack

    def fold(self):
        self.active = False

    def call(self, bet):
        price = bet - self.bet
        self.pay(price)

    def raiseto(self, bet):
        price = bet - self.bet
        # If price == stack then go all-in
        if price >= self.parent.stack:
            self.pay(self.parent.stack)
            raise AllIn(self)
        else:
            self.pay(price)

    def set_prices(self, call, rmin=None, rmax=None):
        """These values are stored just to indicate externally what the
        allowed sizes are for min raise, calling, ..."""
        if rmin is None:
            self.can_raise = False
        else:
            self.can_raise = True
            self.min_raise = rmin
            self.max_raise = rmax
        self.call_price = call

    def __repr__(self):
        srep = '%s stack=%d bets=(%d, %d) active=%s\n'%\
                    (self.parent.nickname, self.parent.stack, self.bet,
                     self.darkbet, self.active)
        srep += 'call=%d'%self.call_price
        if self.can_raise:
            srep += '\traise=%d to %d'%(self.min_raise, self.max_raise)
        return srep

class Rotator:
    """The rotator is an object that takes the players and cycles through
    returning the correct player when it's their turn, processing them,
    and calculating the relevant bets.

    Script sets up and then runs a rotator internally and acts as a glue
    between the player and this object.

    There are 4 states: Open, Capped, Closed and Finished.
    These dictate the type of betting action occuring on the table."""

    # All of these states can move to BettingFinished
    BettingOpen = 0     # Normal betting -> BettingCapped
    BettingCapped = 1   # Allin < full raise -> (BettingOpen, BettingClosed)
    BettingClosed = 2   # No more raising allowed.
    BettingFinished = 3 # Stop.

    def __init__(self, active_players, current_bet, last_raise):
        """active_players should be the players that posted their blinds
        and are sitting in.
        current_bet is the size of the bet (usually the big blind size)."""

        self.players = active_players

        self.last_bettor = None
        self.cap_bettor = None
        # Stores rotator state. Important
        self.state = Rotator.BettingOpen
        # For the first round at least, current_bet != last_bettor.bet
        # Like when the BB is all-in < 1 bb.
        self.current_bet = current_bet
        self.last_raise = last_raise

    def run(self):
        """Main run loop. Continually cycle until we reach
        the end state. Branches into relevant subfunctions:
            - prompt_open
            - prompt_capped
        depending on current state. They return True to yield bettor."""
        for player in itertools.cycle(self.players):
            bettor = player.bettor
            if self.state == Rotator.BettingOpen:
                if self.prompt_open(bettor):
                    yield bettor
            elif (self.state == Rotator.BettingCapped or
                  self.state == Rotator.BettingClosed):
                if self.prompt_capped(bettor):
                    yield bettor
            # End state has been reached. Finish.
            # Can be set in above block hence it's not joined by an elif.
            if self.state == Rotator.BettingFinished:
                break

    def prompt_open(self, bettor):
        if bettor == self.last_bettor:
            # Table went a full cycle without re-raising. Finish up.
            self.state = Rotator.BettingFinished
            return False
        elif not bettor.active:
            # Player folded. Continue on.
            return False
        elif bettor.stack == 0:
            # Player is all-in. Continue on.
            return False

        # First player at the table and beginning of the hand.
        # Set *someone* as the last_bettor to start.
        if not self.last_bettor:
            self.last_bettor = bettor
        # Do allowed-raise calculations
        self.bettor_free_raise(bettor)
        return True

    def bettor_free_raise(self, bettor):
        """Calculates the allowed raise/call sizes for a bettor."""
        assert((self.state != Rotator.BettingClosed or
                self.state != Rotator.BettingFinished))
        # Normal betting scenario.
        if self.state == Rotator.BettingOpen:
            facing_bet = self.current_bet
            min_raise = self.current_bet + self.last_raise
        # Someone went in for < full raise. However raising is still allowed
        # as this bettor hasn't acted yet.
        elif self.state == Rotator.BettingCapped:
            # Current price to call = cap bettor all in price
            facing_bet = self.cap_bettor.bet
            # Original Bet + All-in bet + Price to complete + another raise
            min_raise = self.current_bet + 2*self.last_raise

        if bettor.begin_stack > facing_bet:
            # Can only raise if we have more money than it costs to call.
            bettor.can_raise = True
            bettor.min_raise = min(min_raise, bettor.begin_stack)
            bettor.max_raise = bettor.begin_stack
            bettor.call_price = facing_bet
        else:
            bettor.can_raise = False
            # stack < price to call, so we can only call all-in
            bettor.call_price = bettor.begin_stack

    def prompt_capped(self, bettor):
        if not bettor.active:
            # Continue to next bettor. This one has folded.
            return False
        elif bettor == self.last_bettor:
            # Came back to original raiser before SS went all-in and capped
            # the betting. Betting is now closed- no more raises.
            self.state = Rotator.BettingClosed
        elif bettor == self.cap_bettor:
            # Came back to SS that went all-in < full raise. Stop betting.
            self.state = Rotator.BettingFinished
            return False

        if self.state == Rotator.BettingClosed:
            # Cannot raise
            self.bettor_capped_raise(bettor)
        elif self.state == Rotator.BettingCapped:
            # Can raise
            self.bettor_free_raise(bettor)
        return True

    def bettor_capped_raise(self, bettor):
        bettor.can_raise = False
        # Can only pay as much as can afford.
        bettor.call_price = min(self.cap_bettor.bet, bettor.begin_stack)

    def num_bettors(self):
        """Number of bettors NOT folded."""
        return len([p for p in self.players if p.bettor.active])
    def num_active_bettors(self):
        """Number of bettors NOT folded and NOT allin."""
        return len([p for p in self.players if 
                    p.bettor.active and p.stack > 0])

    def fold(self, bettor):
        bettor.fold()
        if self.num_active_bettors() < 2:
            self.state = Rotator.BettingFinished

    def call(self, bettor):
        bettor.call(bettor.call_price)

    def raiseto(self, bettor, amount):
        if (not bettor.min_raise <= amount <= bettor.max_raise or
            not bettor.can_raise):
            raise IllegalRaise(bettor, amount)
        try:
            bettor.raiseto(amount)
        except AllIn as allin:
            # How much bettor raised by
            raise_size = bettor.bet - self.current_bet
            # Raised allin < full raise -> caps the betting
            if raise_size < self.last_raise:
                # Betting capped. Players can still raise until
                # it becomes closed.
                self.state = Rotator.BettingCapped
                self.cap_bettor = bettor
            else:
                self.normal_raise(bettor)
        else:
            self.normal_raise(bettor)

    def normal_raise(self, bettor):
        # Re-open betting
        if self.state == Rotator.BettingCapped:
            self.state = Rotator.BettingOpen
        self.last_bettor = bettor
        self.last_raise = bettor.bet - self.current_bet
        self.current_bet = bettor.bet

if __name__ == '__main__':
    class P:
        def __init__(self, n, s):
            self.nickname = n
            self.stack = s
        def link(self, bettor):
            self.bettor = bettor
            self.bettor.add_parent(self)
        def __repr__(self):
            return self.nickname

    def do_rotation(rotator):
        for b in rotator.run():
            print b
            cc = raw_input()
            if cc[0] == 'f':
                rotator.fold(b)
            elif cc[0] == 'c':
                rotator.call(b)
            elif cc[0] == 'r':
                rotator.raiseto(b, int(cc[1:]))
            print b
            if rotator.state == Rotator.BettingOpen:
                print 'Betting Open'
            elif rotator.state == Rotator.BettingCapped:
                print 'Someone went all-in < full raise but can still bet'
            elif rotator.state == Rotator.BettingClosed:
                print 'No more raises.'
            elif rotator.state == Rotator.BettingFinished:
                print 'Betting finished. Closing up shop.'
            else:
                print 'Severe error wtf %d'%rotator.state
            print '---------'

    def show_all(players):
        for b in [p.bettor for p in players]:
            print b

    #players = [P('a', 900), P('b', 200), P('c', 800), P('SB', 150), P('BB', 800)]
    players = [P('U', 900), P('SB', 900), P('BB', 900)]
    # Attach betting objects to all the players.
    for player in players:
        bettor = BettingPlayer()
        player.link(bettor)
    players[1].bettor.pay(50)
    players[2].bettor.pay(100)

    rotator = Rotator(players, 100, 100)
    do_rotation(rotator)

    # Begin new street
    for player in players:
        player.bettor.new_street()
    show_all(players)
    print '---------'

    players = players[-2:] + players[:-2]
    rotator = Rotator(players, 0, 100)
    #do_rotation(rotator)
    #show_all(players)

