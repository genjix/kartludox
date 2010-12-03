import table
import rotator

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

    def actionNames(self):
        return [a[0] for a in self.actions]

    def findAction(self, actName):
        for a in self.actions:
            if a[0] == actName:
                return a
        raise KeyError(Action.actionRepr[actName])

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
        self.board = None

    def regenerateList(self):
        # Prune players that sit-out
        self.players = [p for p in self.players if not p.sitOut]
        if len(players) < 2:
            # award pot to only remaining player
            # if applicable
            raise StopIteration

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

        # flop/turn/river cards.
        self.board = []

        #------------------
        # BLINDS
        #------------------
        # We don't worry if the small blind
        # has paid the Big Blind or not.
        #
        # Rotate clockwise until we find a non-sitting out player
        # Make them pay the relevant blind.
        # Move to next blind: PostSB -> PostBB -> PostSB/BB

        activeSeats = [p for p in seats if p and not p.sitOut]
        # Set up bet holding objects
        for player in activeSeats:
            player.newBetPart()

        if len(activeSeats) == 2:
            # heads up is a special case
            # dealer *is* the small blind
            # Copy list cos we're going to move elements around
            blindList = seats[:]
        else:
            # SB is next seat after the dealer. Tag dealer on the end
            blindList = seats[1:] + seats[:1]

        blindToDo = [Action.PostSBBB, Action.PostBB, Action.PostSB]
        blindState = blindToDo.pop()

        # Try to get payment
        for player in blindList:
            if player is None:
                continue
            if blindState == Action.PostBB:
                player.paidState = table.Player.PaidState.Nothing
            # Non-blinds player has already paid blinds
            elif (blindState == Action.PostSBBB and
                  player.paidState == player.PaidState.PaidSBBB):
                activePlayers.append(player)
                continue
            if player.sitOut:
                if blindState == Action.PostSB:
                    player.paidState = table.Player.PaidState.PaidBB
                continue

            if blindState == Action.PostSB:
                blindSize = self.table.sb
            elif blindState == Action.PostBB:
                blindSize = table.convFact
            elif blindState == Action.PostSBBB:
                blindSize = self.table.sb + table.convFact
            # If they have a puny stack < SB, then pay as much as pos
            blindPayment = \
                player.stack > blindSize and blindSize or player.stack
            # Build up response set
            choiceActions = Action(player)
            choiceActions.add(blindState, blindPayment)
            if blindState == Action.PostSBBB:
                choiceActions.add(Action.WaitBB)
            choiceActions.add(Action.SitOut)
            response = yield choiceActions

            if (response[0] == Action.PostSB or
                response[0] == Action.PostBB or
                response[0] == Action.PostSBBB):
                # Player has payed up! Mark them as such.
                if (blindState == Action.PostSB or
                    blindState == Action.PostSBBB):
                    player.paidState = table.Player.PaidState.PaidSBBB
                elif blindState == Action.PostSBBB:
                    player.paidState = table.Player.PaidState.PaidBB
                player.betPart.payDark(blindPayment)
                activePlayers.append(player)
                # Move to the next state. Stop at the last state.
                if blindToDo:
                    blindState = blindToDo.pop()
            elif response[0] == Action.SitOut:
                if blindState == Action.PostSB:
                    player.paidState = table.Player.PaidState.PaidBB
                elif (blindState == Action.PostBB or
                      blindState == Action.PostSBBB):
                    player.paidState = table.Player.PaidState.Nothing
        del blindList

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
        preflopPlayers = activePlayers[2:] + activePlayers[:2]
        preflopPlayers = [p.betPart for p in preflopPlayers]
        preflopRotator = rotator.Rotator(preflopPlayers)
        preflopRotator.setBetSize(bb)
        for player, capped in preflopRotator.run():
            # Players can sit-out beforehand
            if player.parent.sitOut:
                continue

            stackSize = player.parent.stack
            canRaise = not capped
            callAllIn = False
            raiseAllIn = False
            callSizeTotal = preflopRotator.call()
            minRaiseSize = preflopRotator.minRaise()
            maxRaiseSize = player.betPlaced + stackSize
            prevBet = player.betPlaced

            toCall = callSizeTotal - prevBet
            if stackSize <= toCall:
                canRaise = False
                callAllIn = True
                callSizeTotal = stackSize + prevBet
            toMinRaise = minRaiseSize - prevBet
            if stackSize <= toMinRaise:
                minRaiseSize = stackSize + prevBet
                maxRaiseSize = minRaiseSize
                raiseAllIn = True

            choiceActions = Action(player.parent)
            choiceActions.add(Action.SitOut)
            choiceActions.add(Action.Fold)
            if toCall == 0:
                choiceActions.add(Action.Check)
            else:
                choiceActions.add(Action.Call, toCall)
            if canRaise:
                choiceActions.add(Action.Raise, minRaiseSize, maxRaiseSize)
            response = yield choiceActions

            if response[0] == Action.Call:
                player.betPlaced = callSizeTotal
                if callAllIn:
                    player.isAllIn = True
            elif response[0] == Action.Raise:
                raiseSize = response[1]

                if raiseSize < minRaiseSize:
                    raiseSize = minRaiseSize
                elif raiseSize > maxRaiseSize:
                    raiseSize = maxRaiseSize

                if raiseAllIn:
                    player.betPlaced = minRaiseSize
                    player.isAllIn = True
                elif raiseSize == maxRaiseSize:
                    player.betPlaced = maxRaiseSize
                    player.isAllIn = True
                elif raiseSize >= minRaiseSize:
                    player.betPlaced = raiseSize
            elif response[0] == Action.Fold or response[0] == Action.SitOut:
                player.stillActive = False
                continue

            addedBet = player.betPlaced - prevBet
            player.parent.stack -= addedBet

        pots = preflopRotator.createPots()
        for p in pots:
            print p.betSize, p.potSize, p.contestors

        ### Do this at the end of the hand
        #-------------------
        # DEALER
        #-------------------
        # Add rebuys from table
        self.table.executePendingRebuys()

        # Set everyone with zero stack size to sit out
        for player in activePlayers:
            if player.stack == 0:
                self.table.sitOutPlayer(player)

        # Find next dealer
        self.table.nextDealer()


if __name__ == '__main__':
    cash = table.Table(9, 0.25, 0.5, 0, 5000, 25000)
    cash.registerScheduler(table.Schedule())
    cash.start()
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
    #cash.sitOut('honn')
    cash.sitIn('honn')
    cash.sitIn('mison')
    cash.sitIn('john')
    cash.sitIn('mizir')
    cash.dealer = 3

    cash.seats[3].stack = 400

    print '-------------'

    scr = Script(cash)
    run = scr.run()
    act = run.next()
    print act
    try:
        act = run.send((Action.PostSB,))
        #act.player.sitOut = True
        # check game shouldn't halt here
        print act
        #print run.send((Action.SitOut,))
        print run.send((Action.PostBB,))
        print run.send((Action.PostSBBB,))
        print run.send((Action.PostSBBB,))
        act = run.send((Action.PostSBBB,))

        print act

        print run.send((Action.Call,))
        act = run.send((Action.Call,))
        print act

        if len(act.actions) == 3:
            print run.send((Action.Raise, act.actions[2][1]))
        else:
            print run.send((Action.Call,))
        print run.send((Action.Call,))
    except StopIteration:
        print 'END'
    print cash
