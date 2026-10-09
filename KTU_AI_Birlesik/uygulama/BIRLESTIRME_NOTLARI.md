# Birleştirme notları — 9 Ekim 2026

Arkadaş projesindeki belge tabanlı soru hazırlama, kademeli yardım ve raporlama fikirleri mevcut çok hesaplı uygulamaya uyarlandı. Eski tek öğrencili veritabanı, varsayılan PIN ve zorunlu bulut ses akışı aktarılmadı. Hesap kapsamı, el yazısı, yerel ses ve mevcut soru/görsel kaynakları korundu.

`native/keyboard_guard.c` arkadaşın sağladığı kaynak arşivinden alınmıştır. Mevcut DLL değiştirilmedi; arşivdeki DLL ile aynı SHA256 değerine sahip olduğu kontrol edildi. Yeni Windows paketi mevcut DLL'yi içerir.

Değişiklik öncesi kod ve SQLite yedekleri proje kökündeki `.local_backups` klasöründedir. Bu çalışma için commit/push yapılmadı. Otomatik soru üretimi sahte servis yanıtıyla test edildi; gerçek Gemini üretimi API anahtarı gerektirir.
