"""Rastgele saldırı ve girişimsizlik testleri, birden fazla tohumla."""
import pytest

import prototip as p


@pytest.mark.parametrize("seed", [1, 2, 3, 4, 5])
def test_bizim_ihlalsiz(seed):
    assert p.guvenlik_bataryasi("Bizim", n_fuzz=400, n_ni=200, seed=seed) == []


@pytest.mark.parametrize("seed", [1, 2])
def test_yukseltmesiz_ihlalsiz(seed):
    assert p.guvenlik_bataryasi("Bizim (yükseltmesiz)", n_fuzz=300, n_ni=150, seed=seed) == []


@pytest.mark.parametrize("mode", ["Multi-CaMeL", "Multi-CaMeL+Politika", "Bizim (dinamik pc)"])
def test_karsilastirma_sistemleri_aciklari_gosterir(mode):
    # Testin gerçekten bir şey ölçtüğünü doğrular: zayıf sistemlerde sorun bulunmalı.
    assert p.guvenlik_bataryasi(mode, n_fuzz=300, n_ni=150, seed=1) != []


def test_dinamik_pc_acigi_sadece_girisimsizlik_testinde_gorunur():
    # Eski dinamik sürümde değer temelli ihlal ölçümü açığı göremez, girişimsizlik testi görür.
    sorunlar = p.guvenlik_bataryasi("Bizim (dinamik pc)", n_fuzz=300, n_ni=300, seed=1)
    assert any(s.startswith("girişimsizlik/") for s in sorunlar)
    assert not any(s.startswith("rastgele/") for s in sorunlar)
