"""
LLM istemcisi (sadece standart kütüphane).

İki arka uç:
  * ollama : yerel Ollama sunucusu (http://localhost:11434). JSON şeması `format` ile zorlanır.
  * openai : OpenAI uyumlu herhangi bir /v1/chat/completions uç noktası (OpenAI ve uyumlu
             sağlayıcılar, ayrıca Ollama'nın kendi /v1 uç noktası). Anahtar LLM_API_KEY
             ortam değişkeninden okunur.

Yerelden API'ye geçmek için sadece --backend, --model ve gerekirse --base-url değişir.
"""
import json
import os
import re
import time
import urllib.error
import urllib.request


class LLMHatasi(Exception):
    def __init__(self, mesaj, ham=""):
        super().__init__(mesaj)
        self.ham = ham


def json_coz(metin):
    """Model çıktısından JSON nesnesini çıkarır (``` çitlerini ve <think> bloklarını atar)."""
    t = re.sub(r"<think>.*?</think>", "", str(metin), flags=re.S).strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t).strip()
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        bas, son = t.find("{"), t.rfind("}")
        if bas != -1 and son > bas:
            try:
                return json.loads(t[bas:son + 1])
            except json.JSONDecodeError:
                pass
    raise LLMHatasi("model geçerli JSON üretmedi", metin)


class LLMIstemci:
    def __init__(self, backend, model, base_url=None, api_key=None, temperature=0.2,
                 num_ctx=8192, timeout=900, deneme=3):
        if backend not in ("ollama", "openai"):
            raise ValueError("backend 'ollama' ya da 'openai' olmalı")
        self.backend, self.model = backend, model
        self.base_url = (base_url or ("http://localhost:11434" if backend == "ollama"
                                      else "https://api.openai.com/v1")).rstrip("/")
        self.api_key = api_key if api_key is not None else os.environ.get("LLM_API_KEY", "")
        self.temperature, self.num_ctx, self.timeout, self.deneme = temperature, num_ctx, timeout, deneme
        self.sayac = {"cagri": 0, "girdi_token": 0, "cikti_token": 0, "sure_sn": 0.0}

    # ------------------------------------------------------------------
    def _post(self, url, govde, basliklar):
        istek = urllib.request.Request(url, data=json.dumps(govde).encode("utf-8"),
                                       headers={"Content-Type": "application/json", **basliklar})
        son_hata = None
        for i in range(self.deneme):
            try:
                with urllib.request.urlopen(istek, timeout=self.timeout) as r:
                    return json.loads(r.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                govde_metni = e.read().decode("utf-8", "replace")[:500]
                son_hata = LLMHatasi(f"HTTP {e.code}: {govde_metni}")
                if e.code in (400, 401, 403, 404):       # tekrar denemek işe yaramaz
                    raise son_hata
            except (urllib.error.URLError, TimeoutError, ConnectionError, json.JSONDecodeError) as e:
                son_hata = LLMHatasi(f"bağlantı hatası: {e}")
            time.sleep(2 ** i * 3)
        raise son_hata

    def json(self, sistem, kullanici, sema=None):
        """Bir JSON nesnesi döndürür. sema verilirse çıktı o şemaya zorlanır."""
        bas = time.time()
        mesajlar = [{"role": "system", "content": sistem}, {"role": "user", "content": kullanici}]
        if self.backend == "ollama":
            govde = {"model": self.model, "messages": mesajlar, "stream": False,
                     "format": sema if sema else "json",
                     "options": {"temperature": self.temperature, "num_ctx": self.num_ctx}}
            yanit = self._post(self.base_url + "/api/chat", govde, {})
            metin = yanit.get("message", {}).get("content", "")
            gt, ct = yanit.get("prompt_eval_count", 0), yanit.get("eval_count", 0)
        else:
            govde = {"model": self.model, "messages": mesajlar}
            if self.temperature is not None:
                govde["temperature"] = self.temperature
            govde["response_format"] = (
                {"type": "json_schema", "json_schema": {"name": "cikti", "schema": sema, "strict": False}}
                if sema else {"type": "json_object"})
            basliklar = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
            yanit = self._post(self.base_url + "/chat/completions", govde, basliklar)
            try:
                metin = yanit["choices"][0]["message"]["content"] or ""
            except (KeyError, IndexError, TypeError):
                raise LLMHatasi("beklenmeyen API yanıtı", json.dumps(yanit)[:500])
            u = yanit.get("usage") or {}
            gt, ct = u.get("prompt_tokens", 0), u.get("completion_tokens", 0)
        self.sayac["cagri"] += 1
        self.sayac["girdi_token"] += gt or 0
        self.sayac["cikti_token"] += ct or 0
        self.sayac["sure_sn"] += time.time() - bas
        sonuc = json_coz(metin)
        return sonuc, metin
