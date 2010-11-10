import table

class Action:
    """This class represents a set of possible choices for a player
    at a given time.
    An example might be:
       [ (Fold,), (Call, 400), (Raise, 900, 18000) ]
    Values are in tinybb.
    """
    SitIn =     0  # ** = No parameters
    SitOut =    1  # **
    PostSB =    2
    PostBB =    3
    PostSBBB =  4
    PostAnte =  5  # undefined
    Fold =      6
    Call =      7
    Check =     8  # **
    Raise =     9  # 2 parameters- min and max possible raises 
    AllIn =     10
    LeaveSeat = 11 # **
    WaitBB =    12

    actionRepr = {
        SitIn:      'Sit In',
        SitOut:     'Sit Out',
        PostSB:     'Post Small-Blind',
        PostBB:     'Post Big-Blind',
        PostSBBB:   'Post Small & Big Blinds',
        PostAnte:   'Post Ante',
        Fold:       'Fold',
        Call:       'Call',
        Check:      'Check',
        Raise:      'Raise',
        AllIn:      'Go All In',
        LeaveSeat:  'Leave Seat',
        WaitBB:     'Wait for BB'
    }

    def __init__(self, player):
        self.player = player
        self.actions = []
    def add(self, action, arg0=None, arg1=None):
        if not arg0:
            self.actions.append((action,))
        elif not arg1:
            self.actions.append((action, arg0))
        else:
            self.actions.append((action, arg0, arg1))
    def __repr__(self):
        s = ''
        if self.player:
            s += 'Player: %s\n'%self.player.nickname
        for act in self.actions:
            s += '  %s'%Action.actionRepr[act[0]]
            if len(act) > 1:
                s += ' %d'%act[1]
                if len(act) > 2:
                    s += '-%d'%act[2]
            s += '\n'
        return s

class CardsDealt:
    def __init__(self, players):
        self.players = players
    def __repr__(self):
        s = 'Dealt to:\n'
        for p in self.players:
            c = p.cards
            s += '  %s: [%s %s]\n'%(p.nickname, c[0], c[1])
        return s

