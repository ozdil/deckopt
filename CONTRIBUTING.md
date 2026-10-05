# Katkı ve Güvenlik Yönergeleri

Bu proje Valve Steam Deck (LCD/OLED) donanımları için tasarlanmış bağımsız bir açık kaynaklı optimizasyon aracıdır.

## Güvenlik İlkeleri

1. **Donanım Koruma Sınırları:**
   - TDP sınırları: 3W ile 15W arasında zorunlu kırpılır.
   - GPU saat sınırları: 200MHz ile 1600MHz arasında sınırlandırılır.
   - Yenileme hızı: LCD için maksimum 60Hz, OLED için maksimum 90Hz.
2. **Kullanıcı İzolasyonu:**
   - API anahtarları yalnızca kullanıcının yerel cihazında (`user://gemini.key`) 0600 izinleriyle saklanır.
   - Sunucusuz doğrudan bağlantı kullanılır.
3. **Emoji ve Dil Standartları:**
   - Kod tabanında, commit mesajlarında ve dokümanlarda sıfır emoji kuralı geçerlidir.
   - Varsayılan yazı tipi: `JetBrainsMono Nerd Font`.
