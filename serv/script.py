import table
import rotator
import rotator2
import awardhands

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
    AutopostBlinds = 14

    actionRepr = {
        SitIn:      'sitin',
        SitOut:     'sitout',
        PostSB:     'postsb',
        PostBB:     'postbb',
        PostSBBB:   'postsbbb',
        PostAnte:   'postante',
        Fold:       'fold',
        Call:       'call',
        Check:      'check',
        Bet:        'bet',
        Raise:      'raise',
        AllIn:      'allin',
        LeaveSeat:  'leave',
        WaitBB:     'waitbb',
        AutopostBlinds: 'autopost'
    }

    """actionRepr = {
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
    }"""

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

    def notation(self):
        actdict = {}
        for act in self.actions:
            actName = Action.actionRepr[act[0]]
            actdict[actName] = act[1:]
        notat = {'player': self.player.nickname, 'actions': actdict}
        return notat

class CardsDealt:
    def __init__(self, players):
        self.players = players

class CollectedMoney:
    def __init__(self, player, amount):
        self.player = player
        self.amount = amount
    def notation(self):
        return {'collected': self.amount, 'player': self.player.nickname}

class UncalledBet:
    def __init__(self, player, bet):
        self.player = player
        self.bet = bet
    def notation(self):
        return {'uncalled': self.bet, 'player': self.player.nickname}

# Base class for Flop/Turn/RiverDealt
class StreetDealt:
    def __init__(self, board, pots):
        self.board = board
        self.pots = pots
    def notationBase(self, streetName):
        pots = []
        for pot in self.pots:
            pots.append(pot.notation())
        return {streetName: self.board, 'pots': pots}

class FlopDealt(StreetDealt):
    def notation(self):
        return self.notationBase('flop')

class TurnDealt(StreetDealt):
    def notation(self):
        return self.notationBase('turn')

class RiverDealt(StreetDealt):
    def notation(self):
        return self.notationBase('river')

class ShowHands:
    def __init__(self, players):
        self.players = players
    def notation(self):
        cards = []
        for pBet in self.players:
            p = pBet.parent
            cards.append({'player': p.nickname, 'cards': p.cards})
        return {'showhands': cards}

class ShowDown:
    def __init__(self, pots):
        self.pots = pots
    def notation(self):
        return {'showdown': None, 'pots': self.pots}

class ShowRankings:
    def __init__(self, rankings):
        self.rankings = rankings
    def notation(self):
        handRankings = []
        for playerName, handrank in self.rankings:
            handRankings.append({'player': playerName,
                                 'handname': awardhands.handName(handrank)})
        return {'showrankings': handRankings}

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

        # No game with just one player.
        if len(self.activePlayers) < 2:
            self.currentStreet = Street.Finished

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

        # Advance through the streets.
        if self.currentStreet == Street.Preflop:
            self.currentStreet = Street.Flop
            # deal flop
            self.dealCard()
            self.dealCard()
            self.dealCard()
            # if game is HU then reverse order.
            if len(self.activePlayers) == 2:
                self.activePlayers.reverse()
        elif self.currentStreet  == Street.Flop:
            self.currentStreet = Street.Turn
            # deal turn
            self.dealCard()
        elif self.currentStreet == Street.Turn:
            self.currentStreet = Street.River
            # deal river
            self.dealCard()
        elif self.currentStreet == Street.River:
            self.currentStreet = Street.Finished

    def investedPlayers(self):
        return [p for p in self.activePlayers if p.stillActive]

