from collections import OrderedDict

class BlackjackModel:
    VALORES_STANDARD = ['A', 'K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2']
    VALORES_POWER = ['A', 'K', 'Q', 'J', '8', '7', '6', '5', '4', '3', '2']
    NUM_DECKS_INICIAL = 8

    def __init__(self):
        self.game_mode = 'standard'
        self.reset_shoe()

    def _get_card_value(self, card_face: str) -> int:
        if card_face in ['2', '3', '4', '5', '6']: return 1
        if card_face in ['10', 'J', 'Q', 'K', 'A']: return -1
        return 0

    def reset_shoe(self, mode: str = 'standard'):
        self.game_mode = mode
        self.running_count = 0
        self.cards_dealt = 0
        self.shoe = OrderedDict()
        
        valores = self.VALORES_STANDARD if mode == 'standard' else self.VALORES_POWER
        self.cards_per_deck = len(valores) * 4
        self.total_cards = self.NUM_DECKS_INICIAL * self.cards_per_deck
        
        for valor in valores:
            for naipe in ['Hearts', 'Diamonds', 'Clubs', 'Spades']: 
                self.shoe[f"{valor}_{naipe}"] = self.NUM_DECKS_INICIAL
                
        self.history = []

    def process_card(self, valor: str, naipe: str):
        card_key = f"{valor}_{naipe}"
        if self.shoe.get(card_key, 0) > 0:
            self.shoe[card_key] -= 1
            self.cards_dealt += 1
            self.running_count += self._get_card_value(valor)
            self.history.insert(0, card_key)
            if len(self.history) > 3: self.history.pop()

    def process_simple(self, rc_change: int):
        self.cards_dealt += 1
        self.running_count += rc_change
        self.history.insert(0, f"SIMPLE_{rc_change}")
        if len(self.history) > 3: self.history.pop()

    def undo_last(self):
        if not self.history: return
        last_card = self.history.pop(0)
        
        if last_card.startswith("SIMPLE_"):
            rc_change = int(last_card.split('_')[1])
            self.cards_dealt -= 1
            self.running_count -= rc_change
        else:
            self.shoe[last_card] += 1
            self.cards_dealt -= 1
            valor = last_card.split('_')[0]
            self.running_count -= self._get_card_value(valor)

    @property
    def decks_remaining(self) -> float:
        cards_left = self.total_cards - self.cards_dealt
        return cards_left / self.cards_per_deck if cards_left > 0 else 0

    @property
    def true_count(self) -> float:
        return self.running_count / self.decks_remaining if self.decks_remaining > 0 else 0

    def get_stats(self):
        val_counts = {v: 0 for v in self.VALORES_STANDARD} 
        suit_counts = {'Hearts': 0, 'Diamonds': 0, 'Clubs': 0, 'Spades': 0}
        
        for key, count in self.shoe.items():
            val, suit = key.split('_')
            if val in val_counts: val_counts[val] += count
            if suit in suit_counts: suit_counts[suit] += count
            
        total_remaining = self.total_cards - self.cards_dealt
        suit_percs = {s: (c / total_remaining * 100) if total_remaining > 0 else 0 for s, c in suit_counts.items()}
        
        return val_counts, suit_counts, suit_percs