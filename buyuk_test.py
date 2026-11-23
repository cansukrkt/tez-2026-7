#!/usr/bin/env python3
"""Büyük ölçekli rastgele test: her sistem için 10 farklı tohumla rastgele saldırı ve
girişimsizlik testi. Sonuçları tablo olarak yazdırır."""
import random
import sys

import prototip as p

TOHUMLAR = range(1, 11)
N_FUZZ, N_NI = 2000, 1000


def olc(mode):
    ihlalli, ni_ihlal, toplam_f, toplam_n = 0, 0, 0, 0
    attack_scenarios = [s for s in p.SCENARIOS if s["env_attack"] is not None]
    for seed in TOHUMLAR:
        rng = random.Random(seed)
        for _ in range(N_FUZZ):
            sc = rng.choice(attack_scenarios)
            txt = p.random_text(rng)
            sc2 = dict(sc, env_attack={"emails": {k: txt for k in sc["env_benign"].get("emails", {})},
                                       "web": {k: txt for k in sc["env_benign"].get("web", {})}})
            _, s = p.execute(mode, sc2, True)
            ihlalli += bool(p.violations(s, s.env))
            toplam_f += 1
        for _ in range(N_NI):
            sc = rng.choice(attack_scenarios)
            outs = []
            for txt in (p.random_text(rng), p.random_text(rng)):
                sc2 = dict(sc, env_attack={"emails": {k: txt for k in sc["env_benign"].get("emails", {})},
                                           "web": {k: txt for k in sc["env_benign"].get("web", {})}})
                outs.append(p.trusted_actions(p.execute(mode, sc2, True)[1]))
            ni_ihlal += outs[0] != outs[1]
            toplam_n += 1
    return ihlalli, toplam_f, ni_ihlal, toplam_n


if __name__ == "__main__":
    if len(sys.argv) > 1:
        N_FUZZ = int(sys.argv[1])
    if len(sys.argv) > 2:
        N_NI = int(sys.argv[2])
    print(f"{len(TOHUMLAR)} tohum × {N_FUZZ} rastgele saldırı + {N_NI} girişimsizlik çifti\n")
    print(f"{'Sistem':24s} {'İhlalli vaka':>22s} {'Girişimsizlik ihlali':>24s}")
    for m in p.MODES:
        a, b, c, d = olc(m)
        print(f"{m:24s} {a:>8d} / {b:<6d} ({a / b:5.1%}) {c:>8d} / {d:<6d} ({c / d:5.1%})")
