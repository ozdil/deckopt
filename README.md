# deckopt

Steam Deck için YZ destekli oyun ayar asistanı. Kütüphanenizdeki her oyun için Gemini ile bir performans profili üretir: TDP, GPU saati, kare sınırı, yenileme hızı, ölçekleme ve başlatma seçenekleri.

Yalnızca Valve Steam Deck (LCD ve OLED) üzerinde çalışır.

## Kurulum

1. Steam Deck'te Desktop Mode'a geçin ve Konsole'u açın.
2. Şu komutu çalıştırın:

   ```bash
   curl -fsSL https://github.com/ozdil/deckopt/releases/latest/download/install.sh | bash
   ```

3. Steam'de onay penceresi çıkarsa "Ekle"ye basın.
4. Game Mode'a dönün. deckopt kütüphanenizde "Steam Dışı" altında görünür.

Betik root yetkisi istemez. İndirilen paketin SHA256 sağlama toplamını doğrular, uygulamayı `~/Applications/deckopt` altına kurar.

## Kullanım

- İlk açılışta Gemini API anahtarınızı girin (aistudio.google.com üzerinden ücretsiz alınabilir). Ekran klavyesi için Steam + X.
- "Tüm oyunları optimize et" ile profilleri üretin.
- Bir oyunu seçip önerilen değerleri Quick Access (...) > Performans menüsünden uygulayın; başlatma seçeneklerini oyunun Özellikler sayfasına yapıştırın.

Kontroller: D-pad gezinme, A seçme, B geri.

## Gizlilik

API anahtarınız yalnızca cihazınızda, sahibine özel izinlerle (0600) saklanır. Profil üretmek için oyun adı, Steam uygulama numarası ve cihaz modeli (LCD/OLED) Google Gemini API'sine gönderilir. Başka hiçbir yere veri gönderilmez.

## Kaldırma

```bash
curl -fsSL https://github.com/ozdil/deckopt/releases/latest/download/uninstall.sh | bash
```

## Geliştirme

- Uygulama: `godot/` (Godot 4.7). Steam Deck dışında denemek için `DECKOPT_ALLOW_ANY_DEVICE=1`.
- Yeni sürüm: `git tag v0.1.0 && git push --tags`. GitHub Actions build alır ve sürümü yayınlar.
- `deckopt/` altındaki Python CLI eski prototiptir; dağıtıma dahil değildir.