class Script:
    def __init__(self, table):
        self.table = table

    def regenerateList(self):
        # Prune players that sit-out
        self.players = [p for p in self.players if not p.sitOut]
        if len(players) < 2:
            # award pot to only remaining player
            # if applicable
            raise StopIteration

    def deductPayment(self, player, payment, pots, sidepotCreators):
        # deduct the payment
        player.stack -= payment
        pots[-1] += payment
        if player.stack == 0:
            # new sidepot created, player allin
            pots.append(0)
            sidepotCreators.append(player)
    def run(self):
        seats = self.table.seats
        dealer = self.table.dealer
        # Rotate the seats around the dealer.
        # If we have 6 seats and dealer = seat 3 then we get a list like:
        #   [p3, p4, p5, p0, p1, p2]
        seats = seats[dealer:] + seats[:dealer]

        # Active people in the current hand
        # Added to the list preflop as the hand progresses.
        activePlayers = []

        # If a side pot is created then the last value becomes the main
        # pot.
        pots = [0]
        # Everytime a new side pot is made then whoever capped the
        # action creating a new sidepot by going all-in is added to this.
        sidepotCreators = []

        #------------------
        # SMALL BLIND
        #------------------
        # We don't worry if the small blind
        # has paid the Big Blind or not.
        #
        # Rotate clockwise until we find a non-sitting out player
        # that pays the SB. Likewise for BB too.

        activeSeats = [p for p in seats if p and not p.sitOut]
        if len(activeSeats) == 2:
            # heads up is a special case
            # dealer *is* the small blind
            # Copy list cos we're going to move elements around
            smallBlindList = seats[:]
        else:
            # SB is next seat after the dealer. Tag him on the end
            smallBlindList = seats[1:] + seats[:1]

        # Try to get payment
        for player in smallBlindList:
            if not player or player.sitOut:
                continue
            sb = self.table.sb
            # If they have a puny stack < SB, then pay as much as pos
            payment = player.stack > sb and sb or player.stack
            # Build up response set
            choiceActions = Action(player)
            choiceActions.add(Action.PostSB, payment)
            choiceActions.add(Action.SitOut)
            response = yield choiceActions

            if response[0] == Action.PostSB:
                # Player has payed up! Mark them as such.
                player.paidState = table.Player.PaidState.PaidSBBB
                self.deductPayment(player, payment, pots, sidepotCreators)
                activePlayers.append(player)
                break
        del smallBlindList

        assert(len(activePlayers) == 1)

        #------------------
        # BIG BLIND
        #------------------
        # First we find cycle, stopping once we find SB
        # Then mark next player paid state as Not Paid, ask for BB
        # ... and if not paid continue to next player.
        idxSB = seats.index(activePlayers[0])
        bigBlindList = seats[idxSB+1:] + seats[:idxSB+1]

        for player in bigBlindList:
            if not player or player.sitOut:
                continue
            bb = table.convFact
            payment = player.stack > bb and bb or player.stack

            player.paidState = table.Player.PaidState.Nothing

            choiceActions = Action(player)
            choiceActions.add(Action.PostBB, payment)
            choiceActions.add(Action.SitOut)
            response = yield choiceActions

            if response[0] == Action.PostBB:
                player.paidState = table.Player.PaidState.PaidBB
                self.deductPayment(player, payment, pots, sidepotCreators)
                activePlayers.append(player)
                break
        del bigBlindList

        assert(len(activePlayers) == 2)

        idxSB = seats.index(activePlayers[0])
        # Make sure SB player is first in list
        if idxSB != 0:
            # Rotate list around SB if not
            remainingPlayers = seats[idxSB:] + seats[:idxSB]
        else:
            remainingPlayers = seats[:]
        assert(remainingPlayers.index(activePlayers[0]) == 0)

        # Delete from SB up to and including the BB
        idxBB = remainingPlayers.index(activePlayers[1])
        del remainingPlayers[:idxBB+1]

        # remainingPlayers now contains the remaining players
        # from UTG to the dealer

        # We loop through this twice:
        # - First to request SB/BB from anyone who didn't pay yet
        # - To add to the activePlayers list.

        #------------------
        # POST SB/BB
        #------------------
        # If you need to post your SB/BB
        for player in remainingPlayers:
            if not player or player.sitOut:
                continue
            if player.paidState == player.PaidState.WaitingBB or \
              player.paidState == player.PaidState.PaidSBBB:
                continue
            assert(player.paidState == player.PaidState.Nothing)

            sbbb = self.table.sb + table.convFact
            # If they have a puny stack < SB, then pay as much as pos
            payment = player.stack > sbbb and sbbb or player.stack
            # Build up response set
            choiceActions = Action(player)
            choiceActions.add(Action.PostSBBB, payment)
            choiceActions.add(Action.WaitBB)
            choiceActions.add(Action.SitOut)
            response = yield choiceActions

            if response[0] == Action.PostSBBB:
                # Player has payed up! Mark them as such.
                player.paidState = table.Player.PaidState.PaidSBBB
                self.deductPayment(player, payment, pots, sidepotCreators)
                # Unlike for SB/BB we don't append to activePlayers here...
                # We will do that after this for loop so we get the players
                # in order.
            elif response[0] == Action.WaitBB:
                player.paidState = table.Player.PaidState.WaitingBB

        # Now add the players in the game to activePlayers list
        # Remember: activePlayers already has SB [0] and BB [1]
        for player in remainingPlayers:
            if not player or player.sitOut:
                continue
            if player.paidState == player.PaidState.PaidSBBB:
                activePlayers.append(player)

        #------------------
        # DEAL HAND!
        #------------------
        # Generate a new deck and shuffle the hands
        ranks = "23456789TJQKA"
        suits = "hdcs"
        deck = [rank + suit for rank in ranks for suit in suits]
        table.random.shuffle(deck)

        # Deal cards!
        for player in activePlayers:
            player.cards = deck.pop(), deck.pop()
        yield CardsDealt(activePlayers)

        #------------------
        # PREFLOP MINUS BLINDS
        #------------------
        # Current bet to call is big blind
        currentBet = table.convFact
        # For calculating min/max possible raise
        lastRaise = table.convFact
        # Start from UTG and move to dealer
        for player in activePlayers[2:]:
            assert(player and not player.sitOut and \
                player.paidState == player.PaidState.PaidSBBB)

            # Pay as much as the player can afford
            callPayment = player.stack > currentBet and currentBet \
                or player.stack
            minRaise = currentBet + lastRaise
            # If players stack < min raise then thats only pos raise size
            minRaise = player.stack > minRaise and minRaise \
                or player.stack
            raiseMax = player.stack > minRaise and player.stack \
                or minRaise

            # Build up possible responses
            choiceActions = Action(player)
            choiceActions.add(Action.Fold)
            choiceActions.add(Action.Call, callPayment)
            choiceActions.add(Action.Raise, minRaise, raiseMax)
            choiceActions.add(Action.AllIn)
            response = yield choiceActions

        ### Do this at the end of the hand
        #-------------------
        # DEALER
        #-------------------
        # Find next dealer
        # Add rebuys from table
        # Set everyone with zero stack size to sit out

if __name__ == '__main__':
    cash = table.Table(9, 0.25, 0.5, 0, 5000, 25000)
    cash.registerScheduler(table.Schedule())
    cash.addPlayer('john', 0)
    cash.addMoney('john', 5000)
    cash.addPlayer('mison', 1)
    cash.addMoney('mison', 10000)
    cash.addPlayer('lorea', 2)
    cash.addMoney('lorea', 10000)
    cash.addPlayer('honn', 3)
    cash.addMoney('honn', 10000)
    cash.addPlayer('mizir', 6)
    cash.addMoney('mizir', 10000)
    cash.sitIn('honn')
    cash.sitIn('lorea')
    print cash
    cash.sitOut('honn')
    cash.sitIn('honn')
    cash.sitIn('mison')
    cash.sitIn('john')
    cash.sitIn('mizir')
    cash.start()

    cash.seats[0].stack = 200

    print '-------------'

    scr = Script(cash)
    run = scr.run()
    act = run.next()
    print act
    try:
        act = run.send((Action.PostSB,))
        act.player.sitOut = True
        # check game shouldn't halt here
        print act
        print run.send((Action.SitOut,))
        print run.send((Action.PostBB,))
        print run.send((Action.PostSBBB,))
        act = run.send((Action.PostSBBB,))

        print act

        print run.send((Action.Call,))
        print run.send((Action.Call,))

        print run.send((Action.Call,))
    except StopIteration:
        print 'END'
    print cash
