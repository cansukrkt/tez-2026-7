# Çok Ajanlı LLM Sistemlerinde Yetki Ayrımı — LLM'siz Prototip

Bu depo, "Privilege Separation for Multi-Agent LLM Systems" yüksek lisans tezi için
hazırlanan mimarinin **güvenlik mantığını** test eden bir prototiptir.

> **Önemli:** `prototip.py` değerlendirmenin 1. aşamasıdır ve hiçbir gerçek LLM çağırmaz.
> Gerçek LLM ile küçük deneme için aşağıdaki "Aşama 2" bölümüne bak.
> LLM'lerin davranışı en kötü durum varsayımlarıyla taklit edilir. Sonuçlar **güvenlik
> mantığı** hakkında bilgi verir; gerçek görevlerdeki **fayda kaybı** hakkında bilgi vermez.

## Problem

Çok ajanlı bir sistemde, bir ajanın okuduğu güvenilmez veri (web sayfası, e-posta) başka bir
ajana talimat olarak aktarılabilir (**aklama**), ya da başka bir ajanın eylemini tetikleyen bir
karara dönüşebilir (**ajanlar arası dal yönlendirme**). Her ajanı tek başına korumak bunu engellemez.

## Mimari

| Katman | Ne yapar | Dayandığı çalışma |
|---|---|---|
| Ajan içi ayrım | Patron model dış içeriği görmez; çevirmen model dış içeriği okur ama araç çağıramaz | Dual LLM, CaMeL, SPA |
| Talimat/veri kanalı | Ajanlar arası mesajın talimat kısmına güvenilmez veri giremez | multi-CaMeL |
| Etiketler | Her değer güvenilirlik ve gizlilik etiketi taşır; çevirmen etiketi temizleyemez | Denning, Bell–LaPadula, Biba, SPA |
| **Ajanlar arası pc** | Güvenilmez veriye bağlı bir karar, başka ajanlara geçerken de etiketini korur | Denning, LLMbda (tek program içinde) |
| **Statik dal analizi** | Alınmayan dal da etiket bırakır | Denning, LLMbda |
| Değer politikaları | Kayıtlı alıcılar, tutar sınırı, gizli verinin dışarı çıkışı | CaMeL, Progent |
| **Yetki daraltma** | Ajana sadece görev için gereken ve topolojide ulaşabildiği araçların yetkisi devredilir | Klasik yetki sistemleri |
| **Tavanlı yükseltme** | Güvenilmez bir kaynağın talimat vermesi sadece kullanıcı isteğinden türetilen kapsamda ve sabit üst tavanın altında mümkün | LLMbda'nın açık bıraktığı soru |

Kalın satırlar tezin özgün katkısının bulunduğu yerlerdir.

## Karşılaştırılan sistemler

| Sistem | Açıklama |
|---|---|
| Savunmasız | Patron her metni okur ve içindeki talimatlara uyar |
| Bireysel CaMeL | Her ajan kendi içinde korunur; mesaj metnine veri gömülebilir |
| Multi-CaMeL | Talimat/veri kanalı ayrı; politika yok (makaledeki deney düzeni) |
| Multi-CaMeL+Politika | Multi-CaMeL + bizim değer politikalarımız (adil karşılaştırma) |
| Bizim (dinamik pc) | Önceki sürüm: pc sadece çalışan dalda izlenir |
| Bizim (yükseltmesiz) | Tam sistem, yükseltme kapalı |
| Bizim | Tam sistem |

## Kurulum ve çalıştırma

Python 3.10 veya üstü gerekir.

```bash
pip install -r requirements.txt

python prototip.py      # senaryo tablosu, rastgele testler, hasar yarıçapı
python -m pytest -q     # tüm testler
python mutasyon.py      # mutasyon testi
python buyuk_test.py    # büyük ölçekli rastgele test (10 tohum)
```

## Aşama 2: Gerçek LLM ile küçük deneme

`llm_deney.py`, orkestratörün plancısını ve karantinadaki çevirmen modeli gerçek bir LLM'e bağlar.
Hub, etiketler, pc, statik dal analizi, politikalar, yetki daraltma ve yükseltme `prototip.py`'deki
kodun aynısıdır. Alt ajanların patronları hâlâ sabit planları kullanır (plancı mesajı katalogdan
birebir seçmek zorunda); onları da LLM'e bağlamak sonraki adımdır.

Plancı hiçbir dış içerik görmediği için aynı plan meşru ve saldırı ortamında, ve beş sistem modunda
(Multi-CaMeL, Multi-CaMeL+Politika, Bizim (dinamik pc), Bizim (yükseltmesiz), Bizim) aynen kullanılır.
Modlar arasındaki fark yalnızca güvenlik mekanizmasından gelir. Plancı tek atış çalışır: geçersiz
plan düzeltilmez, "geçersiz" olarak sayılır.

**Ölçülenler:** geçerli plan oranı, meşru görevde tamam / onaya düştü / başarısız, saldırıda
geçti / onaya düştü / durdu, ve her senaryo için LLM'siz prototipin sonucuyla karşılaştırma.

