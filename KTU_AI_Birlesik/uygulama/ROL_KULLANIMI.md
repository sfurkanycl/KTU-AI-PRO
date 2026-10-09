# Öğrenci, veli ve öğretmen ekranları

Uygulamayı proje kökünden `python main.py` ile açın. Yeni giriş ekranı varsayılan olarak gelir.

## Veli

1. Giriş ekranından **Veli** seçip hesap oluşturun.
2. **Hesap ve sınıflar → Çocuk hesabı oluştur** ile ad, sınıf ve öğrenci görselini seçin. Çocuk kullanıcı adı/şifresi gerekmez.
3. **Görevler → Yeni görev ver** ile ders/konu, soru sayısı ve son tarih seçin.
4. Çocuğunuzu bir öğretmene bağlamak için öğretmenin sınıf kodunu **Seçili çocuğu sınıfa bağla** alanında kullanın.
5. **Genel bakış** bölümünde seçtiğiniz çocuğun toplam, doğru/yanlış, son 7 gün ve konu grafiklerini izleyin.

Veli yalnızca kendi çocuklarını görür. Öğretmen görevleri de çocuğun görevleri arasında görünür.

Yeni görev formunda tarih ve saat seçip **Bu tarihte otomatik soru ekranını aç** seçeneğini işaretleyebilirsiniz. Uygulama açıkken kendi zamanlayıcısı, kapalıyken Windows Görev Zamanlayıcısı çalışır. Bilgisayar ve Windows oturumu açık olmalıdır; kapalı bilgisayarı açmaz. Windows kayıt işlemi başarısız olursa bunu ekranda bildirir ve uygulamanın açık kalmasını ister. Aynı görevin iki uygulama penceresinde birden açılması engellenir.

**Hesap ve sınıflar → Serbest çalışma derslerini seç** ile alıştırmalarda hangi ders ve konuların sırayla geleceğini belirleyebilirsiniz. Atanmış görevler bu tercihten bağımsızdır.

## Öğretmen

1. Giriş ekranından **Öğretmen** seçip hesap oluşturun.
2. **Hesap ve sınıflar → Yeni sınıf oluştur** ile sınıfınızı kaydedin.
3. **Kodu velilerle paylaş · Bildirim gönder** düğmesi yerel sistemdeki veli hesaplarına sınıf adı ve kodunu gönderir. Veliler sonraki girişte bildirimi görür. Öğrenci kodu kendi başına kullanamaz; veli hesabı gerekir.
4. Sınıf seçerek genel grafikleri, görünüm alanından öğrenci seçerek kişisel grafikleri açın.
5. **Öğrencilerim** tablosunda bir satıra çift tıklamak kişisel raporu açar.
6. **Görevler → Yeni görev ver** ile sınıfın tamamına veya sınıftaki tek bir öğrenciye çalışma verin.

Öğretmen yalnızca kendi sınıflarını ve bu sınıflardaki öğrencileri görür. Bir öğrencinin raporu görev ve serbest alıştırma cevaplarını kapsar.

## Öğrenci

Öğrenci, giriş ekranındaki resmine dokunarak şifresiz girer. Yalnızca kendi görev listesini ve hazırlanan soru ekranını görür; veli ve öğretmen yönetim ekranlarına erişmez. Bu bilgisayardaki çocuk profilleri girişte listelenir; profil seçimi kimlik doğrulaması değildir.

Görevler kaldığı yerden devam eder. Cevaplar öğrenciye kaydedilir. Doğru cevapta otomatik geçilir; yanlış cevapta açıklama incelenip sonraki soruya geçilebilir. Ses, görsel anlatım ve otomatik el yazısı dönüşümü kullanılabilir. Serbest keşif farklı derslerden alıştırmalar içerir.

Serbest keşifte öğrenci kendi konusunu seçebilir. Quiz tam ekranda açılır; kapatma/Escape ile çıkılamaz. Çalışma bitince öğrenci ekranına dönülür; erken çıkış için bağlı veli hesabının şifresi gerekir. Yerel klavye koruması quiz süresince çalışır ve bitişte bırakılır. Windows'un güvenli sistem ekranı (Ctrl+Alt+Del) uygulamalar tarafından engellenmez.

## MEB müfredatı

MEB'in resmi TYMM sitesinden sınıf/ders/tema başlıkları ve kaynak bağlantıları `meb_curriculum.json` dosyasına indirilmiştir. `python curriculum.py` önbelleği yeniler; normal kullanım internet gerektirmez. MEB tema seçimi görev formundadır. Desteklenen işlemler, güvenli yaşam, canlılar ve madde temaları hazır yerel soru bankalarına eşleşir. Diğer temalara öğretmen/veli kendi çoktan seçmeli sorularını ekler. Hazır sorular MEB sorusu olarak sunulmaz; tüm müfredata ait eksiksiz otomatik soru bankası bulunmaz.

2026–2027'de yeni model ilkokul 1, 2 ve 3. sınıflarda uygulanır. Sitedeki yeni 4. sınıf temaları inceleme amacıyla gösterilir ve otomatik eşleştirilmez; uygulanan 4. sınıf yıllık planı öğretmen tarafından ayrıca doğrulanmalıdır. Kaynak: https://tymm.meb.gov.tr/taslak-cerceve-planlari/temel-egitim

## Hazır örnek hesaplar

Öğretmen: `demo.ogretmen` veya `demo.ogretmen2`. Veli: `demo.veli`, `demo.veli2`, `demo.veli3`. Bu örnek hesapların şifresi: `Demo123!`.

