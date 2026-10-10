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

Serbest keşifte renkli ders kartı, konu ve 1–1000 soru seçilir. “Soru sınırı olmadan devam et” seçilirse sorular bitince aynı ders/konudan yeni bir grup yüklenir. Serbest çalışmada öğrenci Çalışmadan çık düğmesi, Escape veya Alt+F4 ile şifresiz döner. Velinin atanmış görevinde ebeveyn doğrulaması korunur.

`homework 2.zip` arşivinden yalnızca rol/mascot görselleri ve görünüm fikirleri alındı: yuvarlak portreler, turuncu–mor–yeşil giriş geçişi, pastel ders kartları, yetişkin panellerinin rol renkleri ve quiz kartları. Arşivin hesap, veritabanı, PIN, ses veya soru çözme mantığı aktarılmadı.


## Serbest çıkış, yanlışlar ve güncel dersler

Serbest çalışma ve yanlış soruları tekrar çözme öğrenci tarafından şifresiz bırakılabilir. Bu oturumlarda klavye kilidi başlatılmaz. Velinin/öğretmenin atanmış görevi aynı çıkış korumasını sürdürür.

Öğrenci ekranındaki **Yanlışlarımdan öğreniyorum** bölümünde tam soru verileri saklanan yanlışlar gösterilir. Doğru tekrar soruyu bu listeden kaldırır; önceki yanlış cevap rapordan silinmez. Görev yanlışının tekrarı serbest alıştırma olarak kaydedilir. Eski görev soruları ve mevcut bankayla eşleştirilebilen eski alıştırmalar da okunur. Seçenekleri/doğru yanıtı tutulmamış temsili örnek kayıtlar yeniden çözüm için uydurulmaz.

**Benzer yeni sorular hazırla** aynı kazanımdan altı Gemini alıştırması üretir. Yalnızca soru içeriği, açıklama ve sınıf düzeyi gönderilir; öğrenci adı veya hesap bilgisi gönderilmez. Üretim ayrı iş parçacığındadır. Üretilen sorular AI alıştırması olarak etiketlenir; öğretmen onaylı bankaya otomatik eklenmez.

Veli/öğretmen: **Hesap ve sınıflar → Yapay zekâ bağlantısını ayarla**. Anahtar bu bilgisayarın `.env` dosyasında tutulur. Anahtar olmadan yanlışların aynısını ve hazır İngilizce sorularını çözebilirsiniz. 1–4. sınıfların bütün mevcut konuları artık çevrimdışı başlangıç bankası içerir; bu sorular için anahtar gerekmez. Gerçek Gemini çağrısı anahtar olmadığı için bu geliştirmede yapılmamıştır; servis arayüzü ve hata akışı sahte yanıtlarla test edilir.

`active_curriculum.json` MEB'in 2026–2027 yıllık planları esas alınarak 10.10.2026 tarihinde hazırlanmıştır. Ders/konu listeleri ilkokul 1–4. sınıf düzeyindedir. İngilizce 2–4. sınıfta sunulur; 1. sınıfta gösterilmez. 4. sınıfta önizleme TYMM temaları yerine uygulanacak yıllık plandaki konular gösterilir. İngilizce başlangıç bankası tema başına sekiz özgün kelime/ifade alıştırması içerir; MEB sorusu veya tüm kazanımların kapsamlı ölçümü olarak sunulmaz. Kaynak: https://tymm.meb.gov.tr/taslak-cerceve-planlari/temel-egitim


Öğrenci adını ve okul numarasını yazarak şifresiz girebilir. İlk kayıt için öğretmenin sınıf kodu gerekir. Aynı sınıfta aynı numara ikinci kez kaydedilmez; sonraki girişlerde isim ve numara yeterlidir (aynı isim/numara birden çok sınıfta varsa sınıf kodu da istenir). Resimle giriş korunmuştur. Öğretmenin öğrenci listesinde okul numarası görünür, satıra çift tıklanarak bireysel gelişim açılır. Sınıf koduyla oluşturulan profil otomatik olarak bir veli hesabına bağlanmaz; veli bağlantısı ayrıca yetişkinlerce düzenlenmelidir.

Mevcut 182 konunun tamamında çevrimdışı başlangıç soruları vardır. Yeni bir müfredat konusu ileride bankasız eklenirse teknik hata yerine kısa açıklama gösterilir. Sınıf öğretmeninin veya kendi velisinin onaylayıp kaydettiği konu paketleri serbest çalışmada çevrimdışı kullanılabilir. Başka sınıf/veli paketleri paylaşılmaz. Yapay zekâ üretimi gerçek API anahtarı gerektirir.


## Bütün konularda çevrimdışı başlangıç soruları

`authored_topics.py` her aktif ders/konuya özel özgün bilgi eşleştirme, okuduğunu anlama ve yerel matematik soruları içerir. MEB ders ve konu listesi kaynağıdır; bu sorular MEB'in yayımladığı resmî sorular değildir. Mevcut 182 konuda toplam 2621 banka kaydı vardır (aynı kavram farklı sınıflarda da çalışılabilir). Her konuda en az 8 soru bulunur. Bu bir başlangıç ve tekrar bankasıdır; her öğrenme çıktısının kapsamlı ölçümü veya öğretmen değerlendirmesinin yerine geçen bir sınav değildir. Türkçe metinleri özgündür, matematik sayısal seçenekleri hesaplanır.