### Yerel model (Ollama)

1. https://ollama.com adresinden Ollama'yı kur.
2. 8 GB VRAM için 7–8B, 4-bit bir model indir (ör. `ollama pull qwen2.5:7b`).
3. Önce tek senaryoyla dene, sonra geceye bırak:

```bash
python llm_deney.py --backend ollama --model qwen2.5:7b --tekrar 1 --senaryo S1,S2
python llm_deney.py --backend ollama --model qwen2.5:7b --tekrar 5
```

17 senaryo × 5 tekrar = 85 kayıt; her kayıt yaklaşık 3–6 LLM çağrısıdır. Süre ekran kartına ve
modele bağlıdır; ilerleme satırı kalan süreyi tahmin eder. Sonuçlar
`sonuclar_llm/<model>.jsonl` dosyasına **her kayıttan sonra** yazılır; program durursa aynı
komut kaldığı yerden devam eder. Bilgisayarın uyku moduna geçmemesi gerekir (ekran kilidi sorun değil).

### API (OpenAI uyumlu)

```bash
export LLM_API_KEY=...          # Windows PowerShell: $env:LLM_API_KEY="..."
python llm_deney.py --backend openai --model <model-adı> --tekrar 5
python llm_deney.py --backend openai --base-url <sağlayıcının /v1 adresi> --model <model-adı>
```

Bazı akıl yürütme modelleri `temperature` kabul etmez; hata alırsan kodda `temperature=None` yap.

### Diğer

```bash
python llm_deney.py --backend sahte --tekrar 1    # LLM'siz boru hattı testi (prototiple aynı sonucu vermeli)
python llm_deney.py --ozet sonuclar_llm/qwen2.5_7b.jsonl
python llm_deney.py --planlar sonuclar_llm/qwen2.5_7b.jsonl --senaryo S1   # ham planlar, hatalar, engeller
```

JSONL kayıtlarında ham plan, doğrulama hataları, çevirmen girdileri/çıktıları ve her moddaki
engelleme gerekçeleri bulunur; tek tek inceleyebilirsin.

**Yorum uyarısı:** Küçük yerel modelle çıkan sonuçlar düzeneği sınamak içindir. Geçersiz planlar
büyük olasılıkla modelin zayıflığından kaynaklanır, mimariden değil. Tez için fayda sayıları
güçlü bir modelle (API) ve ideal olarak AgentDojo uyarlamasıyla alınmalıdır.

## Dosyalar

| Dosya | İçerik |
|---|---|
| `prototip.py` | Etiketler, araçlar, politikalar, hub, yorumlayıcı, senaryolar, rastgele ve girişimsizlik testleri, hasar yarıçapı |
| `mutasyon.py` | Güvenlik kurallarını tek tek bozup testlerin yakalayıp yakalamadığını kontrol eder |
| `buyuk_test.py` | 10 tohumla büyük ölçekli rastgele test |
| `llm_istemci.py` | Ollama ve OpenAI uyumlu API istemcisi (sadece standart kütüphane) |
| `llm_deney.py` | Gerçek LLM ile deney: plancı istemi, katalog, plan doğrulama, çalıştırma, özet |
| `tests/` | pytest testleri (birim, senaryo matrisi, rastgele, mutasyon) |
| `sonuclar.txt`, `mutasyon_sonuclari.txt`, `buyuk_sonuclar.txt` | Son çalıştırmanın çıktıları |

## Senaryolar

| Kod | Senaryo | Neyi test eder |
|---|---|---|
| S1 | Klasik talimat aklama | Talimat/veri kanalı |
| S2 | Sahte IBAN | Değer politikası (kayıtlı alıcı) |
| S3 | Yeni tedarikçi (meşru) | Değer politikasının fayda bedeli |
| S4 | Sahte ev sahibi isteği | Ajanlar arası dal yönlendirme |
| S5 | Sahte muhasebe adresi | Gizli veri sızdırma |
| S6 | Patronun takvim istekleri | Yükseltme; tavan içi saldırı (belgelenmiş sınırlama) |
| S7 | "İstekleri uygula" | Tavan dışı yükseltme girişimi |
| S8 | İtiraz e-postası silinmiş | Alınmayan dal sızıntısı |
| Z1 | İç içe dallar | Alınmayan iç dal |
| Z2 | Boş liste | Gövdesi hiç çalışmayan döngü |
| Z3 | orkestratör → web → finans | İki atlamalı dal yönlendirme |
| Z4 | E-postadaki linkten gelen istekler | Yükseltmenin dolaylı kaynağa sızmaması |
| Z5 | Ele geçirilmiş web ajanı | Yetki daraltma (çalışma anında) |
| Z6 | Gizli veriye bağlı karar | Gizlilik + dışarıdan gelen alıcı |
| Z7 | Tutar şişirme | Tutar sınırı |
| Z8 | Yükseltilmiş alıcıya gizli veri | Yükseltmenin gizliliği delmemesi |
| Z9 | Dallanmasız güvenilmez argüman | Genel argüman kuralı |

## Değerlendirme yöntemleri

