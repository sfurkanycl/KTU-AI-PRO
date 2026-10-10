# Öğrenme Molası — 7 dakikalık konuşma metni

## 1. Öğrenme Molası (20 sn)

Öğrenme Molası, ilkokul öğrencilerinin bilgisayarda geçirdiği zamanın içine planlı öğrenme etkinlikleri yerleştiren bir Windows masaüstü uygulamasıdır. Projede öğrenci, veli ve öğretmen aynı öğrenme sürecini farklı ekranlardan takip eder. Amacımız çocuğa yalnızca soru çözdürmek değil, zorlandığı kazanımı belirleyip farklı sorularla pekiştirmesini sağlamaktır. Sunumda kullanıcı akışını, teknik yapıyı ve mevcut sınırlarımızı anlatacağız.

## 2. Veliye konu bazında tekrar önerisi (30 sn)

Veli ekranına yalnızca genel doğru yanlış sayısını değil, tekrar edilmesi önerilen konuları ekledik. Ders, konu, toplam cevap, yanlış sayısı ve başarı oranı birlikte görülüyor. Başarı yüzde seksenin altında olduğunda veya ipucu kullanımı yüksek olduğunda pekiştirme önerisi gösteriyoruz. Beşten az cevap varsa kesin bir yetersizlik yargısı vermeden az veri diyoruz. Çözülmemiş konular değerlendirilmez. reading_values gibi teknik kodlar kullanıcıya gösterilmiyor. Öğretmen kendi sınıfını ve seçtiği öğrencinin gelişimini görebiliyor.

## 3. Kullandığımız diller ve araçlar (35 sn)

Uygulamanın ana programlama dili Python. Veriler SQLite üzerinde SQL ile tutuluyor. Yapay zekâ ve soru paketleri arasında JSON kullanıyoruz; Windows görev zamanlayıcı tanımları XML biçiminde. Masaüstü arayüz PyQt6 ile geliştirildi. QThread ağ ve tanıma işlerini arayüzden ayırıyor, QTimer zaman ve çizim olaylarını yönetiyor. Gemini bağlantısında google-genai, yanıt doğrulamada Pydantic kullanılıyor. PDF metinleri pypdf ile okunuyor. Ses için yapılandırmaya göre yerel Piper, ElevenLabs veya Gemini TTS, oynatma için pygame kullanılıyor. Geliştirme ortamı VS Code, sürüm takibi Git ve GitHub. Uygulama yerel Windows prototipidir.

## 4. Yazılım mimarisi ve iş parçacıkları (35 sn)

Uygulamanın ana dili Python, masaüstü arayüzü PyQt6. Arayüz olay döngüsü kullanıcı işlemlerini yönetiyor. role_store hesap, yetkilendirme, görev ve cevap kaydını gerçekleştiriyor. role_quiz oturum akışını, mastery_session ise ilerleme kararını yönetiyor. Yeni soru üretimi curriculum_practice içindeki QThread işçisiyle çalışıyor. İşçi ready ve failed sinyalleri gönderiyor, arayüz bu sinyalleri ana iş parçacığında karşılıyor. Böylece ağ isteği sürerken çocuk çalışmaya devam edebiliyor. Kalıcı kayıtları SQLite üzerinde tutuyoruz. Gemini dış hizmet, hazır soru bankası ise yerel kaynak. Bu sürümde merkezi sunucu veya cihazlar arasında eşitleme yok.

## 5. Veri modeli ve cevapların kaydı (30 sn)

Veri modelinde veli ve öğretmen users tablosunda, çocuklar students tablosunda bulunuyor. students.parent_id çocuğu veliye bağlıyor. classes.teacher_id sınıfı öğretmene bağlıyor. class_students öğrencilerle sınıflar arasındaki çoktan çoğa ilişkiyi tutuyor. Görevler assignments, sorular questions tablosunda. Görev yanıtları student_results, serbest ve ek destek yanıtları practice_attempts üzerinden saklanıyor. answer_metadata ders, kazanım, süre ve destek bilgisini tamamlıyor. answer_snapshots soru metninin o andaki kopyasını ve parmak izini tutuyor. SQLite bağlantılarında foreign_keys açık. Cevap kaydı BEGIN IMMEDIATE işlemiyle birden fazla ilgili kaydı birlikte yazıyor.

