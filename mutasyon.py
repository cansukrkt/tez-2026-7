#!/usr/bin/env python3
"""Mutasyon testi: güvenlik kurallarını tek tek bilerek bozar ve güvenlik bataryasının
bu bozulmayı yakalayıp yakalamadığını kontrol eder.

'Öldürüldü'  = test bataryası bozulmayı yakaladı (iyi).
'Hayatta'    = bozulma fark edilmedi. Ya kural başka bir kuralla örtüşüyor (savunma derinliği)
               ya da testlerde bu kuralı tek başına sınayan bir senaryo eksik.
"""
import contextlib

import prototip as p

KURAL_MUTANTLARI = {
    "pc_kontrolu_yok": "Güvenilmez karara bağlı eylem kontrolü kaldırıldı",
    "alici_kontrolu_yok": "Ödemede kayıtlı alıcı kontrolü kaldırıldı",
    "tutar_siniri_yok": "Dışarıdan gelen tutar sınırı kaldırıldı",
    "gizlilik_kontrolu_yok": "Gizli verinin dışarı gitme kontrolü kaldırıldı",
    "eposta_alici_kontrolu_yok": "E-postada dışarıdan gelen alıcı kontrolü kaldırıldı",
    "genel_arguman_kontrolu_yok": "Orta/yüksek riskli araçta genel argüman kontrolü kaldırıldı",
    "sabit_tavan_yok": "Sabit üst tavan (ödeme/silme yükseltilemez) kaldırıldı",
    "yukseltme_kapsami_yok": "Yükseltmenin kaynak kontrolü kaldırıldı",
    "cevirmen_temizler": "Çevirmen modelin çıktısı etiket taşımıyor",
}
MOD_MUTANTLARI = {
    "protocol": "Talimat/veri kanalı ayrımı kaldırıldı",
    "pc_cross": "pc ajan sınırında sıfırlanıyor",
    "static_branch": "Statik dal analizi kaldırıldı",
    "attenuation": "Yetki daraltma kaldırıldı",
}


@contextlib.contextmanager
def kural_mutanti(ad):
    p._MUTANTS.add(ad)
    try:
        yield
    finally:
        p._MUTANTS.discard(ad)


@contextlib.contextmanager
def mod_mutanti(bayrak):
    eski = p.MODES["Bizim"][bayrak]
    p.MODES["Bizim"][bayrak] = False
    try:
        yield
    finally:
        p.MODES["Bizim"][bayrak] = eski


def tum_mutantlar():
    for ad, aciklama in KURAL_MUTANTLARI.items():
        yield ad, aciklama, kural_mutanti(ad)
    for bayrak, aciklama in MOD_MUTANTLARI.items():
        yield bayrak, aciklama, mod_mutanti(bayrak)


def calistir(n_fuzz=400, n_ni=300, seed=3):
    sonuc = []
    assert p.guvenlik_bataryasi("Bizim", n_fuzz, n_ni, seed) == [], "Bozulmamış sistem bataryayı geçmeli"
    for ad, aciklama, ctx in tum_mutantlar():
        with ctx:
            sorunlar = p.guvenlik_bataryasi("Bizim", n_fuzz, n_ni, seed)
        sonuc.append((ad, aciklama, sorunlar))
    return sonuc


if __name__ == "__main__":
    sonuc = calistir()
    olu = sum(1 for _, _, s in sonuc if s)
    print(f"Mutasyon testi: {olu}/{len(sonuc)} mutant öldürüldü\n")
    for ad, aciklama, sorunlar in sonuc:
        durum = "ÖLDÜRÜLDÜ" if sorunlar else "HAYATTA  "
        ornek = sorted({s.split(":")[0] for s in sorunlar})[:4]
        print(f"  {durum}  {aciklama}")
        if sorunlar:
            print(f"             yakalayan: {', '.join(ornek)}")
