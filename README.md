# deckopt: Valve Steam Deck için YZ Destekli Otonom Oyun Optimizasyon Motoru (Alfa v0.1.0)

Valve Steam Deck donanımları (LCD "Jupiter" ve OLED "Galileo") ile SteamOS 3.x çalışma zamanı için özel olarak geliştirilmiş, hibrit yapay zeka destekli yerleşik oyun optimizasyon motoru ve yönetim arayüzüdür.

Bu yazılım yalnızca Valve Steam Deck donanımı üzerinde çalışacak şekilde platform kilidine sahiptir. Farklı bir sistemde çalıştırıldığında DMI/BIOS seviyesinde devreye giren donanım kilidi sayesinde yürütmeyi güvenle durdurur.

---

## 1. Mimari Genel Bakış

deckopt, kullanıcıların oyun bazında saatlerce TDP, GPU frekansı, FSR ölçekleme ve başlatma parametresi denemesi yapma zorunluluğunu ortadan kaldırır. 

```
+-------------------------------------------------------------------------+
|                  Valve Steam Deck (SteamOS 3.x / Gamescope)              |
+-------------------------------------------------------------------------+
       |                                                    |
       v                                                    v
 [Dahili NVMe / MicroSD]                            [DMI BIOS Kontrolü]
 Appmanifest ACF Taraması                        (Jupiter LCD / Galileo OLED)
       |                                                    |
       +--------------------+-------------------------------+
                            |
                            v
               +---------------------------+
               |  Godot 4.7 Gamepad UI     |
               |  (1280x800, D-Pad Nav)    |
               +---------------------------+
                            |
                            v
               +---------------------------+
               |  Yerel Guvenlik & Depo    |  <-- user://gemini.key (0600)
               |  Store & Profile Engine   |  <-- user://profiles.json (0600)
               +---------------------------+
                            |
                            | (HTTPS REST / Yalnizca Oyun Adi + AppID + Donanim)
                            v
               +---------------------------+
               |  Google Gemini 2.5 Flash  |
               +---------------------------+
                            |
                            v (Ham JSON)
               +---------------------------+
               |  Katı Sanitization Katmanı|  <-- TDP: [3, 15] W
               |  (profile.gd / Limits)    |  <-- GPU: [200, 1600] MHz
               +---------------------------+  <-- FPS: Hz Tam Boleni [30, 90]
                            |
                            v
        +----------------------------------------+
        | Nihai Onerilen Profil & Parametreler   |
        | - Quick Access Menu Yonergeleri        |
        | - Steam Baslatma Secenekleri (Panoya)  |
        +----------------------------------------+
```

---

## 2. Temel Bileşenler ve Teknik Özellikler

### A. Donanım ve Platform Kilidi (`deck_scan.gd`)
- `/sys/devices/virtual/dmi/id/product_name` arayüzünü denetler.
- Yalnızca `jupiter` (Steam Deck LCD, Aerith APU, 60Hz) ve `galileo` (Steam Deck OLED, Sephiroth 6nm APU, 90Hz) donanımlarını kabul eder.
- SteamOS 3.x kütüphane yollarını (`/home/deck/.local/share/Steam/steamapps` ve `/run/media/mmcblk0p1/steamapps`) otomatik tarayarak kurulu oyunları listeler.

### B. Hibrit YZ Motoru (`gemini.gd`)
- Kütüphanedeki her oyun için hedef donanım profilini (Aerith/Sephiroth, ekran tavan tazeleme hızı) temel alarak Google Gemini API üzerinden oyun motoruna özel profil üretir.
- **Güvenli API İletişimi:** Kullanıcının API anahtarı hiçbir uzak sunucuya aktarılmaz; yalnızca doğrudan Google AI Studio uç noktasına iletilir ve yerel cihazda `0600` izinleriyle izole edilir.

