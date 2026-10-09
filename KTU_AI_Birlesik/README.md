# Birleşik Öğrenme Molası

Başlangıç dosyası: `uygulama/main.py`. Python **3.12** gerekir.
Bu teslim, üç ZIP ve bizim mevcut motorumuzun ayrı klasörde birleştirilmiş sürümüdür.
Mevcut proje ve indirilen ZIP'ler değiştirilmedi.

## Kayıpsız koruma

- `orijinaller/`: gönderilen üç ZIP birebir saklanır. Bizim kaynaklarımız ayrıca
  `bizim_kaynaklar.zip` içinde, gizli ayar ve çalışma verileri olmadan saklanır.
- `KAYNAK_ENVANTERI.json`: üç ZIP içindeki 236 dosyanın boyutu ve SHA-256 değeri.
- `TESLIM_ENVANTERI.json`: yeni teslimdeki dosyaların SHA-256 değerleri.
- Mac kaynak adları bozuk kodlandığı için aktif arayüzde Windows paketinin
  aynı içerikli `assets/student_girl.png` vb. dosyaları kullanıldı; orijinal adlar
  ve Mac metadata dosyaları ZIP içinde kaybolmadan korunur.

## Birleşen özellikler

- Windows sürümünün oyun/mola sayacı, kazanım ilerlemesi, soru paketleri,
  PIN deneme sınırı, PBKDF2 PIN saklama, sonuç/CSV raporu ve DLL arayüzü korunur.
- Homework arayüzünün profil/giriş/veli/öğretmen/ayar sayfaları, görselleri,
  animasyonları ve quiz kartı kullanılır. Ana çocuk quiz kartı gerçek oturum
  motoruna bağlıdır; demo bitir butonu PIN doğrulamasını atlatamaz.
- KTU veritabanının veli, öğretmen, sınıf, öğrenci, konu, ödev, soru ve rapor
  fonksiyonları `Sınıflar ve Ödevler` sekmesinden kullanılabilir.
- Jessica Türkçe ses, WAV önbelleği ve arka planda Qt ses hazırlığı bağlandı.
- Bizim resimli fen/sosyal içeriği ve gözden geçirilmiş Gemini bankası korunur.
  Yanlış/yardımlı cevaptan sonra aynı kavramdan soru önceliği vardır.
- Mevcut Anthropic üretimi korunur; ayrıca Gemini üretimi + ikinci model kontrolü
  soru paketi sekmesine eklenir. Gerçek API'ler yalnız kullanıcı üretim isterse çağrılır.
- Homework JSON'undaki 20 sorunun tamamı aktarılır. Türkçe, matematik, genel
  kültür ve fen havuzları konu listesinden seçilebilir. Bir soru belirsiz olduğu
  için otomatik çocuk havuzuna alınmaz, veli paket incelemesinde gösterilir.

## Kurulum ve çalıştırma

1. Python 3.12'nin Windows kurulumunu kullanın.
2. `uygulama` klasöründe `powershell -File kurulum.ps1` çalıştırın.
3. `.env.example` örneğinden kendi `.env` dosyanızı oluşturup kendi anahtarlarınızı
   girin. Başka bir projenin `.env` dosyasının üzerine yazmayın. Anahtarlar pakette yoktur.
4. `BASLAT.bat` ile arayüz ve öğrenme akışı açılır; native klavye DLL'si yüklenmez.
5. DLL arayüzünü de etkinleştirmek isteyen veli `BASLAT_KLAVYE_KILIDI.bat` kullanabilir.
   Bu native yolun gerçek klavye engelleme davranışı bu birleşimde test edilmedi.

Mevcut yerel ayarı kopyalamadan okumak için:
`python main.py --no-native-guard --env "mevcut-proje\.env"`

Öğrenci/Konu sekmesinden ad, sınıf ve kazanımları seçip Kaydet'e basın.
Oyun oturumunu başlatın; hızlı deneme için “Molayı şimdi başlat” kullanılabilir.
İlk kurulumun miras alınan demo ebeveyn PIN'i **1234**; Süre-Güvenlik sekmesinden değiştirilebilir.
Ses düğmesi Jessica'yı kullanır. Ücretsiz ElevenLabs hesabı sınırsız değildir.

## Veritabanları

Windows oturum şeması `uygulama/data/ogrenme_molasi.db`, sınıf/ödev şeması
`uygulama/data/school_records.db` altında tutulur. Birbirlerinin üzerine yazılmaz.
Yollar `OM_DB_PATH` / `OM_SCHOOL_DB_PATH` ile ayrı ayrı ayarlanabilir.
Öğrenci oturum profili ile sınıf/ödev öğrenci kayıtları farklı şemalardadır;
otomatik kimlik eşleştirmesi yapılmaz, sınıf/ödev sekmesinden öğrenci seçilir.
Mevcut dış veritabanlarının otomatik taşınması bu çalışmada yapılmadı.

## Doğrulama ve sınırlar

`uygulama` klasöründe: `python -m unittest discover -s . -p "test_*.py" -v`

27 test geçti. Tüm aktif Python kaynaklarının sentaks kontrolü geçti.
Qt ekranları offscreen açılıp görüntüleri incelendi. Gerçek kullanıcı DB'lerine
yazılmadı; testler iki geçici DB kullandı. Native DLL importtan önce mock ile
devre dışı bırakıldı; yeni ağ çağrısı ve gerçek klavye kilidi testi yapılmadı.
Jessica'nın önceki gerçek API ve pygame denemeleri başarılıydı; birleşik Qt
bağlantısının canlı ses testi ayrıca yapılmalı. Mikrofon ayrıca bağımlılık gerektirir.

`OgrenmeMolasi-Windows.zip` kaynak .py içermiyor. 14 uygulama modülü EXE'nin
PYZ arşivinden çalıştırılmadan çıkarılıp **orijinal bytecode olarak** korunmuştur.
Kaynak kod geri elde edilmiş sayılmaz. Düzenlenebilir adaptörler bu kodu yükler.
Bu nedenle Python 3.12 bağımlılığı vardır; kaynak .py'ler gelirse bytecode yerine
geçirilebilir. Yeni EXE üretilmedi; orijinal EXE orijinal ZIP'te korunur.

Çakışan kaynaklar körlemesine birleştirilmedi: boş `keyboard_guard.py` yerine
Windows'un gerçek DLL arayüzü; sabit demo PIN yerine kayıtlı/deneme sınırlı PIN;
bağımsız quiz cevabı yerine gerçek oturum kaydı seçildi. Tüm eski dosyalar arşivde durur.

Bilinen içerik notu: “Aşağıdakilerden hangisi birleşik yazılır?” sorusunda
“bilgisayar” ve “pazartesi” birlikte doğru olabilir. Orijinal cevap indeksi
değiştirilmeden saklandı; veli incelemesi gerekli olarak işaretlendi.

Eski yerel TTS ve bağımsız Tkinter demo `learning_engine/` altında korunur.
Yerel model/venv ağırlıkları paylaşım paketine alınmaz; mevcut klasörlerinde durur.
Jessica kullanımı için bu modellerin kurulması gerekmez.