## 6. İlerlemeyi cevaplardan izliyoruz (40 sn)

Planlı görevlerde yalnızca süre dolmasını beklemiyoruz. Her soru türü için son en fazla beş yanıtı tutuyoruz. İpucu kullanılan doğru cevap, yardımsız başarı göstergesine katkı sağlamıyor. Bir soru türündeki son beş yanıtın dördü yardımsız doğruysa o türün oranı yüzde seksen olur. Ancak diğer türlerde de gerekli örnek sayısı ve başarı sağlanmalıdır. Kod, görevdeki soru sayısına göre asgari örnek sayısını sınırlar. Dolayısıyla çok küçük görevlerde ölçüm daha zayıftır. Bu oran bir uygulama içi ilerleme kuralıdır. Çocuğun konuyu bilimsel olarak yüzde seksen öğrendiğini kanıtlayan psikometrik bir ölçüm değildir. Eşiği ve örnek sayısını pilot sonuçlarına göre geliştirmeyi hedefliyoruz.

## 7. Gemini API ve doğrulama hattı (40 sn)

Yanlış cevap, arayüzden arka plan işçisine gider. Gemini isteğine soru, seçenekler, doğru cevap, açıklama, kazanım ve daha önce kullanılan soru metinleri ekleniyor. Öğrenci kimliğini bu isteğin ayrı bir alanı olarak göndermiyoruz, ancak soru veya belge içine kişisel bilgi yazılmışsa içerikle birlikte gidebilir. Google GenAI SDK üzerinden Interactions API kullanıyoruz. Kodun varsayılan modeli gemini-3.8-flash, model adı ortam ayarıyla değişebilir. Yanıt JSON metni olarak geliyor. Pydantic seçenek sayısını ve cevap indeksini doğruluyor. Ek kurallar ve tekrar kontrolünden sonra üç yeni destek sorusu oturuma ekleniyor. Altmış saniyelik zaman aşımı ayarlı. Kota ve bağlantı hatasında hazır sorularla devam ediyoruz. Şema kontrolü içeriğin anlam bakımından doğruluğunu garanti etmiyor.

## 8. Yardım istendiğinde işlemli matematik çözümü (30 sn)

Matematikte yapay zekâyı öğrenci yardım istediğinde devreye alıyoruz. Bu soruyu anlat düğmesi mevcut soru, seçenekler ve beklenen cevap üzerinden kısa işlemli çözüm istiyor. İstek QThread üzerinde yürürken mevcut anlatım başlıyor. JSON şeması doğrulanıyor; üretilen sonucun kayıtlı seçenekle uyumu kontrol ediliyor. Aynı sorunun çözümü yeniden kullanılıyor. Adımlar ses bitince ilerliyor; eski veya kesilen sesin bildirimleri yeni adımı atlatmıyor. API hata verirse mevcut anlatım sürüyor. Bu kontrol matematiksel doğruluğun tam kanıtı değildir; öğretmen kontrolü önemlidir. Slayttaki işlemler temsili örnektir. Canlı ses ve API yanıtlarının cihaz üzerinde ayrıca denenmesi gerekir.

## 9. Zamanlama ve oturum kontrolü (35 sn)

Velinin seçtiği tarih ve saat task_schedules tablosunda tutuluyor. role_schedule Windows Görev Zamanlayıcısına XML tanımıyla görev ekliyor. Başlatma komutu uygulamaya schedule-id ile görev numarasını iletiyor. Uygulama açıksa zaman kontrolü de devrede. Başlatma anında durum pending iken started yapılması, aynı görevin birden fazla akış tarafından alınmasını azaltıyor. Windows oturumu ve bilgisayar açık olmalı. Serbest çalışma istediği zaman çıkışa izin veriyor. Planlı çalışmada öğrenme hedefi veya veli doğrulaması çıkış sağlıyor. Klavye ve pencere kontrolü yöneticiye karşı aşılamaz işletim sistemi güvenliği değildir.