### C. Deterministik Güvenlik Katmanı (`profile.gd`)
Büyük dil modellerinin çıktısına donanım seviyesinde asla doğrudan güvenilmez. Tüm değerler katı sınır filtrelerinden geçirilir:
- **TDP Güç Sınırı:** 3 Watt ile 15 Watt arasına zorunlu kırpılır.
- **GPU Saat Frekansı:** 200 MHz ile 1600 MHz arasına zorunlu kırpılır.
- **Kare Hızı & Tazeleme Uyumu:** Kare süresi tutarlılığı (frame pacing) için FPS sınırı ekran tazeleme hızının tam böleni (`refresh_hz % fps_limit == 0`) olmaya zorlanır (Örn: 60Hz ekranda 60, 30; 90Hz ekranda 90, 45, 30).
- **Ortam Değişkeni Beyaz Listesi:** Yalnızca güvenli Wine/Proton/Mesa bayraklarına (`PROTON_USE_WINED3D`, `DXVK_ASYNC`, `DXVK_FRAME_RATE`, `WINE_FULLSCREEN_FSR`, `mesa_glthread` vb.) izin verilir. Zararlı kabuk komutları elenir.

### D. Gamepad Odaklı Arayüz (`main.gd`)
- Godot 4.7 tabanlı, 1280x800 Steam Deck ekran çözünürlüğüne optimize edilmiş tam ekran arayüz.
- D-Pad ve analog çubukla sorunsuz menü navigasyonu (A: Seç, B: Geri, D-Pad: Gezin).
- "Tüm oyunları optimize et", "Oyun listesi", "API anahtarı yönetimi" ve "Tek tuşla panoya kopyalama".
- Asenkron optimizasyon sürecini istenildiği anda durduran iptal emniyeti.

---

## 3. Kurulum (Steam Deck)

Steam Deck üzerinde Masaüstü Moduna (Desktop Mode) geçip Konsole uygulamasında aşağıdaki tek komutu çalıştırmanız yeterlidir:

```bash
curl -fsSL https://github.com/ozdil/deckopt/releases/latest/download/install.sh | bash
```

### Kurulum Betiğinin Yaptığı İşlemler:
1. Donanımın Steam Deck olduğunu BIOS düzeyinde doğrular.
2. Sürüm paketini ve SHA256 sağlama toplamını indirerek kriptografik doğrulama yapar.
3. Uygulamayı `~/Applications/deckopt/` dizinine yerleştirir.
4. `steamos-add-to-steam` aracılığıyla kısayolu doğrudan Steam kütüphanenize "Steam Dışı Oyun" olarak ekler.
5. Game Mode'a döndüğünüzde **deckopt** uygulamasını kütüphanenizde doğrudan görebilir ve oyun kumandasıyla başlatabilirsiniz.

---

## 4. Kullanım Adımları

1. **API Anahtarı:** İlk açılışta ücretsiz edinebileceğiniz Gemini API anahtarınızı girin (Ekran klavyesi kısayolu: `Steam + X`).
2. **Optimizasyon:** "Tüm oyunları optimize et" butonuna basın. Motor kütüphanedeki oyunları tarayarak profilleri üretir ve yerel veritabanında önbelleğe alır.
3. **Uygulama:** Listeden bir oyunu seçin:
   - Önerilen Kare Hızı, Yenileme Hızı, TDP ve GPU saat ayarlarını Steam'in sağ panelindeki **Quick Access (...) > Performans** menüsünden seçin.
   - "Başlatma seçeneklerini panoya kopyala" butonuna basarak kopyaladığınız satırı oyunun **Özellikler > Başlatma Seçenekleri** alanına yapıştırın.

---

## 5. Kaldırma (Uninstall)

```bash
curl -fsSL https://github.com/ozdil/deckopt/releases/latest/download/uninstall.sh | bash
```

Profillerinizi ve API anahtarınızı korumak veya tamamen temizlemek sizin tercihinize bırakılır (`-y` parametresi ile tümü temizlenebilir).

---

## 6. Lisans ve Güvenlik

- Kod tabanında, belgelerde ve commit geçmişinde katı sıfır emoji kuralı uygulanmaktadır.
- Tipografi: Varsayılan font `JetBrainsMono Nerd Font` standardındadır.
- Katkıda bulunma kuralları için `CONTRIBUTING.md` belgesini inceleyiniz.
