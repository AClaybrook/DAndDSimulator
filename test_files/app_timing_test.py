""" Testing how look it takes to simulate character rounds.
Run the following command with this file selected:
$(pipenv --py) -m cProfile -o ${file}.prof ${file}
"""
from dataclasses import replace
from computations.models import Character, Enemy, Attack
from computations.numerical_simulation import simulate_rounds_from_characters, simulate_rounds_from_characters_multi_acs # pylint: disable=unused-import

# Build attacks
attacksPython = [Attack(name=f"Greatsword{ii+1}", two_handed=True, ability_stat="strength", damage='2d6', type='weapon (melee)') for ii in range(3)]

# Character stats
character1 = Character(name='Fighter',level=12, attacks=attacksPython, strength=20)
character2 = replace(character1, name='Fighter GWF + Crit On 19', disadvantage=False, GWF=True, crit_on=19)
character3 = replace(character1, name='Fighter Advantage', advantage=True)
character4 = replace(character1, name='Fighter GWM + Advantage', GWM=True, advantage=True)
enemy = Enemy(armor_class=18)

characters = [character1, character2, character3, character4]


# Run the following command with this file selected
# "$(pipenv --py) -m cProfile -o ${file}.prof ${file}",
# dfs, df_by_rounds, df_by_attacks = simulate_rounds_from_characters(characters, enemy,num_rounds=100_000, save_memory=True)
# df_acs = simulate_rounds_from_characters_multi_acs(characters, enemy, num_rounds=10_000)
df_acs2 = simulate_rounds_from_characters_multi_acs(characters, enemy, num_rounds=1_000_000, by_round=False)