## 10. Belge, ses ve el yazısı işleme (30 sn)

Öğretmenin PDF belgesinden pypdf ile metin çıkarılıyor. Word ve metin belgeleri de soru atölyesine kaynak olabiliyor. Kaynak içerik sınıf, ders ve kazanım bilgisiyle birlikte soru taslağı üretimine gönderiliyor. Öğretmen taslağı kontrol edip onaylayabiliyor. Metin katmanı olmayan taranmış PDF doğrudan metin çıkarımını sınırlayabilir. Ses için yerel Piper veya yapılandırılmış dış hizmet bağlantısı kullanılıyor. El yazısı alanında bir QTimer son çizimden sonra sekiz yüz elli milisaniyelik duraklamayı izliyor. Tanıma arka plan işçisi sonucunu arayüze gönderiyor. animated_story modülü açıklamayı animasyonlu sahneyle destekliyor. Burada bir dil modeli eğittiğimizi iddia etmiyoruz. Ses adımı oynatma tamamlandığında ilerler. Eski seslerin bekleyen bildirimleri engellenir. Gemini çözümü hazırlanırken mevcut anlatım durdurulmaz.

## 11. Güvenlik, tutarlılık ve testler (30 sn)

Veli ve öğretmen parolaları her hesap için ayrı rastgele tuz ve iki yüz bin yinelemeli PBKDF2-SHA256 ile özetleniyor. Doğrulamada hmac.compare_digest kullanılıyor. require_student gibi işlevler veri katmanında erişimi denetliyor. Hesaplarda başarısız giriş takibi bulunuyor. Basit öğrenci girişi güçlü kimlik doğrulama değildir. API anahtarı ortam ayarlarından okunuyor. Yerel SQLite dosyası kendiliğinden şifrelenmiş değildir. Son soru üretimi değişikliğinde yirmi beş seçili otomatik test geçti. Özellikle gösterilen soruyu koruma, tekrar eleme, ilerleme ve hata akışları test edildi. Modelin eğitim doğruluğunu veya ürünün tamamının hatasız olduğunu bu sayıdan çıkaramayız.

## 12. Tablet ve telefona entegre edecek olsak ne yapardık? (45 sn)

Telefon ve tablet için mevcut PyQt6 ekranlarını doğrudan taşımak yerine Flutter ve Dart ile Android ve iOS arayüzü hazırlamayı planlarız. Dokunmatik kullanım, tablet kalemi ve farklı ekran boyutlarına uyum sağlarız. Python iş mantığını bir sunucu API’si arkasında düzenler, hesapları, görevleri ve ilerlemeyi merkezi veritabanında eşitleriz. Gemini anahtarları mobil uygulamaya gömülmez; istekler yetkilendirilmiş sunucudan geçer. Planlı çalışmalar bildirimle hatırlatılır. Zorunlu ekran ve çıkış sınırlaması platforma bağlıdır: Android’de yönetilen cihaz ve kiosk, iOS’ta Guided Access veya cihaz yönetimi seçenekleri incelenir. Guided Access kullanıcının başlattığı bir oturumdur, uygulamanın kendiliğinden kilit açma yetkisi değildir. Windows davranışının her kişisel telefonda aynısını garanti etmeyiz. Bu bölüm uygulanmış özellik değil, geliştirme planıdır.

## 13. Çalışan prototipten ölçülebilir pilota (20 sn)

Prototipin rol ekranları, planlama, raporlama ve pekiştirme akışı hazır. Yazılım testleri bu davranışları sınar; çocuğun daha iyi öğrendiğini tek başına kanıtlamaz. Öğretmen denetimindeki pilotta konu başarısını, öğrenmenin kalıcılığını ve yapay zekâ sorularının doğruluğunu ölçmeyi planlıyoruz. Sonuçlara göre uygulamanın öğrenme ölçütlerini geliştireceğiz.