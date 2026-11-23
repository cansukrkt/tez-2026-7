"""Etiket birleştirme kuralları: bir damla güvenilmez -> güvenilmez, bir damla gizli -> gizli."""
import itertools

from prototip import Label, TRUSTED, T, U, PUB, PRIV

TUM = [Label(i, c, s) for i in (T, U) for c in (PUB, PRIV)
       for s in (frozenset(), frozenset({"web:x"}), frozenset({"eposta:y"}))]


def test_guvenilmez_bulasir():
    assert TRUSTED.join(Label(U)).integ == U
    assert Label(U).join(TRUSTED).integ == U


def test_gizli_bulasir():
    assert TRUSTED.join(Label(conf=PRIV)).conf == PRIV


def test_kaynaklar_birlesir():
    a = Label(U, sources=frozenset({"web:a"}))
    b = Label(U, sources=frozenset({"eposta:b"}))
    assert a.join(b).sources == {"web:a", "eposta:b"}


def test_notr_eleman():
    for x in TUM:
        assert TRUSTED.join(x) == x


def test_degisme_birlesme_tekrar():
    for a, b in itertools.product(TUM, TUM):
        assert a.join(b) == b.join(a)
        assert a.join(a) == a
    for a, b, c in itertools.product(TUM, TUM, TUM):
        assert a.join(b).join(c) == a.join(b.join(c))


def test_monotonluk():
    # Birleştirme hiçbir zaman güvenilirliği artırmaz, gizliliği azaltmaz.
    for a, b in itertools.product(TUM, TUM):
        j = a.join(b)
        if U in (a.integ, b.integ):
            assert j.integ == U
        if PRIV in (a.conf, b.conf):
            assert j.conf == PRIV
