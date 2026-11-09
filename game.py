import os
import sys
import math
import random


class Gen:
    @staticmethod
    def deck(decks):
        base_deck = ([2, 3, 4, 5, 6, 7, 8, 9] * 4 + [10] * 16 + ["A"] * 4) * decks
        random.shuffle(base_deck)
        return base_deck

    @staticmethod
    def player(player, game_state):
        game_state[player] = []
        card = game_state["deck"].pop()
        game_state[player].append(card)
        card = game_state["deck"].pop()
        game_state[player].append(card)


def calculate_score(hand):
    score = 0
    aces = 0
    for card in hand:
        if card == "A":
            aces += 1
            score += 11
        else:
            score += card
    while score > 21 and aces > 0:
        score -= 10
        aces -= 1
    if score > 21:
        return "lose"
    return score

def hit(player, game_state):
    game_state[player].append(game_state["deck"].pop())

def stand(player, game_state):
    game_state["stood"][player] = 1

if os.name == "nt":
    os.system("")

def get_valid_move():
    move = input("").strip().lower()
    if move in ["h", "s"]:
        return move
    sys.stdout.write("\033[1A\033[K")
    sys.stdout.flush()

    return get_valid_move()

player_count = int(input("How many players: "))


if player_count <= 2:
    decks = 2
elif player_count <= 4:
    decks = 4
elif player_count <= 6:
    decks = 6
else:
    decks = 8
base_deck = Gen.deck(decks)

game_state = {
    "deck": base_deck,
    "stood": []
    }

for player in range(0, 1 + player_count):
    Gen.player(player, game_state)
    game_state["stood"].append(0)

print("A game has been created with:")
print(f" ╰╴{decks} decks")
print(f" ╰╴{player_count} players")
for player in range(0, 1 + player_count):
    print(f"    ╰╴{player} has {game_state[player]} {calculate_score(game_state[player])}")

while True:
    if game_state["stood"] == [1] * (player_count+1):
        print("Round over")
        for player in range(0, 1 + player_count):
            print(f"    ╰╴{player} has {game_state[player]} {calculate_score(game_state[player])}")
        break
    for player in range(1, 1 + player_count):
        print("")
        print(f"Player {player}'s turn.")
        print(f"    ╰╴Currently has {', '.join(map(str, game_state[player]))}  Total: {calculate_score(game_state[player])}")
        print(f"What move does player {player} want to take?")
        print(f"    ╰╴Hit    H")
        print(f"    ╰╴Stand  S")
        move = get_valid_move()
        if move == "h":
            hit(player, game_state)
            if calculate_score(game_state[player]) == "lose":
                print(f"Lose. {game_state[player]} {calculate_score(game_state[player])}")
                stand(player, game_state)
            else:
                print(f"Player {player} now has {game_state[player]} {calculate_score(game_state[player])}")
        elif move == "s":
            stand(player, game_state)
            print(f"Player {player} has stood with {game_state[player]} {calculate_score(game_state[player])}")
        if game_state["stood"][player] == 1:
            continue
    if player == 0:
         # pick the dealer's move
        if calculate_score(game_state[player]) < 16:
            hit(player, game_state)
            if calculate_score(game_state[player]) == "lose":
                print(f"Lose. {game_state[player]} {calculate_score(game_state[player])}")
                stand(player, game_state)
            else:
                print(f"Dealer now has {game_state[player]} {calculate_score(game_state[player])}")
        else:
            stand(player, game_state)
            print(f"Dealer has stood with {game_state[player]} {calculate_score(game_state[player])}")

