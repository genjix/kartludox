import random
import table
import rotator as rotator_m
import rotator2
import awarder

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
    def __init__(self, players, get_player_hand):
        self.players = players
        self.get_player_hand = get_player_hand

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
        return {streetName: self.board, 'pots': self.pots.notation()}

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
                                 'handname': awarder.handName(handrank)})
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
            self.rotator = rotator_m.Rotator(preflopPlayers)
            self.rotator_m.setBetSize(table.convFact)
        else:
            self.rotator = rotator_m.Rotator(self.activePlayers)
            self.rotator_m.setRaise(table.convFact)
        return self.rotator

    def dealCard(self):
        self.board.append(self.deck.pop())

    def prepareNext(self):
        self.pots.extend(self.rotator_m.createPots())

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

class CardDeck:
    """Represents a deck of cards."""
    def __init__(self):
        # Generate a new deck and shuffle the hands
        ranks = "23456789TJQKA"
        suits = "hdcs"
        self.deck = [rank + suit for rank in ranks for suit in suits]
        random.shuffle(self.deck)
        # Player hands are stored here in a map for added security
        # since this object is created on the heap.
        self.player_hands = {}

    def new_card(self):
        return self.deck.pop()

    def deal_hands(self, players):
        for p in players:
            hand = self.new_card(), self.new_card()
            self.player_hands[p] = hand

    def get_player_hand(self, player):
        return self.player_hands[player]

class StreetStateMachine2:
    Preflop = 0
    Flop = 1
    Turn = 2
    River = 3
    Finished = 4

    def __init__(self, active_players, board, new_card):
        self.players = active_players
        self.current_street = self.Preflop

        self.board = board
        self.deal_new_card = new_card

        # No game with just one player.
        if len(self.players) < 2:
            self.current_street = self.Finished

    def finished(self):
        return self.current_street == self.Finished

    def finish(self):
        self.current_street = self.Finished

    def create_rotator(self, bb):
        if self.current_street == self.Preflop:
            preflop_players = self.players[2:] + self.players[:2]
            rotator = rotator2.Rotator(preflop_players, bb, bb)
        else:
            rotator = rotator2.Rotator(self.players, 0, bb)
        return rotator

    def next(self):
        # Advance through the streets.
        if self.current_street == self.Preflop:
            self.current_street = self.Flop
            # deal flop
            self.board.append(self.deal_new_card())
            self.board.append(self.deal_new_card())
            self.board.append(self.deal_new_card())
            # if game is HU then reverse order.
            if len(self.players) == 2:
                self.players.reverse()
        elif self.current_street  == self.Flop:
            self.current_street = self.Turn
            # deal turn
            self.board.append(self.deal_new_card())
        elif self.current_street == self.Turn:
            self.current_street = self.River
            # deal river
            self.board.append(self.deal_new_card())
        elif self.current_street == self.River:
            self.current_street = self.Finished

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

        active_players = blinds_enforcer.active_players

        #------------------
        # DEAL HANDS!
        #------------------
        card_deck = CardDeck()
        card_deck.deal_hands(active_players)
        yield CardsDealt(active_players, card_deck.get_player_hand)

        street_statemachine = StreetStateMachine2(active_players, self.board,
                                            card_deck.new_card)

        while not street_statemachine.finished():
            rotator = street_statemachine.create_rotator(self.big_blind)
            # Auto-check it all down since there's 1+ players all-in
            # vs 1 active player.
            if rotator.num_active_bettors() > 1:
                for bettor in rotator.run():
                    player = bettor.parent
                    # Players can sit-out beforehand
                    if player.sitting_out:
                        continue
                    choice_actions = Action(player)
                    choice_actions.add(Action.SitOut)
                    choice_actions.add(Action.Fold)
                    to_call = bettor.call_price - bettor.bet
                    if to_call == 0:
                        choice_actions.add(Action.Check)
                    else:
                        assert(to_call > 0)
                        choice_actions.add(Action.Call, to_call)
                    if bettor.can_raise:
                        if rotator.last_raise > 0:
                            bet_or_raise = Action.Raise
                        else:
                            bet_or_raise = Action.Bet
                        choice_actions.add(bet_or_raise, bettor.min_raise,
                                           bettor.max_raise)
                    response = yield choice_actions
                    if len(response) == 1:
                        response, param = response[0], None
                    else:
                        response, param = response[0], int(response[1])

                    if response == Action.Fold or response == Action.SitOut:
                        rotator.fold(bettor)
                    elif response == Action.Call:
                        rotator.call(bettor)
                    elif response == Action.Raise or response == Action.Bet:
                        assert(param is not None)
                        rotator.raiseto(bettor, param)

            bettors = [p.bettor for p in active_players]
            for b in bettors:
                b.new_street()
            street_statemachine.next()

            pots = awarder.Pots(bettors)
            uncontested_pots = pots.uncontested()
            if uncontested_pots:
                for unpot in uncontested_pots:
                    player = unpot.contestors[0].parent
                    yield UncalledBet(player, unpot.size)

                if len(uncontested_pots) == 1:
                    street_statemachine.finish()

            street = street_statemachine.current_street
            if street == street_statemachine.Flop:
                response = yield FlopDealt(self.board, pots)
            elif street == street_statemachine.Turn:
                response = yield TurnDealt(self.board, pots)
            elif street == street_statemachine.River:
                response = yield RiverDealt(self.board, pots)

        #------------------
        # ALL FOUR STREETS
        #------------------
        if False:
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

            pots = []
            if streetState.currentStreet == Street.Flop:
                response = yield FlopDealt(self.board, pots)
            elif streetState.currentStreet == Street.Turn:
                response = yield TurnDealt(self.board, pots)
            elif streetState.currentStreet == Street.River:
                response = yield RiverDealt(self.board, pots)

        if False: # if pots
            # show hands
            endPlayers = streetState.investedPlayers()
            response = yield ShowHands(endPlayers)
            # show hand rankings
            award = awarder.AwardHands(endPlayers, pots, self.board)
            rankings = awarder.calculateRankings()
            response = yield ShowRankings(rankings)
            # who wins what.
            for winner in awarder.award():
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

if __name__ == '__main__':
    pass
