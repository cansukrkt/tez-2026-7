"""Araç kapısındaki politika kuralları."""
from prototip import (LV, Label, TRUSTED, U, PRIV, Env, check_policy, endorsed,
                      ALLOW, DENY, ASK, PAY_LIMIT)

ENV = Env()
UNT = Label(U, sources=frozenset({"eposta:acme"}))


def para(alici, tutar, alici_lab=TRUSTED, tutar_lab=TRUSTED, pc=TRUSTED, end=None):
    return check_policy("send_money", {"recipient": LV(alici, alici_lab), "amount": LV(tutar, tutar_lab)},
                        pc, ENV, end or {})[0]


def test_dusuk_riskli_her_zaman_izinli():
    assert check_policy("read_web", {"url": LV("x", UNT)}, Label(U), ENV, {})[0] == ALLOW


def test_guvenilir_odeme_izinli():
    assert para("TR11-ACME", 800) == ALLOW


def test_disaridan_gelen_kayitli_alici_izinli():
    assert para("TR11-ACME", 800, alici_lab=UNT, tutar_lab=UNT) == ALLOW


def test_disaridan_gelen_kayitsiz_alici_onaya():
    assert para("TR99-SALDIRGAN", 800, alici_lab=UNT) == ASK


def test_disaridan_gelen_tutar_sinir_ustu_onaya():
    assert para("TR11-ACME", PAY_LIMIT + 1, tutar_lab=UNT) == ASK
    assert para("TR11-ACME", PAY_LIMIT, tutar_lab=UNT) == ALLOW


def test_guvenilmez_karar_onaya():
    assert para("TR11-ACME", 100, pc=UNT) == ASK


def test_odeme_yukseltilemez():
    end = {"send_money": {"eposta:acme"}}
    assert para("TR11-ACME", 100, pc=UNT, end=end) == ASK


def test_gizli_veri_disariya_ret():
    r = check_policy("send_email", {"to": LV("saldirgan@kotu.com", UNT), "body": LV(1, Label(conf=PRIV))},
                     TRUSTED, ENV, {})[0]
    assert r == DENY


def test_gizli_veri_ice_izinli():
    r = check_policy("send_email", {"to": LV("ali@sirket.com"), "body": LV(1, Label(conf=PRIV))},
                     TRUSTED, ENV, {})[0]
    assert r == ALLOW


def test_guvenilmez_govde_guvenilir_aliciya_izinli():
    r = check_policy("send_email", {"to": LV("ali@sirket.com"), "body": LV("x", UNT)}, TRUSTED, ENV, {})[0]
    assert r == ALLOW


def test_genel_kural_yukseltmeyle_acilir():
    args = {"title": LV("Toplantı", Label(U, sources=frozenset({"eposta:patron"})))}
    assert check_policy("add_event", args, TRUSTED, ENV, {})[0] == ASK
    assert check_policy("add_event", args, TRUSTED, ENV, {"add_event": {"eposta:patron"}})[0] == ALLOW


def test_yukseltme_kaynaga_bagli():
    end = {"add_event": {"eposta:patron"}}
    assert endorsed("add_event", frozenset({"eposta:patron"}), end)
    assert not endorsed("add_event", frozenset({"eposta:patron", "web:x"}), end)
    assert not endorsed("add_event", frozenset(), end)
    assert not endorsed("delete_file", frozenset({"eposta:patron"}), {"delete_file": {"eposta:patron"}})
