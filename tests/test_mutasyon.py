"""Her güvenlik kuralı bilerek bozulduğunda, test bataryası bunu yakalamalı."""
import pytest

import mutasyon
import prototip as p

MUTANTLAR = list(mutasyon.KURAL_MUTANTLARI) + list(mutasyon.MOD_MUTANTLARI)


@pytest.mark.parametrize("ad", MUTANTLAR)
def test_mutant_olduruldu(ad):
    ctx = mutasyon.kural_mutanti(ad) if ad in mutasyon.KURAL_MUTANTLARI else mutasyon.mod_mutanti(ad)
    with ctx:
        sorunlar = p.guvenlik_bataryasi("Bizim", n_fuzz=300, n_ni=200, seed=3)
    assert sorunlar, f"'{ad}' mutantı fark edilmedi"


def test_mutantlar_temizlendi():
    assert p._MUTANTS == set()
    assert all(p.MODES["Bizim"][k] for k in mutasyon.MOD_MUTANTLARI)
