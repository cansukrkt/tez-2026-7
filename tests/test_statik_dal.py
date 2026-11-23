"""Statik dal analizi: alınmayan dal da bilgi taşır."""
from prototip import System, Env, LV, Label, TRUSTED, U, L, V, QLLM, writes, ALL_TOOLS

UNT = Label(U, sources=frozenset({"web:x"}))


def calistir(mode, plan, env_vars):
    s = System(mode, Env(), {"qllm": QLLM})
    s.run("orkestrator", plan, env_vars, TRUSTED, set(ALL_TOOLS))
    return env_vars


def test_writes_ic_ice():
    plan = [{"op": "if", "cond": L(True), "then": [
        {"op": "set", "var": "a", "value": L(1)},
        {"op": "if", "cond": L(True), "then": [{"op": "set", "var": "b", "value": L(1)}]}],
        "else": [{"op": "set", "var": "c", "value": L(1)}]},
        {"op": "for", "in": L([]), "item": "x", "body": [{"op": "set", "var": "d", "value": L(1)}]}]
    assert writes(plan) == {"a", "b", "c", "d", "x"}


def test_alinmayan_dal_etiketlenir():
    plan = [{"op": "set", "var": "f", "value": L(True)},
            {"op": "if", "cond": V("k"), "then": [{"op": "set", "var": "f", "value": L(False)}]}]
    statik = calistir("Bizim", plan, {"k": LV(False, UNT)})
    dinamik = calistir("Bizim (dinamik pc)", plan, {"k": LV(False, UNT)})
    assert statik["f"].value is True and statik["f"].label.integ == U
    assert dinamik["f"].value is True and dinamik["f"].label.integ != U   # eski sürümdeki açık


def test_hic_calismayan_dongu_etiketlenir():
    plan = [{"op": "set", "var": "f", "value": L(True)},
            {"op": "for", "in": V("liste"), "item": "x", "body": [{"op": "set", "var": "f", "value": L(False)}]}]
    out = calistir("Bizim", plan, {"liste": LV([], UNT)})
    assert out["f"].value is True and out["f"].label.integ == U


def test_guvenilir_kosul_etiketlemez():
    plan = [{"op": "set", "var": "f", "value": L(True)},
            {"op": "if", "cond": L(False), "then": [{"op": "set", "var": "f", "value": L(False)}]}]
    out = calistir("Bizim", plan, {})
    assert out["f"].label == TRUSTED
