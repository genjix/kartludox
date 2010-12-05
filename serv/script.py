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
    Bet =       9  # 2 parameters- min and max possible raises 
    Raise =     10 # 2 parameters- min and max possible raises 
    AllIn =     11
    LeaveSeat = 12 # **
    WaitBB =    13

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
        Bet:        'Bet',
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
            s += '  %s: [ %s %s ]\n'%(p.nickname, c[0], c[1])
        return s

class UncalledBet:
    def __init__(self, player, bet):
        self.player = player
        self.bet = bet
    def __repr__(self):
        pname = self.player.nickname
        return 'Uncalled bet. %s won %d\n'%(self.pname, self.bet)

class FlopDealt:
    def __init__(self, board, pots):
        self.board = board
        self.pots = pots
    def __repr__(self):
        b = self.board
        s = 'Flop: [ %s %s %s ]\n'%(b[0], b[1], b[2])
        for p in self.pots:
            s += '  %s\n'%p
        return s

class TurnDealt:
    def __init__(self, board, pots):
        self.board = board
        self.pots = pots
    def __repr__(self):
        b = self.board
        s = 'Turn: [ %s %s %s ] [ %s ]\n'%(b[0], b[1], b[2], b[3])
        for p in self.pots:
            s += '  %s\n'%p
        return s

class RiverDealt:
    def __init__(self, board, pots):
        self.board = board
        self.pots = pots
    def __repr__(self):
        b = self.board
        s = 'River: [ %s %s %s ] [ %s ] [ %s ]\n'% \
            (b[0], b[1], b[2], b[3], b[4])
        for p in self.pots:
            s += '  %s\n'%p
        return s

class ShowDown:
    def __init__(self, pots):
        self.pots = pots
    def __repr__(self):
        s = ''
        for p in self.pots:
            s += '%d %d %s\n'%(p.betSize, p.potSize, p.contestors)
        return s

class Street:
    Nothing = 0
    Preflop = 1
    Flop = 2
    Turn = 3
    River = 4
    Finished = 5

class StreetStateMachine:
    def __init__(self, activePlayers, board, deck):
        self.activePlayers = [p.betPart for p in activePlayers]
        self.currentStreet = Street.Preflop
        self.rotator = None
        self.pots = []

        self.deck = deck
        self.board = board

    def finished(self):
        return self.currentStreet == Street.Finished

    def createRotator(self):
        if self.currentStreet == Street.Preflop:
            preflopPlayers = self.activePlayers[2:] + self.activePlayers[:2]
            self.rotator = rotator.Rotator(preflopPlayers)
            self.rotator.setBetSize(table.convFact)
        else:
            self.rotator = rotator.Rotator(self.activePlayers)
            self.rotator.setRaise(table.convFact)
        return self.rotator

    def dealCard(self):
        self.board.append(self.deck.pop())

    def prepareNext(self):
        self.pots.extend(self.rotator.createPots())
        # award pots with single contestor back to them
        for pot in []:
            if len(pot.contestors) < 2:
                assert(len(pot.contestors) == 1)
                playerObj = pot.contestors[0].parent
                playerObj.stack += pot.potSize
                self.pots.remove(pot)

        # If no pots left then finished
        if self.rotator.oneBettingPlayer():
            self.currentStreet = Street.Finished
        # Advance through the streets.
        elif self.currentStreet  == Street.Preflop:
            self.currentStreet = Street.Flop
            # deal flop
            self.dealCard()
            self.dealCard()
            self.dealCard()
        elif self.currentStreet  == Street.Flop:
            self.currentStreet = Street.Turn
            # deal turn
            self.dealCard()
        elif self.currentStreet  == Street.Turn:
            self.currentStreet = Street.River
            # deal river
            self.dealCard()
        elif self.currentStreet  == Street.River:
            self.currentStreet = Street.Finished

class Script:
    def __init__(self, table):
        self.table = table
        self.board = None

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
                if blindState == Action.PostSB:
                    player.paidState = table.Player.PaidState.PaidSBBB
                    player.betPart.pay(blindPayment)
                elif blindState == Action.PostSBBB:
                    player.paidState = table.Player.PaidState.PaidSBBB
                    player.betPart.pay(table.convFact)
                    player.betPart.payDark(self.table.sb)
                elif blindState == Action.PostBB:
                    player.paidState = table.Player.PaidState.PaidBB
                    player.betPart.pay(blindPayment)
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
        # DEAL HANDS!
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
        # ALL FOUR STREETS
        #------------------
        streetState = StreetStateMachine(activePlayers, self.board, deck)

        while not streetState.finished():
            rotatorControl = streetState.createRotator()

            i = self.rotateTheAction(rotatorControl)
            try:
                # re-yield rotateTheAction
                choiceActions = i.next()
                while True:
                    response = yield choiceActions
                    choiceActions = i.send(response)
            except StopIteration:
                streetState.prepareNext()

                pots = streetState.pots
                if len(pots[-1].contestors) == 1:
                    returnedBet = pots.pop()
                    player = returnedBet.contestors[0].parent
                    potSize = returnedBet.potSize
                    player.stack += potSize
                    response = yield UncalledBet(player, potSize)

                if streetState.currentStreet == Street.Flop:
                    response = yield FlopDealt(self.board, pots)
                elif streetState.currentStreet == Street.Turn:
                    response = yield TurnDealt(self.board, pots)
                elif streetState.currentStreet == Street.River:
                    response = yield RiverDealt(self.board, pots)

        pots = streetState.pots
        response = yield ShowDown(pots)

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

        if self.table.gameState == table.GameState.Running:
            # Find next dealer
            self.table.nextDealer()

    def rotateTheAction(self, rotatorControl):
        # Auto-check it all down since there's 1+ players all-in
        # vs 1 active player.
        if rotatorControl.oneBettingPlayer():
            raise StopIteration

        for player, capped in rotatorControl.run():
            # Players can sit-out beforehand
            if player.parent.sitOut:
                continue

            stackSize = player.parent.stack
            canRaise = not capped
            callAllIn = False
            raiseAllIn = False
            callSizeTotal = rotatorControl.call()
            minRaiseSize = rotatorControl.minRaise()
            maxRaiseSize = player.betPlaced + stackSize
            prevBet = player.betPlaced

            toCall = callSizeTotal - prevBet
            if stackSize <= toCall:
                canRaise = False
                callAllIn = True
                callSizeTotal = stackSize + prevBet
                toCall = stackSize
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
                if rotatorControl.lastBet > 0:
                    betraiseAct = Action.Raise
                else:
                    betraiseAct = Action.Bet
                choiceActions.add(betraiseAct, minRaiseSize, maxRaiseSize)
            response = yield choiceActions

            if response[0] == Action.Call:
                player.betPlaced = callSizeTotal
                if callAllIn:
                    player.isAllIn = True
            elif (response[0] == Action.Raise or
                  response[0] == Action.Bet):
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