Serbest çalışmada soru sırası karıştırılır. Soru sayısı bankadaki soru sayısını aşarsa aynı konunun soruları tekrar edilir; farklı dersten dolgu soru kullanılmaz. Veli/öğretmenin 1–30 soruluk görevlerinde de aynı tekrar ilkesi uygulanır. Yepyeni Gemini soruları ve yapay zekâ ile benzer soru üretimi hâlâ API anahtarı gerektirir. Uzun cevap seçenekleri butonlarda satırlara bölünerek gösterilir.

Trafik/ilk yardım başlangıç bölümündeki acil çağrı ve konum bilgisi için resmî kaynak: https://112.gov.tr/kurumlar/112.gov.tr/IcSite/ankara/ACIL_DURUM_KILAVUZU.pdf . Çocuklara tıbbi müdahale tarifi verilmez.


## Öğretmenin sorularını veli saatinde açma

1. Öğretmen **Soru atölyesi** bölümünde sorularını elle ekler veya ders belgesinden taslak hazırlar. Doğru cevapları kontrol edip paketi kaydeder.
2. Veli kendi çocuğunu seçer. Çocuk öğretmenin sınıfına bağlı olmalıdır.
3. **Görevler → Yeni görev ver → Hocanın sorularını ekle** düğmesiyle öğretmenin paketini seçer.
4. Önizlemede istenmeyen soruların işaretini kaldırabilir. Başlangıç tarihi ve saati seçilip görev oluşturulur.
5. Saat geldiğinde soru ekranı otomatik açılır; çocuk serbest alıştırma çözüyorsa saatli göreve geçilir. Bilgisayar ve Windows oturumu açık olmalıdır. Öğrencinin bir başlatma düğmesine basması gerekmez.

Paketler bu bilgisayarın veritabanında paylaşılır. Ayrı bilgisayarlar arasında internet üzerinden eşitleme yapılmaz.

**Genel bakış** raporları tüm zamanlar, son 7 gün ve son 30 gün için filtrelenebilir; CSV seçili raporu indirir. **Hesap ve sınıflar** bölümünden öğrenci veya sınıf adı düzenlenebilir. Kayıtlı öğrencilerin sınıf düzeyleri çelişecek şekilde değiştirilmez.

**Ses ve yapay zekâ ayarları** penceresinde yerel Türkçe ses, ElevenLabs veya Gemini seçilir. Boş anahtar alanları kayıtlı anahtarları silmez. Anlatımda hareketli ders görselleri kullanılır; otomatik adım geçişi ses bittikten sonra olur ve kapatılabilir. Mevcut matematik/kesir çizimleri korunur.


## Yanlış sorular için benzer alıştırmalar

Öğrenci → Yanlışlarımdan öğreniyorum → Benzer alıştırmalar hazırla: Gemini anahtarı yoksa veya hizmet çalışmazsa aynı müfredat konusunun onaylı hazır soruları açılır. Aynı kazanımdaki sorular önceliklidir; kaynak soru ve tekrarlar hariç tutulur. Bu çevrimdışı sorular yapay zekâ üretimi olarak işaretlenmez. Yeterli farklı soru varsa altıya kadar alıştırma gelir; eksik sayı aynı soruyla doldurulmaz.


Soru atölyesinde **Seçili konunun hazır sorularını getir · İnternetsiz** düğmesi belge yüklemeden kullanılabilir. Gemini anahtarı olmadan belgeden üretim istendiğinde de bu hazır banka getirilir ve durum mesajında belirtilir. Belgeye özel yeni soru üretimi için aynı ekrandaki **Ses ve yapay zekâ bağlantısını ayarla** düğmesiyle kendi Gemini anahtarınızı kaydedin.


## Soru türüne göre %80 öğrenme hedefi

Saatli/atanmış görevlerde süreye bağlı bitiş kaldırıldı. Her soru türünün son en fazla 5 yanıtındaki ipucusuz doğruluk oranı izlenir. Her türde en az %80 ve o tür için gerekli yanıt sayısına ulaşılınca **Uygulamadan çık** düğmesi açılır. En az 5 soruluk türlerde 5 yanıt aranır; daha küçük paketlerde mevcut tür kapsamı esas alınır. Yalnızca 1 doğru yanıtla büyük bir görev tamamlanmaz. Bu oran öğrenmeye yönelik bir uygulama göstergesidir.

Yanlış yapılan türler öne alınır; onaylı aynı türdeki varyasyonlar ek destek olarak sunulur. Yeni varyasyon yoksa aralıklı tekrar yapılır. Ek destek yanıtları özgün görev cevaplarının üzerine yazılmaz. Öğrenme ilerlemesi kapanıp açılınca korunur. Veli doğrulamasıyla çıkış seçeneği devam eder. Serbest çalışmada çocuk istediği zaman çıkabilir.

Öğretmen soru atölyesine PDF/Word/metin belgesini yükleyip **PDF sorularını analiz et · Benzer taslaklar üret** düğmesini kullanabilir. Gemini soru türü/kazanım etiketlerini belirler ve farklı bağlamlarda benzer sorular üretir. Öğretmen inceleyip onaylar; veli bu paketi saatli göreve ekler. Bu gerçek yapay zekâ işlemi için Gemini anahtarı gerekir; internetsiz hazır bankanın belgeden üretim olmadığı ayrıca gösterilir.
