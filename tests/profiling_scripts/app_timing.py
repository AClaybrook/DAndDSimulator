""" Testing how look it takes to simulate character rounds.
Run the following command with this file selected:
$(pipenv --py) -m cProfile -o ${file}.prof ${file}
"""
from dataclasses import replace
from computations.models import Character, Enemy, Attack
from computations.numerical_simulation import simulate_rounds_from_characters, simulate_rounds_from_characters_multi_acs # pylint: disable=unused-import
from components.initial_characters import initialize_characters

characters, enemy = initialize_characters()


# Run the following command with this file selected
# "$(pipenv --py) -m cProfile -o ${file}.prof ${file}",
# dfs, df_by_rounds, df_by_attacks = simulate_rounds_from_characters(characters, enemy,num_rounds=100_000, save_memory=True)
# df_acs = simulate_rounds_from_characters_multi_acs(characters, enemy, num_rounds=10_000)
df_acs2 = simulate_rounds_from_characters_multi_acs(characters, enemy, num_rounds=1_000_000, by_round=False)