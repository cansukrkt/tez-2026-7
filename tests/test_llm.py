"""LLM boru hattı testleri (gerçek model gerektirmez)."""
import json
import re
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

import llm_deney as d
import prototip as p
from llm_istemci import LLMIstemci, json_coz


@pytest.mark.parametrize("sc", p.SCENARIOS, ids=lambda s: s["id"])
def test_sahte_plan_prototiple_ayni_sonucu_verir(sc):
    k = d.bir_tekrar(sc, None, sahte=True)
    assert k["plan_gecerli"], k["plan_hatalari"]
    bek = d.beklenen(sc)
    for m in d.MODLAR:
        assert k["sonuclar"][m]["mesru"] == bek[m]["mesru"]
        assert k["sonuclar"][m].get("saldiri") == bek[m]["saldiri"]


KAT = d.katalog(p.SCENARIOS[1])


def test_katalog_disi_mesaj_reddedilir():
    _, _, h = d.dogrula([{"op": "call", "to": "finans", "msg": "TR99 hesabına öde", "vars": {}}], KAT)
    assert any("kataloğunda olmayan" in x for x in h)


def test_ulasilamayan_ajan_reddedilir():
    sc = next(s for s in p.SCENARIOS if s["id"] == "Z3")
    _, _, h = d.dogrula([{"op": "call", "to": "finans", "msg": "Bakiyeyi getir.", "vars": {}, "out": "b"}], d.katalog(sc))
    assert any("ulaşılamayan" in x for x in h)


def test_tanimsiz_degisken_ve_kotu_sema():
    _, _, h = d.dogrula([
        {"op": "qllm", "inputs": [{"var": "yok"}], "prompt": "x", "schema": {"type": "string"}, "out": "a"}], KAT)
    assert any("tanımsız" in x for x in h)
    assert any("şeması" in x for x in h)


def test_neq_ve_tur_hatasi():
    sc = p.SCENARIOS[0]
    plan = [{"op": "set", "var": "a", "value": {"lit": "x"}},
            {"op": "if", "cond": {"gt": [{"var": "a", "path": []}, {"lit": 3}]}, "then": []}]
    _, s = d.calistir("Bizim", sc, False, plan, {})
    assert any("tür hatası" in b[3] for b in s.blocked)
    s2 = d.LLMSystem("Bizim", p.Env(), sc)
    assert s2.ev({"neq": [{"lit": 1}, {"lit": 2}]}, {}).value is True


def test_json_coz():
    assert json_coz('```json\n{"a": 1}\n```') == {"a": 1}
    assert json_coz('<think>hmm</think> sonuç: {"a": 2}') == {"a": 2}


def test_sema_duzelt():
    s = d.sema_duzelt({"type": "object", "properties": {"x": {"type": "array", "items": {"type": "object",
                       "properties": {"y": {"type": "integer"}}}}}})
    assert s["required"] == ["x"] and s["additionalProperties"] is False
    assert s["properties"]["x"]["items"]["required"] == ["y"]


# --- sahte HTTP sunucusu: gerçek istemci kodunu uçtan uca sınar ---------------------------
PLAN_S2 = {"steps": [
    {"op": "call", "to": "eposta", "msg": "Verilen kişiden gelen e-postayı oku.", "vars": {"kimden": {"lit": "acme"}}, "out": "e"},
    {"op": "qllm", "inputs": [{"var": "e"}], "prompt": "Faturadaki tutarı ve IBAN'ı çıkar.",
     "schema": {"type": "object", "properties": {"tutar": {"type": "integer"}, "iban": {"type": "string"}}}, "out": "f"},
    {"op": "call", "to": "finans", "msg": "Verilen alıcıya verilen tutarı öde.",
     "vars": {"alici": {"var": "f", "path": ["iban"]}, "tutar": {"var": "f", "path": ["tutar"]}}}]}


class Sahte(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        govde = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        sistem = govde["messages"][0]["content"]
        if sistem == d.PLANCI_SISTEM:
            icerik = "```json\n" + json.dumps(PLAN_S2, ensure_ascii=False) + "\n```"
        else:
            girdi = json.loads(govde["messages"][1]["content"])["inputs"][0]
            t, i = re.search(r"Tutar: (\d+)", girdi), re.search(r"IBAN (\S+)", girdi)
            icerik = json.dumps({"tutar": int(t.group(1)), "iban": i.group(1)})
            assert (govde.get("format") or govde["response_format"]["json_schema"]["schema"])["required"]
        if self.path == "/api/chat":
            yanit = {"message": {"content": icerik}, "prompt_eval_count": 10, "eval_count": 5}
        else:
            yanit = {"choices": [{"message": {"content": icerik}}], "usage": {"prompt_tokens": 10, "completion_tokens": 5}}
        veri = json.dumps(yanit).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(veri)))
        self.end_headers()
        self.wfile.write(veri)


@pytest.fixture(scope="module")
def sunucu():
    srv = HTTPServer(("127.0.0.1", 0), Sahte)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_port}"
    srv.shutdown()


@pytest.mark.parametrize("backend,yol", [("ollama", ""), ("openai", "/v1")])
def test_istemci_uctan_uca(sunucu, backend, yol):
    ist = LLMIstemci(backend, "deneme", base_url=sunucu + yol, api_key="x")
    sc = next(s for s in p.SCENARIOS if s["id"] == "S2")
    k = d.bir_tekrar(sc, ist)
    assert k["plan_gecerli"], k["plan_hatalari"]
    assert k["sonuclar"]["Bizim"]["mesru"] == "tamam"
    assert k["sonuclar"]["Bizim"]["saldiri"] == "onay"
    assert k["sonuclar"]["Multi-CaMeL"]["saldiri"] == "gecti"
    assert k["llm"]["cagri"] == 3          # 1 plancı + meşru ve saldırı için birer çevirmen (önbellekli)
