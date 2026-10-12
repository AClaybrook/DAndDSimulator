""" Simulation speed benchmark. Run from the repo root: python -m benchmarks.benchmark
    Speed matters, check this before and after changing computations/ """
import time, statistics, sys, io, contextlib
from dataclasses import replace
from computations.models import Character, Enemy, Attack
from computations import numerical_simulation as ns
attacks = [Attack(name="Greatsword", two_handed=True, ability_stat="strength", damage='2d6', type='weapon (melee)') for _ in range(3)]
c1 = Character(name='Fighter', level=12, attacks=attacks, strength=20)
chars = [c1, replace(c1, name='GWF', GWF=True, crit_on=19), replace(c1, name='Adv', advantage=True),
         replace(c1, name='GWM', GWM=True, advantage=True, bonus_damage_die_mod_list=['1d6'], savage_attacker=True)]
enemy = Enemy(armor_class=18)
def t(label, f, n=5):
    times = []
    for _ in range(n):
        with contextlib.redirect_stdout(io.StringIO()):
            s = time.perf_counter(); f(); times.append(time.perf_counter() - s)
    print(f"{label:38s} median {statistics.median(times)*1000:8.1f} ms")
rng = ns.set_seed(1)
t("DPR 10k rounds", lambda: ns.simulate_rounds_from_characters(chars, enemy, num_rounds=10_000, save_memory=True, rng=rng))
t("DPR 100k rounds", lambda: ns.simulate_rounds_from_characters(chars, enemy, num_rounds=100_000, save_memory=True, rng=rng))
t("DPR 1M rounds", lambda: ns.simulate_rounds_from_characters(chars, enemy, num_rounds=1_000_000, save_memory=True, rng=rng), n=3)
t("DPR vs AC 10k (16 ACs)", lambda: ns.simulate_rounds_from_characters_multi_acs(chars, enemy, num_rounds=10_000, rng=rng))
t("DPA vs AC 10k (16 ACs)", lambda: ns.simulate_rounds_from_characters_multi_acs(chars, enemy, num_rounds=10_000, by_round=False, rng=rng))
t("DPR vs AC 100k (16 ACs)", lambda: ns.simulate_rounds_from_characters_multi_acs(chars, enemy, num_rounds=100_000, rng=rng), n=3)