1. **Senaryo matrisi:** 17 senaryo × 7 sistem, meşru görev ve saldırı durumunda.
2. **Rastgele saldırı testi:** Saldırgan dış içeriği rastgele parçalardan oluşturur; değer
   temelli ihlaller (kayıtlı olmayan hesaba ödeme, gizli veri sızıntısı vb.) sayılır.
3. **Girişimsizlik (noninterference) testi:** Aynı görev iki farklı saldırgan içeriğiyle
   çalıştırılır. Sistemin "tamamen güvenilir" saydığı eylemler değişiyorsa, sistem saldırganın
   etkilediği bir şeyi güvenilir sanmıştır.
4. **Mutasyon testi:** Her güvenlik kuralı tek tek bozulur; testlerin bunu yakalaması gerekir.
5. **Hasar yarıçapı:** Bir ajan tamamen ele geçirilirse ulaşılabilen riskli araçlar (statik).

## Sonuçlar (son çalıştırma)

**Büyük ölçekli test** (10 tohum × 2000 rastgele saldırı + 1000 girişimsizlik çifti):

| Sistem | İhlalli vaka | Girişimsizlik ihlali |
|---|---|---|
| Savunmasız | %42,2 | %48,6 |
| Bireysel CaMeL | %28,1 | %22,2 |
| Multi-CaMeL | %34,7 | %9,5 |
| Multi-CaMeL+Politika | %9,8 | %9,5 |
| Bizim (dinamik pc) | %0,0 | %6,9 |
| Bizim (yükseltmesiz) | %0,0 | %0,0 |
| **Bizim** | **%0,0** | **%0,0** |

**Mutasyon testi:** 13/13 mutant öldürüldü.

**Hasar yarıçapı** (bir ajan ele geçirildiğinde ulaşılabilen riskli araçların ortalama oranı):
daraltmasız eşler arası sistem %67, ağaç yapısı (multi-CaMeL) %33, bizim yetki daraltmamız %13.

**Testler:** 141 test.

### Öne çıkan bulgular

- Multi-CaMeL'e değer politikaları eklense bile kalan açıkların tamamı dal yönlendirme
  kaynaklıdır (S4, S7, S8, Z1–Z3). Bunları ajanlar arası pc ve statik dal analizi kapatır.
- Değer temelli rastgele test, eski dinamik sürümdeki alınmayan dal açığını **göremez**;
  açığı yalnızca girişimsizlik testi yakalar. Bu yüzden değerlendirmede girişimsizlik testi
  kullanılmalıdır.
- Mutasyon testi ilk çalıştırmada 3 kuralın (tutar sınırı, gizlilik, genel argüman kuralı) hiçbir
  senaryo tarafından tek başına sınanmadığını gösterdi; Z7–Z9 bu yüzden eklendi.

## Bilinen sınırlamalar

- **LLM yok.** Patron ve çevirmen modeller en kötü durum varsayımlarıyla taklit edilir.
  Fayda ölçümü için gerçek LLM'li 2. aşama gereklidir.
- **Fayda bedeli.** S3, S4, Z3 ve Z9'da meşru görevler de kullanıcı onayına düşer. Sahte ve
  gerçek istek metin olarak ayırt edilemediğinde sistem ikisini de onaya gönderir.
- **Tavan içi saldırılar** (S6) engellenmez; bu tasarımın kabul ettiği bir sınırdır.
- Etiketler değişken düzeyindedir, alan düzeyinde değildir.
- Savunmasız ve Bireysel CaMeL için rastgele test sayıları basit metin ayrıştırıcıdan etkilenir;
  anlamlı karşılaştırma Multi-CaMeL, Multi-CaMeL+Politika ve Bizim arasındadır.
- Z3 ve Z5'te eşler arası topoloji kullanılır; gerçek multi-CaMeL yalnızca ağaç topolojisini destekler.
- Biçimsel bir güvenlik kanıtı yoktur; testler deneyseldir.

## İlgili çalışmalar

- Debenedetti ve ark., *Defeating Prompt Injections by Design* (CaMeL), 2025.
- Peters-Gill ve ark., *Can CaMeLs Talk? Securing Multi-Agent Systems Against Indirect Prompt Injection Attacks* (multi-CaMeL), arXiv:2610.05640, 2026.
- Garby, Gordon ve Sands, *The LLMbda Calculus: AI Agents, Conversations, and Information Flow*, arXiv:2602.20064, 2026.
- Wu ve ark., *IsolateGPT: An Execution Isolation Architecture for LLM-Based Agentic Systems*, NDSS 2025.
- Ji ve ark., *Taming Various Privilege Escalation in LLM-Based Agent Systems: A Mandatory Access Control Framework* (SEAgent), arXiv:2601.11893, 2026.
- Costa ve ark., *Securing AI Agents with Information-Flow Control* (FIDES), 2025.
- Shi ve ark., *Progent: Programmable Privilege Control for LLM Agents*, 2025.
- Denning, *A Lattice Model of Secure Information Flow*, CACM 1976.
- Debenedetti ve ark., *AgentDojo*, NeurIPS 2024.