class BlindsEnforcer:
    def __init__(self, small_blind, big_blind):
        self.small_blind = small_blind
        self.big_blind = big_blind

        self.blind_todo = [Action.PostSBBB, Action.PostBB, Action.PostSB]
        self.blind_state = self.blind_todo.pop()
        self.active_players = []
        self.blind_payment = [None, None]

    def prompt(self, player):
        if player is None:
            return False
        if self.blind_state == Action.PostBB:
            player.paid_state = player.PaidNothing
        elif self.blind_state == Action.PostSB:
            player.paid_state = player.PaidBB

        # Everything below this point requires player to be sitting-in
        if player.sitting_out:
            return False

        # Non-blinds player has already paid blinds
        if (self.blind_state == Action.PostSBBB and
            player.paid_state == player.PaidSBBB):
            self.active_players.append(player)
            return False

        return True

    def calc_payment(self, bettor, pay, darkpay):
        """Calculates the payment possible by a blind player when
        stacksize is too small."""
        assert(max(pay, darkpay) == pay)
        if pay > bettor.stack:
            pay = bettor.stack
            darkpay = 0
        elif pay + darkpay > bettor.stack:
            darkpay = bettor.stack - pay
        self.blind_payment[0] = pay
        self.blind_payment[1] = darkpay

    def choice_actions(self, player):
        """Build choice action list for person need to pay blinds."""
        choice_actions = Action(player)
        choice_actions.add(Action.AutopostBlinds)
        choice_actions.add(Action.SitOut)
        assert(self.blind_state in (Action.PostSB, Action.PostBB, 
                                    Action.PostSBBB))
        bettor = player.bettor
        if self.blind_state == Action.PostSB:
            choice_actions.add(Action.PostSB, self.small_blind)
            self.calc_payment(bettor, self.small_blind, 0)
        elif self.blind_state == Action.PostBB:
            self.calc_payment(bettor, self.big_blind, 0)
        elif self.blind_state == Action.PostSBBB:
            self.calc_payment(bettor, self.big_blind, self.small_blind)
            choice_actions.add(Action.WaitBB)
        choice_actions.add(self.blind_state, sum(self.blind_payment))
        return choice_actions

    def blind_to_paidstate(self, blind_state):
        assert(blind_state in (Action.PostSB, Action.PostBB, Action.PostSBBB))
        if blind_state == Action.PostBB:
            return table.Player.PaidBB
        else:
            return table.Player.PaidSBBB

    def do_autopost(self, player):
        response = (self.blind_state,)
        self.process_response(player, response)

    def process_response(self, player, response):
        """Carry out the response from the blind player. Returns True if they
        are playing this hand. False if not."""
        # Discard args as not needed here.
        response = response[0]
        
        if response == Action.AutopostBlinds:
            player.settings.autopost = True
            response = self.blind_state
        assert(response in (self.blind_state, Action.SitOut, Action.WaitBB))

        if response == self.blind_state:
            player.paid_state = self.blind_to_paidstate(self.blind_state)
            player.bettor.pay(self.blind_payment[0])
            player.bettor.pay_dark(self.blind_payment[1])

            self.active_players.append(player)
            if self.blind_todo:
                self.blind_state = self.blind_todo.pop()

class Script:
    def __init__(self, table):
        # Variables that stay constant between hands
        self.table = table
        # Variables that are externally accessible
        self.board = None

    def active_seats(self):
        seats = self.table.seats
        dealer = self.table.dealer
        # Rotate the seats around the dealer.
        # If we have 6 seats and dealer = seat 3 then we get a list like:
        #   [p3, p4, p5, p0, p1, p2]
        seats = seats[dealer:] + seats[:dealer]
        # Filter empty seats & non players
        seats = [p for p in seats if p and not p.sitting_out]
        if len(seats) != 2:
            assert(len(seats) > 2)
            # SB is next seat after the dealer. Tag dealer on the end
            seats = seats[1:] + seats[:1]
        #else:
            # heads up is a special case
            # dealer *is* the small blind
        return seats

    def run(self):
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

        active_seats = self.active_seats()
        # Set up bet holding objects
        for player in active_seats:
            bettor = rotator2.BettingPlayer()
            player.link(bettor)
            player.newBetPart()

        self.small_blind = self.table.sb
        self.big_blind = table.convFact
        blinds_enforcer = BlindsEnforcer(self.small_blind, self.big_blind)
        for player in active_seats:
            if not blinds_enforcer.prompt(player):
                continue
            choice_actions = blinds_enforcer.choice_actions(player)
            if player.settings.autopost:
                blinds_enforcer.do_autopost(player)
            else:
                response = yield choice_actions
                blinds_enforcer.process_response(player, response)

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
                    betSize = returnedBet.betSize
                    response = yield UncalledBet(player, betSize)

                    remainder = potSize - betSize
                    assert(remainder >= 0)
                    if remainder > 0:
                        assert(rotatorControl.onePlayer())
                        response = yield CollectedMoney(player, remainder)

                # Award pots with single contestor back to them
                for pot in pots:
                    if len(pot.contestors) < 2:
                        assert(len(pot.contestors) == 1)
                        playerObj = pot.contestors[0].parent
                        playerObj.stack += pot.potSize
                        self.pots.remove(pot)
                        response = yield CollectMoney(player, pot.potSize)

                # Merge pots with same players in them.
                # Happens when you had a preflop pot and then a flop pot.
                """for potA in pots:
                    for potB in pots:
                        if potA == potB:
                            continue
                        if potA.contestors == potB.contestors:
                            # merge pots
                            pass"""

                if streetState.currentStreet == Street.Flop:
                    response = yield FlopDealt(self.board, pots)
                elif streetState.currentStreet == Street.Turn:
                    response = yield TurnDealt(self.board, pots)
                elif streetState.currentStreet == Street.River:
                    response = yield RiverDealt(self.board, pots)

        pots = streetState.pots
        if pots:
            # show hands
            endPlayers = streetState.investedPlayers()
            response = yield ShowHands(endPlayers)
            # show hand rankings
            award = awardhands.AwardHands(endPlayers, pots, self.board)
            rankings = award.calculateRankings()
            response = yield ShowRankings(rankings)
            # who wins what.
            for winner in award.award():
                response = yield CollectedMoney(*winner)
            #   CollectedMoney
            # go through and award players the pots
            #response = yield ShowDown(pots)

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
    pass
