# deckopt: Valve Steam Deck için YZ Destekli Otonom Oyun Optimizasyon Motoru (Alfa v0.1.0)

Valve Steam Deck donanımları (LCD "Jupiter" ve OLED "Galileo") ile SteamOS 3.x çalışma zamanı için özel olarak geliştirilmiş, hibrit yapay zeka destekli yerleşik oyun optimizasyon motoru ve yönetim arayüzüdür.

Bu yazılım yalnızca Valve Steam Deck donanımı üzerinde çalışacak şekilde platform kilidine sahiptir. Farklı bir sistemde çalıştırıldığında DMI/BIOS seviyesinde devreye giren donanım kilidi sayesinde yürütmeyi güvenle durdurur.

İngilizce ana dokümantasyon için lütfen [README.md](README.md) dosyasına bakınız.

---

## Kurulum (Steam Deck)

Steam Deck üzerinde Masaüstü Moduna (Desktop Mode) geçip Konsole uygulamasında aşağıdaki tek komutu çalıştırmanız yeterlidir:

```bash
curl -fsSL https://github.com/ozdil/deckopt/releases/latest/download/install.sh | bash
```

## Kullanım Adımları

1. **API Anahtarı:** İlk açılışta ücretsiz edinebileceğiniz Gemini API anahtarınızı girin (Ekran klavyesi kısayolu: `Steam + X`).
2. **Optimizasyon:** "Tüm oyunları optimize et" butonuna basın.
3. **Uygulama:** Listeden bir oyunu seçin ve önerilen değerleri Steam'in **Quick Access (...) > Performans** menüsünden seçin; başlatma seçeneklerini oyunun Özellikler alanına yapıştırın.

## Kaldırma

```bash
curl -fsSL https://github.com/ozdil/deckopt/releases/latest/download/uninstall.sh | bash
```
