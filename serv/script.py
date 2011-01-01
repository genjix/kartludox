#import random as prng
# Truly random number source
#random = prng.SystemRandom()
import random

import table
import rotator as rotator_m
import rotator2
import awarder

class Action:
    """This class represents a set of possible choices for a player
    at a given time.
    An example might be:
       [ (FOLD,), (CALL, 400), (RAISE, 900, 18000) ]
    Values are in tinybb.
    """
    SIT_IN =      0  # ** = No parameters
    SIT_OUT =     1  # **
    POST_SB =     2
    POST_BB =     3
    POST_SB_BB =  4
    POST_ANTE =   5  # undefined
    FOLD =        6
    CALL =        7
    CHECK =       8  # **
    BET =         9  # 2 parameters- min and max possible raises 
    RAISE =       10 # 2 parameters- min and max possible raises 
    ALL_IN =      11
    LEAVE_SEAT =  12 # **
    WAIT_BB =     13
    AUTOPOST_BLINDS = 14

    action_to_repr = {
        SIT_IN:       'sitin',
        SIT_OUT:      'sitout',
        POST_SB:      'postsb',
        POST_BB:      'postbb',
        POST_SB_BB:   'postsbbb',
        POST_ANTE:    'postante',
        FOLD:         'fold',
        CALL:         'call',
        CHECK:        'check',
        BET:          'bet',
        RAISE:        'raise',
        ALL_IN:       'allin',
        LEAVE_SEAT:   'leave',
        WAIT_BB:      'waitbb',
        AUTOPOST_BLINDS: 'autopost'
    }
    repr_to_action = {
        'sitin':    SIT_IN,
        'sitout':   SIT_OUT,
        'postsb':   POST_SB,
        'postbb':   POST_BB,
        'postsbbb': POST_SB_BB,
        'postante': POST_ANTE,
        'fold':     FOLD,
        'call':     CALL,
        'check':    CHECK,
        'bet':      BET,  
        'raise':    RAISE,
        'allin':    ALL_IN,
        'leave':    LEAVE_SEAT,
        'waitbb':   WAIT_BB,
        'autopost': AUTOPOST_BLINDS
    }

    """actionRepr = {
        SIT_IN:      'Sit In',
        SIT_OUT:     'Sit Out',
        POST_SB:     'Post Small-Blind',
        POST_BB:     'Post Big-Blind',
        POST_SB_BB:   'Post Small & Big Blinds',
        POST_ANTE:   'Post Ante',
        FOLD:       'Fold',
        CALL:       'Call',
        CHECK:      'Check',
        BET:        'Bet',
        RAISE:      'Raise',
        ALL_IN:      'Go All In',
        LEAVE_SEAT:  'Leave Seat',
        WAIT_BB:     'Wait for BB'
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

    def action_names(self):
        return [a[0] for a in self.actions]

    def findAction(self, actName):
        for a in self.actions:
            if a[0] == actName:
                return a
        raise KeyError(Action.action_to_repr[actName])

    def notation(self):
        actdict = {}
        for act in self.actions:
            actName = Action.action_to_repr[act[0]]
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
    def __init__(self, players, gethand):
        self.players = players
        self.gethand = gethand
    def notation(self):
        cards = []
        for p in self.players:
            cards.append({'player': p.nickname, 'cards': self.gethand(p)})
        return {'show hands': cards}

class ShowDown:
    def __init__(self, pots):
        self.pots = pots
    def notation(self):
        return {'showdown': None, 'pots': self.pots}

class ShowRankings:
    def __init__(self, rankings):
        self.rankings = rankings
    def notation(self):
        hand_rankings = []
        for player, handrank in self.rankings.items():
            hand_rankings.append({'player': player.nickname,
                                  'handname': awarder.hand_name(handrank)})
        return {'show rankings': hand_rankings}

class BlindsEnforcer:
    def __init__(self, small_blind, big_blind):
        self.small_blind = small_blind
        self.big_blind = big_blind

        self.blind_todo = [Action.POST_SB_BB, Action.POST_BB, Action.POST_SB]
        self.blind_state = self.blind_todo.pop()
        self.active_players = []
        self.blind_payment = [None, None]

    def prompt(self, player):
        if player is None:
            return False
        if self.blind_state == Action.POST_BB:
            player.paid_state = player.PAID_NOTHING
        elif self.blind_state == Action.POST_SB:
            player.paid_state = player.PAID_BB

        # Everything below this point requires player to be sitting-in
        if player.sitting_out:
            return False

        if self.blind_state == Action.POST_SB_BB:
            # Sometimes new players can sit between former BB
            # and old SB. So we give the BB an upgrade
            if player.paid_state == player.PAID_BB:
                player.paid_state = player.PAID_SB_BB
            # Non-blinds player has already paid blinds
            if player.paid_state == player.PAID_SB_BB:
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
        choice_actions.add(Action.AUTOPOST_BLINDS)
        choice_actions.add(Action.SIT_OUT)
        assert(self.blind_state in (Action.POST_SB, Action.POST_BB, 
                                    Action.POST_SB_BB))
        bettor = player.bettor
        if self.blind_state == Action.POST_SB:
            self.calc_payment(bettor, self.small_blind, 0)
        elif self.blind_state == Action.POST_BB:
            self.calc_payment(bettor, self.big_blind, 0)
        elif self.blind_state == Action.POST_SB_BB:
            self.calc_payment(bettor, self.big_blind, self.small_blind)
            choice_actions.add(Action.WAIT_BB)
        choice_actions.add(self.blind_state, sum(self.blind_payment))
        return choice_actions

    def blind_to_paidstate(self, blind_state):
        assert(blind_state in (Action.POST_SB, Action.POST_BB,
                               Action.POST_SB_BB))
        if blind_state == Action.POST_BB:
            return table.Player.PAID_BB
        else:
            return table.Player.PAID_SB_BB

    def do_autopost(self, player):
        response = (self.blind_state,)
        self.process_response(player, response)

    def process_response(self, player, response):
        """Carry out the response from the blind player. Returns True if they
        are playing this hand. False if not."""
        # Discard args as not needed here.
        response = response[0]
        
        if response == Action.AUTOPOST_BLINDS:
            player.settings.autopost = True
            response = self.blind_state
        assert(response in (self.blind_state, Action.SIT_OUT, Action.WAIT_BB))

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
        # Move to next blind: POST_SB -> POST_BB -> POST_SB_BB

        active_seats = self.active_seats()
        # Set up bet holding objects
        for player in active_seats:
            bettor = rotator2.BettingPlayer()
            player.link(bettor)

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

        pots = None
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
                    choice_actions.add(Action.SIT_OUT)
                    choice_actions.add(Action.FOLD)
                    to_call = bettor.call_price - bettor.bet
                    if to_call == 0:
                        choice_actions.add(Action.CHECK)
                    else:
                        assert(to_call > 0)
                        choice_actions.add(Action.CALL, to_call)
                    if bettor.can_raise:
                        if rotator.current_bet > 0:
                            bet_or_raise = Action.RAISE
                        else:
                            bet_or_raise = Action.BET
                        choice_actions.add(bet_or_raise, bettor.min_raise,
                                           bettor.max_raise)
                    response = yield choice_actions
                    if len(response) == 1:
                        response, param = response[0], None
                    else:
                        response, param = response[0], int(response[1])

                    if response == Action.FOLD or response == Action.SIT_OUT:
                        rotator.fold(bettor)
                    elif response == Action.CALL:
                        rotator.call(bettor)
                    elif response == Action.RAISE or response == Action.BET:
                        assert(param is not None)
                        rotator.raiseto(bettor, param)

            bettors = [p.bettor for p in active_players]
            for b in bettors:
                b.new_street()
            street_statemachine.next()

            pots = awarder.Pots(bettors)
            uncontested_pots = pots.uncontested()
            assert(len(uncontested_pots) < 2)
            if uncontested_pots:
                unpot = uncontested_pots.pop()
                bettor = unpot.contestors[0]
                player = bettor.parent
                if len(pots) == 1:  # only one uncontested_pot
                    yield CollectedMoney(player, unpot.size)
                    street_statemachine.finish()
                    pots.pots.remove(unpot)
                else:
                    assert(not uncontested_pots)
                    yield UncalledBet(player, unpot.size)
                    # Awards it back to them.
                    assert(bettor.stack == bettor.parent.stack)
                bettor.darkbet -= unpot.size
                bettor.stack += unpot.size

            street = street_statemachine.current_street
            if street == street_statemachine.Flop:
                response = yield FlopDealt(self.board, pots)
            elif street == street_statemachine.Turn:
                response = yield TurnDealt(self.board, pots)
            elif street == street_statemachine.River:
                response = yield RiverDealt(self.board, pots)

        if pots:
            first_pot = pots.pots[0]
            all_contestors = first_pot.contestors
            invested_players = [b.parent for b in all_contestors]
            gethand = card_deck.get_player_hand
            response = yield ShowHands(invested_players, gethand)
            award_hands = awarder.AwardHands(invested_players, gethand,
                                             pots, self.board)
            rankings = award_hands.calculate_rankings()
            response = yield ShowRankings(rankings)
            winners = award_hands.calculate_winners()
            for player, potsize in winners:
                yield CollectedMoney(player, potsize)
                player.stack += potsize

        #-------------------
        # DEALER
        #-------------------
        # Add rebuys from table
        self.table.execute_pending_rebuys()

        # Set everyone with zero stack size to sit out
        for player in active_players:
            if player.stack == 0:
                self.table.sit_out(player)

        if self.table.game_state == table.GameState.RUNNING:
            # Find next dealer
            self.table.next_dealer()