Altı örnek öğrenci, dört örnek sınıf, atanmış görevler ve yedi günlük temsili ilerlemeler eklenmiştir. Adlarında **Örnek** yazar; gerçek hesaplar değiştirilmez. `python seed_demo.py` tekrar çalıştırılınca aynı kayıtlar çoğalmaz. Öğrenciler görsellerinden şifresiz seçilir. Örnek görevler otomatik başlatılacak saatler içermez.

## Eski kayıtlar

Önceki veritabanları silinmez. Eski tek öğrenci raporlarını yeni hesaba bağlamak için veli ekranında doğru çocuğu seçip **Hesap ve sınıflar → Önceki tek öğrenci raporlarını bağla** işlemini kullanın. Eski ebeveyn PIN’i gerekir. Aynı kayıt iki kez veya farklı çocuklara aktarılamaz.

Korunan eski yönetim ekranı gerekirse `python main.py --legacy-admin` ile açılabilir. Eski okul kullanıcılarına otomatik şifre atanmaz.

## Verilerin kapsamı

Bu sürüm aynı bilgisayardaki yerel SQLite kayıtlarını kullanır. Bildirimler bu veritabanındaki hesaplara ulaşır; ayrı bilgisayarlara internet üzerinden gönderim/eşitleme içermez. Örnek ilerlemeler yalnızca açıkça etiketlenmiş örnek öğrencilere eklenir. Görev ve sınıf oluşturma arayüzü ilkokul 1–4. sınıf içindir.

Şifreler düz metin saklanmaz; PBKDF2 ile türetilen değerler saklanır. Beş hatalı girişten sonra hesap beş dakika bekletilir.

## Soru atölyesi ve yeni raporlar

Veli veya öğretmen menüsündeki **Soru atölyesi** ile PDF, DOCX, TXT ve MD belgelerini okuyabilir, ders ve MEB temasını seçebilir, soruları ayrı alanlarda düzenleyebilirsiniz. Belgeden otomatik taslak üretimi `.env` içindeki `GEMINI_GENERATOR_KEY` ile çalışır; yalnızca üret düğmesine basınca belge metni Gemini hizmetine gönderilir. Taranmış, metinsiz PDF için önce OCR gerekir. Taslaklar kontrol edilip açıkça onaylanmadan görev olarak kullanılamaz. Paketler yalnızca oluşturan yetişkin hesabına görünür.

Yanlış cevaplarda önce ipucu, ardından açıklama ve mevcutsa çözümlü örnek gösterilir. Uygun olduğunda aynı kavramdan farklı soru öne alınır. Yerel sorularda en fazla iki ek destek sorusu verilir; bunlar asıl ödevin tamamlanma sayısını değiştirmez. Öğretmenin onayladığı belge paketine dışarıdan soru karıştırılmaz.

Raporlar ders/kavram, ipucu, yardımsız doğru ve destek sorusu bilgilerini içerir. CSV çıktısı seçili çocuğun/sınıfın erişilebilir kayıtlarıyla sınırlıdır. Yeterli kayıt yokken “Veri birikiyor” gösterilir; durum etiketleri eğitimsel özetlerdir.

## Windows teslim paketi

`python build_release.py` yerel ses modeli dahil `dist/OgrenmeMolasi-Windows.zip` oluşturur. ZIP tamamen çıkarıldıktan sonra `OgrenmeMolasi.exe` açılır. Paket, kaynak projenin kişisel veritabanını veya API anahtarlarını içermez. İlk ekranda örnek hesapları yükleyebilir veya kendi hesaplarınızı oluşturabilirsiniz. Paket sürümünün kayıtları ve isteğe bağlı `.env` dosyası `%LOCALAPPDATA%\OgrenmeMolasi` altında tutulur. Yerel ses için hedef bilgisayarda Python veya `.venv` gerekmez.


## 10 Ekim: öğrenci keşif ekranı ve otomatik çalışmalar

Öğrenci ekranında görev başlatma/devam düğmesi bulunmaz. Veli yeni görev verirken tarih ve saati seçer. Öğretmenin verdiği veya önceden saatsiz oluşturulmuş görev için veli **Görevler → Başlangıç saatini ayarla** yolunu kullanır. Zamanlama çocuk bazındadır; aynı sınıftaki kardeşin saatini etkilemez. Saat değiştirilince önceki bekleyen zamanlama iptal edilir. Uygulama açıkken saniyelik kontrol yapılır; kapalıyken Windows Görev Zamanlayıcısı açar. Bilgisayar ve Windows kullanıcı oturumu açık olmalıdır. Planlı çalışma, devam eden serbest alıştırmanın önüne geçer; kaydedilmiş cevaplar korunur.

Serbest keşifte renkli ders kartı, konu ve 1–1000 soru seçilir. “Soru sınırı olmadan devam et” seçilirse sorular bitince aynı ders/konudan yeni bir grup yüklenir. Mevcut oturum süresi ve ebeveyn doğrulaması korunur. Öğrenciye sunulan konular uygulamadaki hazır soru kaynaklarıyla sınırlıdır.

`homework 2.zip` arşivinden yalnızca rol/mascot görselleri ve görünüm fikirleri alındı: yuvarlak portreler, turuncu–mor–yeşil giriş geçişi, pastel ders kartları, yetişkin panellerinin rol renkleri ve quiz kartları. Arşivin hesap, veritabanı, PIN, ses veya soru çözme mantığı aktarılmadı.
