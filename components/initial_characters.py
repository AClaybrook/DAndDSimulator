""" Initializes characters for the app """
from dataclasses import replace
from computations.models import Character, Enemy, Attack

def initialize_characters():
    """ Function to initializes characters for the app """
    # Build attacks
    attacks_python = [Attack(name="Greatsword", two_handed=True, ability_stat="strength", damage='2d6', type='weapon (melee)') for _ in range(3)]

    # Character stats
    character1 = Character(name='Fighter',level=12, attacks=attacks_python, strength=20)
    character2 = replace(character1, name='Fighter GWF + Crit On 19', disadvantage=False, GWF=True, crit_on=19)
    character3 = replace(character1, name='Fighter Advantage', advantage=True)
    character4 = replace(character1, name='Fighter GWM + Advantage', GWM=True, advantage=True)
    enemy = Enemy(armor_class=18)

    characters = [character1, character2, character3, character4]

    return characters, enemy
