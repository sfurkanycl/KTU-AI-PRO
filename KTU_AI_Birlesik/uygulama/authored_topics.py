"""Original offline concept exercises. MEB supplies the topic list, not these questions.

Every group is explicit: unknown subjects/units fail rather than receiving unrelated
generic questions. Definitions are paired in both directions with distinct choices.
"""
import hashlib
import random

CONTENT = r'''
[school]
Söz almak|Konuşmadan önce parmak kaldırıp sıramızı beklemek.
Okul eşyalarını korumak|Sıramızı ve kitaplarımızı temiz kullanmak.
Ders hazırlığı|Ders için gerekli araçları çantamıza koymak.
Arkadaşlık|Arkadaşlarımızla saygılı ve nazik iletişim kurmak.
Okul kuralı|Okulda birlikte yaşamayı düzenleyen ortak davranış.
Yardım istemek|Zorlandığımız bir durumda öğretmenimize başvurmak.
[health]
El temizliği|Ellerimizi su ve sabunla yıkamak.
Dengeli beslenmek|Farklı besin gruplarından yeterli miktarda yemek.
Uyku düzeni|Yaşımıza uygun süre uyuyup dinlenmek.
Güvenli oyun|Araç trafiğinden uzak oyun alanını seçmek.
Kişisel sınır|Rahatsız olduğumuz bir davranışa hayır diyebilmek.
Güvenilir yetişkin|Bir sorun yaşadığımızda yardım isteyebileceğimiz öğretmen veya aile büyüğü.
[family]
İş bölümü|Evdeki işleri aile üyeleri arasında paylaşmak.
Dayanışma|Bir zorluğu aşmak için birbirimize destek olmak.
Aile içi iletişim|Duygularımızı ailemize saygıyla anlatmak.
Ev sorumluluğu|Kendi oyuncaklarımızı toplamak gibi yapabileceğimiz bir işi üstlenmek.
Komşuluk|Yakınımızda yaşayan insanlarla saygılı ilişkiler kurmak.
Ortak karar|Bir konuyu birlikte konuşarak karara bağlamak.
[country]
Başkent|Türkiye için Ankara olan, ülkenin yönetim merkezinin bulunduğu şehir.
Millî bayrak|Türkiye'de üzerinde beyaz ay ve yıldız bulunan kırmızı bayrak.
İstiklâl Marşı|Türkiye'nin millî marşı.
Cumhuriyet Bayramı|Her yıl 29 Ekim'de kutladığımız millî bayram.
23 Nisan|Ulusal Egemenlik ve Çocuk Bayramı'nın kutlandığı gün.
Adres|Yaşadığımız yerin bulunmasını sağlayan mahalle, sokak ve bina bilgileri.
[environment]
Geri dönüşüm|Uygun atıkların işlenerek yeniden kullanılabilir malzemeye dönüştürülmesi.
Su tasarrufu|İhtiyacımız olmayan zamanlarda musluğu kapatmak.
Ağaçları korumak|Ağaçların dallarını kırmamak ve onlara zarar vermemek.
Çöp kutusu|Geri dönüştürülemeyen günlük çöpleri çevreye atmadan biriktirdiğimiz yer.
Enerji tasarrufu|Kullanmadığımız odanın ışığını kapatmak.
Doğal yaşam alanı|Canlıların doğada yaşayıp ihtiyaçlarını karşıladığı yer.
[technology]
İcat|Bir ihtiyacı karşılayan yeni bir araç veya yöntem geliştirmek.
Gözlem|Bir varlığı veya olayı dikkatle incelemek.
Teknolojik araç|İnsanların işlerini kolaylaştırmak için geliştirilmiş araç.
Güvenli internet|Kişisel bilgilerimizi yabancılarla paylaşmadan internet kullanmak.
Sanat|Duygu ve düşüncelerimizi resim, müzik gibi yollarla ifade etmek.
Tasarruflu kullanım|Bir aracı gerektiği kadar kullanıp gereksiz tüketimden kaçınmak.
[science_method]
Araştırma sorusu|Bir araştırmada cevap aradığımız soru.
Tahmin|Bir olayın sonucu hakkında önceden düşündüğümüz olasılık.
Gözlem|Bir olayı dikkatle inceleyerek bilgi toplamak.
Deney|Bir fikri kontrollü bir çalışma yaparak sınamak.
Veri|Araştırma sırasında topladığımız bilgi ve ölçümler.
Sonuç|Toplanan bilgilere bakarak araştırma sorusuna verdiğimiz cevap.
[living]
Bitki|Uygun koşullarda büyüyen, kök ve yaprak gibi bölümleri bulunabilen canlı.
Hayvan|Besinini başka canlılardan sağlayan, bitki olmayan canlı grubu.
Su ihtiyacı|Canlıların yaşamlarını sürdürebilmek için suya gereksinim duyması.
Büyüme|Bir canlının zamanla boyutunun veya kütlesinin artması.
Beslenme|Bir canlının yaşamı için gerekli besinleri alması.
Cansız varlık|Taş gibi büyüme ve beslenme özellikleri göstermeyen varlık.
[earth3]
Kayaç|Yer kabuğunda bulunan, bir veya daha fazla mineralden oluşan doğal madde.
Toprak|Bitkilerin kök salabildiği, yeryüzünü örten gevşek tabaka.
Fosil|Geçmişte yaşamış canlıların korunmuş kalıntı veya izleri.
Kara|Yeryüzünün deniz ve göl gibi sularla kaplı olmayan bölümü.
Su katmanı|Yeryüzündeki okyanus, deniz, göl ve akarsu gibi suların oluşturduğu bölüm.
Hava katmanı|Dünya'yı çevreleyen gazlardan oluşan bölüm.
[matter3]
Katı|Belirli şekli olan madde hâli.
Sıvı|Konulduğu kabın şeklini alan, akabilen madde hâli.
Gaz|Bulunduğu kabın her tarafına yayılabilen madde hâli.
Karışım|Birden fazla maddenin bir araya gelmesi.
Eleme|Farklı büyüklükteki katı parçaları elek yardımıyla ayırma.
Süzme|Suda çözünmemiş katı parçaları uygun bir süzgeçle sıvıdan ayırma.
[motion]
İtme|Bir cismi kendimizden uzağa doğru kuvvet uygulayarak hareket ettirme.
Çekme|Bir cismi kendimize doğru kuvvet uygulayarak hareket ettirme.
Hızlanma|Bir cismin hareket süratinin artması.
Yavaşlama|Bir cismin hareket süratinin azalması.
Yön değiştirme|Hareket eden cismin başka bir yöne dönmesi.
Sallanma|Bir cismin bir konumun iki yanına gidip gelmesi.
[electricity]
Pil|Basit bir devrede elektrik enerjisi sağlayan kaynak.
Ampul|Uygun bir devrede elektrik enerjisini ışığa dönüştüren araç.
Bağlantı kablosu|Devrede elektriksel bağlantıyı sağlayan parça.
Anahtar|Devreyi açıp kapatmak için kullanılan parça.
Kapalı devre|Elektriğin izlediği yolun kesintisiz olduğu devre.
Elektrik güvenliği|Prizlere yabancı cisim sokmamak ve elektrikli araçları ıslak elle tutmamak.
[soil]
Verimli toprak|Bitkilerin büyümesi için uygun koşullar sağlayan toprak.
Tohum|Uygun koşullarda yeni bir bitkinin gelişebildiği yapı.
Çimlenme|Bir tohumdan yeni bitkinin gelişmeye başlaması.
Sulama|Yetiştirilen bitkinin su ihtiyacını karşılamak.
Tarım|Toprağı işleyerek bitkisel ürün yetiştirme faaliyeti.
Erozyon|Toprağın su veya rüzgâr gibi etkenlerle taşınması.
[habitat]
Orman|Çok sayıda ağacın ve başka canlıların bir arada yaşadığı alan.
Göl|Karalar içindeki bir çukurda birikmiş su alanı.
Çöl|Yağışın çok az olduğu doğal yaşam alanı.
Kutup bölgesi|Yılın büyük bölümünde çok soğuk olan, kutuplar çevresindeki alan.
Yaşam alanını korumak|Canlıların yaşadığı yerlere çöp atmamak ve zarar vermemek.
Yaşam alanı ihtiyacı|Bir canlının besin, su ve barınma bulabileceği ortama gereksinimi.
[earth4]
Yer kabuğu|Dünya'nın üzerinde yaşadığımız dış katmanı.
Kayaç|Yer kabuğunu oluşturan, minerallerden meydana gelen doğal madde.
Fosil|Geçmişte yaşayan canlıların korunmuş kalıntı veya izleri.
Dönme hareketi|Dünya'nın kendi ekseni etrafında yaptığı hareket.
Dolanma hareketi|Dünya'nın Güneş'in çevresinde yaptığı hareket.
Gece ve gündüz|Dünya'nın kendi ekseni etrafında dönmesiyle oluşan zaman bölümleri.
[nutrition]
Karbonhidrat|Vücudumuzun başlıca enerji kaynaklarından olan besin içeriği.
Protein|Büyüme ve vücuttaki onarımda görev alan besin içeriği.
Vitamin|Vücudun düzenli çalışmasına yardımcı olan besin içeriği.
Su|Vücudumuzdaki birçok yaşamsal olay için gerekli sıvı.
Dengeli beslenme|Besin gruplarından ihtiyacımıza uygun miktarlarda tüketmek.
Son tüketim tarihi|Ambalajlı gıdada güvenli tüketim açısından kontrol edilen tarih.
[force4]
Kuvvet|Cisimlerin hareketini veya şeklini değiştirebilen etki.
Mıknatıs|Demir gibi bazı maddeleri kendine çekebilen nesne.
Mıknatısın kutupları|Mıknatısta kuzey ve güney olarak adlandırılan uçlar.
Şekil değişikliği|Süngeri sıkmak gibi bir cismin biçiminin değişmesi.
İtme kuvveti|Bir kapıyı kendimizden uzağa doğru açarken uyguladığımız kuvvet.
Çekme kuvveti|Bir çekmeceyi kendimize doğru açarken uyguladığımız kuvvet.
[matter4]
Kütle|Maddenin miktarıyla ilgili, gram veya kilogramla ölçülen büyüklük.
Hacim|Bir maddenin uzayda kapladığı yer.
Erime|Katı maddenin ısı alarak sıvı hâle geçmesi.
Donma|Sıvı maddenin ısı vererek katı hâle geçmesi.
Buharlaşma|Sıvı maddenin gaz hâle geçmesi.
Çözünme|Şekerin su içinde dağılması gibi, bir maddenin başka bir madde içinde homojen karışım oluşturması.
[light_sound]
Doğal ışık kaynağı|Güneş gibi insanlar tarafından yapılmamış ışık kaynağı.
Yapay ışık kaynağı|Lamba gibi insanlar tarafından yapılmış ışık kaynağı.
Işık kirliliği|Işığın yanlış yerde, miktarda veya zamanda kullanılması.
Ses kirliliği|İnsanları ve diğer canlıları rahatsız eden aşırı veya düzensiz sesler.
Mikrofon|Sesin elektriksel sinyale dönüştürülmesinde kullanılan araç.
Hoparlör|Elektriksel sinyalleri sese dönüştüren araç.
[social_person]
Kimlik belgesi|Kişiye ait resmî kimlik bilgilerini gösteren belge.
Bireysel farklılık|İnsanların ilgi, yetenek ve özelliklerinin birbirinden farklı olması.
Empati|Kendimizi bir başkasının yerine koyarak onun duygularını anlamaya çalışmak.
Kronoloji|Olayları gerçekleşme zamanlarına göre sıralama.
İlgi|Bir etkinliğe veya konuya yönelme ve onu merak etme.
Yetenek|Bir işi yapmada sahip olduğumuz ve geliştirebildiğimiz beceri.
[culture]
Gelenek|Bir toplumda kuşaktan kuşağa aktarılan davranış veya uygulama.
Kültürel miras|Geçmişten günümüze ulaşan maddi ve manevi değerler.
Tarihî eser|Geçmiş dönemlerden kalmış, tarih açısından değer taşıyan yapı veya nesne.
Sözlü tarih|Geçmiş hakkında kişilerin anlattıklarından bilgi toplama yöntemi.
Millî bayram|Bir ülke için önemli olayların yıldönümünde kutlanan bayram.
Geleneksel oyun|Bir toplumda uzun zamandır oynanan ve kuşaklara aktarılan oyun.
[places]
Kroki|Bir yerin kuş bakışı görünümünün kabaca çizimi.
Harita|Yeryüzünün tamamının veya bir bölümünün belirli ölçüde küçültülmüş gösterimi.
Pusula|Yön bulmaya yardımcı olan, iğnesi yaklaşık kuzey-güney doğrultusunu gösteren araç.
Doğal unsur|Dağ veya akarsu gibi insanlar tarafından yapılmamış çevre ögesi.
Beşerî unsur|Yol veya köprü gibi insanlar tarafından yapılmış çevre ögesi.
Hava durumu|Bir yerde kısa süre içinde gözlenen yağış ve sıcaklık gibi hava olayları.
[social_tech]
İhtiyaç|Yaşamımızı sürdürmek veya temel gereksinimlerimizi karşılamak için gerekli olan şey.
İcat|Daha önce bulunmayan bir araç veya yöntemin geliştirilmesi.
Mucit|Bir icadı geliştiren kişi.
Teknolojik değişim|Kullanılan araçların zaman içinde geliştirilmesi.
Güvenli kullanım|Bir teknolojik aracı kullanım kurallarına uyarak çalıştırmak.
Dijital gizlilik|Kişisel bilgileri ve şifreleri başkalarıyla paylaşmadan korumak.
[economy]
Üretim|Bir mal veya hizmet ortaya koyma işi.
Dağıtım|Üretilen malın kullanılacağı veya satılacağı yere ulaştırılması.
Tüketim|Bir mal veya hizmetten yararlanma.
Bütçe|Gelir ve giderleri planlamak için hazırlanan düzenleme.
Tasarruf|Kaynakları gereksiz harcamadan, bir bölümünü ilerisi için ayırmak.
Bilinçli tüketici|Ürünün ihtiyacına, fiyatına ve özelliklerine bakarak alışveriş yapan kişi.
[citizen]
Hak|İnsanın yararlanabileceği, kurallarla güvence altına alınan olanak.
Sorumluluk|Üstlendiğimiz görevleri yerine getirme yükümlülüğü.
Katılım|Ortak bir konuda görüş belirterek veya çalışarak sürece dâhil olmak.
Egemenlik|Devlet yönetiminde karar verme yetkisi.
TBMM|Türkiye Büyük Millet Meclisinin kısaltması.
Dilekçe|Bir isteği veya şikâyeti ilgili kuruma yazıyla iletme yolu.
[global]
Ülke|Kendine ait yönetimi ve sınırları bulunan siyasi birim.
Kültürel farklılık|Toplumların dil, yemek veya geleneklerinin farklı olması.
Saygı|İnsanların farklı yaşam biçimlerini küçümsemeden kabul etmek.
Uluslararası iletişim|Farklı ülkelerdeki insanlar arasında haberleşme.
Ortak miras|Farklı toplumların da değer verdiği insanlık birikimi.
Turizm|İnsanların gezmek ve tanımak gibi amaçlarla farklı yerlere gitmesi.
[art_life]
Resim|Duygu ve düşünceleri çizgi ve renklerle anlatma yolu.
Heykel|Taş, kil veya başka malzemelerle oluşturulan üç boyutlu sanat eseri.
Sanatçı|Sanat eserleri üreten kişi.
İlham|Bir sanat çalışmasını başlatan duygu veya düşünce.
Gözlem|Çizmek istediğimiz nesneyi dikkatle incelemek.
Özgünlük|Çalışmamızda kendi düşünce ve anlatımımıza yer vermek.
[art_language]
Çizgi|Bir noktanın hareketiyle oluştuğu düşünülen görsel iz.
Nokta|Görsel anlatımdaki en küçük temel iz.
Biçim|Bir varlığın dış görünüşünü oluşturan şekil.
Doku|Bir yüzeyin pürüzlü veya düzgün gibi özellikleri.
Renk|Kırmızı, sarı veya mavi gibi görsel özellik.
Kompozisyon|Bir resimdeki ögelerin bir bütün oluşturacak şekilde düzenlenmesi.
[artists]
Ressam|Resim yapan sanatçı.
Heykeltıraş|Heykel yapan sanatçı.
Eser adı|Bir sanat çalışmasına verilen isim.
İmza|Sanatçının eser üzerinde kendini belirten işareti veya yazısı.
Sergi|Sanat eserlerinin izleyicilerle buluştuğu düzenleme.
Emeğe saygı|Başkasının eserini kendimiz yapmış gibi göstermemek.
[drawing]
Eskiz|Bir çalışma öncesinde yapılan hızlı taslak çizim.
Ön plan|Resimde izleyiciye daha yakın görünen bölüm.
Arka plan|Resimde daha uzakta görünen bölüm.
Portre|Bir kişinin yüzünü veya görünümünü konu alan resim.
Manzara|Doğal veya yerleşim alanlarının görünümünü konu alan resim.
Görsel anlatım|Duygu ve düşünceleri çizim ve görüntülerle aktarmak.
[color]
Kırmızı|Geleneksel resim eğitiminde sarı ve maviyle birlikte ana renk kabul edilen renklerden biri.
Turuncu|Kırmızı ve sarı boyalar karıştırıldığında elde edilen renk.
Yeşil|Sarı ve mavi boyalar karıştırıldığında elde edilen renk.
Mor|Kırmızı ve mavi boyalar karıştırıldığında elde edilen renk.
Sıcak renkler|Kırmızı, turuncu ve sarının oluşturduğu renk grubu.
Soğuk renkler|Mavi, yeşil ve morun oluşturduğu renk grubu.
[art_national]
Bayrak resmi|Ay ve yıldız gibi millî sembolleri konu alan görsel çalışma.
Ebru|Su yüzeyinde boyalarla desen oluşturup kâğıda aktarma sanatı.
Çini|Seramik yüzeylerde desen ve renklerle yapılan geleneksel süsleme.
Kilim|Çeşitli motiflerle dokunan geleneksel yaygı.
Motif|Süslemede tekrarlanabilen küçük desen ögesi.
Kültürü korumak|Geleneksel sanatları öğrenmek ve değer vermek.
[museum]
Müze|Tarih, sanat veya bilimle ilgili eserlerin korunup sergilendiği yer.
Müze etiketi|Sergilenen eser hakkında kısa bilgi veren yazı.
Eseri korumak|Sergilenen nesnelere izin verilmeden dokunmamak.
Kültürel miras|Geçmişten gelen, korunup geleceğe aktarılacak değerler.
Rehber|Gezilen yer hakkında bilgi veren kişi.
Tarihî yapı|Geçmiş dönemlerden günümüze ulaşmış yapı.
[art_criticism]
Betimleme|Bir eserde gördüğümüz çizgi, renk ve biçimleri anlatmak.
Yorumlama|Bir eserin bize düşündürdüklerini veya hissettirdiklerini söylemek.
Estetik|Güzellik ve sanatla ilgili düşünme alanı.
Saygılı değerlendirme|Bir eseri incelerken sanatçıyı küçümsemeden görüş belirtmek.
Karşılaştırma|İki eserin benzer ve farklı yönlerini incelemek.
Kişisel beğeni|Bir eseri kendi duygu ve düşüncelerimize göre sevmemiz.
[music_language]
Ritim|Seslerin ve sessizliklerin zaman içindeki düzeni.
Melodi|Birbirini izleyen seslerin oluşturduğu ezgi.
Nota|Müzik seslerini yazıyla gösteren işaret.
Sus işareti|Müzikte sessiz kalınacak süreyi gösteren işaret.
Tempo|Bir müzik parçasının çalınma veya söylenme hızı.
Gürlük|Bir sesin güçlü veya hafif duyulma özelliği.
[music_culture]
Türkü|Halk kültüründe gelişmiş, sözlü bir müzik türü.
Ninni|Bebeği uyutmak için genellikle yumuşak sesle söylenen ezgi.
Marş|Genellikle belirgin ritmi olan, topluca da söylenebilen müzik türü.
Bağlama|Tellerine vurularak veya telleri çekilerek çalınan geleneksel çalgı.
Koro|Birlikte şarkı söyleyen topluluk.
Konser|Müziğin dinleyiciler önünde seslendirildiği etkinlik.
[music_singing]
Birlikte söyleme|Bir şarkıyı aynı başlangıç ve ritme uyarak topluca seslendirmek.
Dinleme|Müzik çalınırken seslere dikkatini vermek.
Nefes hazırlığı|Şarkıya başlamadan önce rahat bir biçimde nefes almak.
Bağırmadan söyleme|Sesimizi zorlamadan şarkı söylemek.
Başlangıç işareti|Birlikte müziğe ne zaman girileceğini gösteren işaret.
Dinleyici saygısı|Bir gösteri sırasında konuşarak veya gürültü yaparak müziği bölmemek.
[music_creative]
Ritim oluşturma|El çırpma gibi seslerle kendi zaman düzenimizi kurmak.
Ezgi oluşturma|Sesleri bir araya getirerek kısa bir müzik cümlesi kurmak.
Doğaçlama|O anda düşündüğümüz ses veya hareketlerle müzik yapmak.
Bedensel vurmalı|El çırpma veya dize hafif vurma gibi bedenle ritim üretme.
Ses denemesi|Güvenli nesnelerin çıkardığı farklı sesleri araştırmak.
Birlikte üretme|Arkadaşlarımızla ortak bir müzik çalışması hazırlamak.
[pe_move]
Yürüme|Adımlayarak, koşmadan yer değiştirme hareketi.
Koşma|Yürümeye göre daha hızlı, adımlar arasında kısa uçuş bulunan hareket.
Sıçrama|Ayaklarla yerden kuvvet alıp yükselme hareketi.
Denge|Vücudun konumunu kontrollü biçimde koruyabilme.
Koordinasyon|Vücudun farklı bölümlerini uyum içinde kullanma.
Isınma|Asıl etkinlikten önce vücudu hafif hareketlerle hazırlama.
[pe_rules]
Oyun kuralı|Bir oyunun nasıl oynanacağını belirleyen ortak ilke.
Adil oyun|Kurallara uyarak dürüstçe oynamak.
Sıra bekleme|Oyundaki hakkımız gelene kadar sabırla beklemek.
İş birliği|Ortak hedef için takım arkadaşlarıyla birlikte çalışmak.
Saygılı yarışma|Kazananı kutlamak ve kaybedeni küçümsememek.
Güvenli alan|Engel ve tehlikelerden uzak, etkinliğe uygun oyun yeri.
[pe_rhythm]
Ritme uyma|Hareketleri duyulan vuruş düzenine uygun yapmak.
Hızlı tempo|Vuruşların kısa aralıklarla geldiği düzen.
Yavaş tempo|Vuruşların daha uzun aralıklarla geldiği düzen.
El çırpma|İki eli birbirine vurarak ritim oluşturma.
Hareket dizisi|Belirli sırayla yapılan birden fazla hareket.
Uyum|Grubun hareketlerini birlikte ve aynı düzene göre yapması.
[pe_health]
Düzenli hareket|Yaşa ve koşullara uygun fiziksel etkinlikleri alışkanlık hâline getirmek.
Dinlenme|Yorulduğumuzda vücudumuza toparlanma zamanı vermek.
Su içme|Hareket sırasında ve sonrasında su ihtiyacımızı karşılamak.
Uygun kıyafet|Etkinlikte rahat ve güvenli hareket etmeye uygun giysi seçmek.
Dengeli beslenme|Farklı besin gruplarını ihtiyacımız kadar tüketmek.
Kişisel temizlik|Etkinlikten sonra ellerimizi yıkamak ve gerektiğinde temizlenmek.
[pe_nature]
Doğa yürüyüşü|Doğal bir çevrede güvenli bir güzergâhta yürümek.
Çevreyi koruma|Etkinlik alanında çöp bırakmamak ve canlılara zarar vermemek.
Grup güvenliği|Açık alanda öğretmenimizin belirlediği gruptan ayrılmamak.
Rota|Bir yürüyüşte izlenmesi planlanan yol.
Uygun hazırlık|Etkinlik öncesinde hava durumuna ve alana uygun araçları seçmek.
Gözlem|Yürüyüş sırasında çevredeki canlıları rahatsız etmeden incelemek.
[pe_traditional]
Geleneksel oyun|Kuşaktan kuşağa aktarılarak oynanan oyun.
Mendil kapmaca|Oyuncuların ortadaki mendili alıp kendi tarafına dönmeye çalıştığı oyun.
Seksek|Yere çizilen bölmelerde belirli kurallarla sıçrayarak oynanan oyun.
Saklambaç|Bir ebenin saklanan oyuncuları bulmaya çalıştığı oyun.
Oyun kültürü|Bir toplumda öğrenilip paylaşılan oyun alışkanlıkları.
Kurala saygı|Geleneksel bir oyunu oynarken kararlaştırılan ilkelere uymak.
[pe_world]
Dünya çocuk oyunları|Farklı ülkelerde çocukların oynadığı oyunlar.
Kültür tanıma|Başka toplumların oyun ve alışkanlıklarını öğrenmek.
Ortak oyun|Farklı diller konuşan çocukların da birlikte katılabildiği etkinlik.
Farklılığa saygı|Başka bir ülkenin oyununu küçümsemeden öğrenmek.
Kural paylaşımı|Yeni bir oyunun nasıl oynandığını arkadaşlara açıklamak.
Dayanışma|Oyun sırasında yardıma ihtiyaç duyan arkadaşımıza destek olmak.
[pe_inclusion]
Kapsayıcı oyun|Farklı ihtiyaçları olan çocukların da katılabileceği oyun.
Uyarlama|Bir oyunun araç veya kurallarını katılımı kolaylaştıracak şekilde değiştirmek.
Eşit katılım|Herkese etkinliğe katılma fırsatı vermek.
Destek olma|Bir arkadaşın ihtiyacını sorarak ona uygun biçimde yardım etmek.
Farklılığa saygı|İnsanları bedensel özellikleri nedeniyle dışlamamak.
Takım dayanışması|Takımdaki herkesin birlikte başarı için birbirine destek olması.
[religion_words]
Besmele|Bir işe başlarken Allah'ın adıyla başlamayı ifade eden söz.
Elhamdülillah|Allah'a şükretmeyi ifade eden söz.
İnşallah|Bir işin Allah dilerse olacağını belirtmek için kullanılan söz.
Maşallah|Beğenilen bir şey karşısında iyi dileği ifade eden söz.
Selamlaşma|Karşılaştığımız kişiye iyi dilek bildiren bir söz söylemek.
Dua|Allah'a yönelerek dileklerimizi ve teşekkürümüzü ifade etmek.
[islam]
İman|İslam dininde inanmayı ifade eden kavram.
İbadet|Allah'a kulluk amacıyla yapılan davranışlar.
Namaz|İslam'da belirli vakitlerde yerine getirilen ibadet.
Oruç|İslam'da imsak ile iftar arasında yeme içmeden ve orucu bozan davranışlardan uzak durma ibadeti.
Zekât|Şartlarını taşıyan Müslümanın malından belirli payı ihtiyaç sahiplerine verme ibadeti.
Hac|Şartlarını taşıyan Müslümanın belirli zamanda Kâbe ve çevresinde yaptığı ibadet.
[morals]
Dürüstlük|Doğruyu söylemek ve insanları aldatmamak.
Yardımseverlik|İhtiyacı olan birine gücümüz ölçüsünde destek olmak.
Sabır|Bir zorluk karşısında hemen vazgeçmeden dayanabilmek.
Saygı|İnsanların haklarını ve duygularını önemsemek.
Adalet|İnsanlara haklarını gözeterek davranmak.
Sorumluluk|Üstlendiğimiz işleri zamanında ve özenle yerine getirmek.
[prophet]
Mekke|Hz. Muhammed'in doğduğu şehir.
Medine|Hz. Muhammed'in hicret ettiği şehir.
Âmine|Hz. Muhammed'in annesinin adı.
Abdullah|Hz. Muhammed'in babasının adı.
El-Emin|Hz. Muhammed'in güvenilirliğini ifade eden unvan.
Merhamet|Hz. Muhammed'in de öğütlediği, canlılara şefkatle davranma özelliği.
[religion_clean]
Beden temizliği|Vücudumuzu temiz tutmak için yıkanmak gibi davranışlar.
Giysi temizliği|Kıyafetlerimizin temiz olmasına özen göstermek.
Çevre temizliği|Yaşadığımız ortak alanları kirletmemek.
Abdest|İslam'da belirli ibadetler öncesinde belirli organları usulüne uygun yıkama veya mesh etme hazırlığı.
Güzel söz|İnsanları kırmadan nazik ifadeler kullanmak.
Temiz alışkanlık|Tuvaletten sonra ve yemekten önce elleri yıkamak.
[human]
İnsan onuru|Her insanın yalnızca insan olduğu için sahip olduğu değer.
Eşitlik|İnsanların temel haklar bakımından aynı değerde olması.
Empati|Başkasının duygularını onun bakış açısından anlamaya çalışmak.
Özgürlük|Başkalarının haklarına saygı duyarak seçim yapabilmek.
Saygı|İnsanların haklarını ve farklılıklarını gözetmek.
Farklılık|İnsanların ilgi, özellik ve düşüncelerinin birbirinden ayrı olması.
[rights]
Eğitim hakkı|Her çocuğun öğrenim görme hakkı.
Oyun hakkı|Çocukların dinlenme ve yaşlarına uygun oyunlara katılma hakkı.
Sorumluluk|Kendi görevlerini yerine getirme yükümlülüğü.
İfade özgürlüğü|Düşüncelerimizi başkalarının haklarına saygı duyarak açıklayabilmek.
Sağlık hakkı|Sağlığı koruyan hizmetlerden yararlanma hakkı.
Haklara saygı|Kendi hakkımızı kullanırken başkasının hakkını engellememek.
[justice]
Adalet|Herkesin hakkını ve ihtiyacını gözeterek davranmak.
Eşitlik|Temel hakları bakımından herkesi aynı değerde görmek.
Ayrımcılık|Bir kişiyi kimliği veya özellikleri nedeniyle haksız biçimde dışlamak.
Tarafsızlık|Bir kararda kişisel yakınlığa göre taraf tutmamak.
Hakkaniyet|Bir durumun koşullarını ve kişilerin ihtiyaçlarını dikkate almak.
Adil paylaşım|Ortak kaynakları hakları ve ihtiyaçları gözeterek bölüştürmek.
[consensus]
Uzlaşı|Farklı görüşleri konuşarak ortak bir çözüme varmak.
Dinleme|Bir kişinin sözünü kesmeden onu anlamaya çalışmak.
Görüş|Bir konu hakkında düşündüğümüz fikir.
Gerekçe|Bir düşünceyi savunurken sunduğumuz neden.
Ortak çözüm|Tarafların ihtiyaçlarını dikkate alan çözüm yolu.
Saygılı konuşma|Farklı düşündüğümüzde bile kırıcı sözlerden kaçınmak.
[rules]
Kural|Birlikte yaşamı düzenleyen ilke.
Yazılı kural|Metin hâlinde belirtilmiş kural.
Yazılı olmayan kural|Gelenek veya görgü yoluyla öğrenilen kural.
Kurala katılım|Ortak kurallar belirlenirken görüşümüzü söylemek.
Kurala uyma|Kararlaştırılmış ilkelere göre davranmak.
Kuralı değerlendirme|Bir kuralın adil ve yararlı olup olmadığını düşünmek.
[together]
Dayanışma|Bir sorunu aşmak için birbirimize destek olmak.
İş birliği|Ortak bir iş için görevleri paylaşarak çalışmak.
Hoşgörü|Farklı görüş ve alışkanlıkları saygıyla karşılamak.
Ortak alan|Herkesin birlikte kullandığı park veya okul bahçesi gibi yer.
Barışçıl çözüm|Sorunları şiddet kullanmadan konuşarak çözmek.
Birlikte yaşama|Aynı toplumda hak ve sorumlulukları gözeterek yaşamını sürdürmek.
[traffic]
Yaya|Trafikte yürüyerek ilerleyen kişi.
Yaya geçidi|Yayaların karşıya geçişi için işaretlenmiş yol bölümü.
Kaldırım|Yolun yayaların yürümesi için ayrılmış bölümü.
Emniyet kemeri|Araç içinde uygun biçimde takılarak güvenliği artıran araç.
Trafik ışığı|Yol kullanıcılarına durma veya geçiş durumunu bildiren ışıklı işaret.
Bisiklet kaskı|Bisiklet kullanırken başı korumaya yardımcı güvenlik donanımı.
[first_aid]
112|Türkiye'de acil yardım için aranan telefon numarası.
Konum bilgisi|Acil yardım isterken olayın nerede olduğunu anlatan bilgi.
Güvenilir yetişkin|Bir kaza gördüğümüzde hemen haber verebileceğimiz öğretmen veya aile büyüğü.
Güvenli mesafe|Kaza yerindeki trafik veya başka tehlikelerden uzak durmayı sağlayan uzaklık.
Sakin iletişim|Yardım isterken bağırmadan, anlaşılır bilgi vermek.
İlk yardım eğitimi|Doğru ilk yardım uygulamalarını yetkili kişilerden öğrenme süreci.
'''


def _parse():
    groups = {}; current = None
    for line in CONTENT.strip().splitlines():
        if line.startswith('['):
            current = line[1:-1]; groups[current] = []
        else:
            term, definition = line.split('|', 1)
            groups[current].append((term, definition))
    return groups


GROUPS = _parse()


def question(topic, text, correct, alternatives, explanation, concept, visual=None):
    choices = [str(correct)] + [str(x) for x in alternatives if str(x) != str(correct)]
    choices = list(dict.fromkeys(choices))[:4]
    if len(choices) != 4:
        raise ValueError(f'Dört farklı seçenek gerekli: {text}')
    seed = hashlib.sha256((topic['skill'] + text).encode()).hexdigest()
    random.Random(seed).shuffle(choices)
    return dict(skill=topic['skill'], text=text, choices=choices, answer=choices.index(str(correct)),
        hint='Sorudaki bilgileri ve seçenekleri tek tek karşılaştır.', explanation=explanation,
        visual=visual, concept=concept, source='authored-curriculum', verified=True,
        qkey=seed, curriculum=dict(grade=topic['grade'], subject=topic['subject'],
        title=topic['title'], source=topic['url']))


def concept_bank(topic, group):
    pairs = GROUPS[group]; result = []
    for i, (term, definition) in enumerate(pairs):
        others = [p for j, p in enumerate(pairs) if j != i]
        explanation = f'{term}: {definition}'
        result.append(question(topic, f'“{term}” için doğru açıklama hangisidir?', definition,
            [p[1] for p in others], explanation, group))
        result.append(question(topic, f'“{definition}”\nBu açıklama hangisine aittir?', term,
            [p[0] for p in others], explanation, group))
    return result


def group_for(topic):
    subject, i, grade = topic['subject'], topic['unit_index'], topic['grade']
    if subject == 'Hayat Bilgisi': return ['school','health','family','country','environment','technology'][i]
    if subject == 'Fen Bilimleri':
        return (['science_method','living','earth3','matter3','motion','electricity','soil','habitat'] if grade == 3 else
                ['earth4','nutrition','force4','matter4','light_sound','environment','electricity'])[i]
    if subject == 'Sosyal Bilgiler': return ['social_person','culture','places','social_tech','economy','citizen','global'][i]
    if subject == 'Görsel Sanatlar':
        return (['art_life','art_language','artists','drawing','color','art_national','museum'] if grade < 3 else
                ['art_language','museum','art_criticism'])[i]
    if subject == 'Müzik':
        return (['music_language','music_culture'] if grade < 3 else
                ['music_singing','music_culture','music_language','music_creative'])[i]
    if subject == 'Beden Eğitimi ve Oyun':
        return (['pe_move','pe_rules','pe_rhythm','pe_health'] if grade < 3 else
                ['pe_rules','pe_rules','pe_rhythm','pe_health','pe_nature','pe_traditional'] if grade == 3 else
                ['pe_move','pe_world','pe_rhythm','pe_health','pe_nature','pe_inclusion'])[i]
    if subject == 'Din Kültürü ve Ahlak Bilgisi': return ['religion_words','islam','morals','prophet','religion_clean'][i]
    if subject == 'İnsan Hakları, Vatandaşlık ve Demokrasi': return ['human','rights','justice','consensus','rules','together'][i]
    if subject == 'Trafik Güvenliği': return ['traffic','first_aid'][i]
    raise ValueError(f'Eşleştirilmemiş konu: {grade} {subject} {topic["title"]}')


# Short original passages, not excerpts from textbooks. Each row contains the
# passage and four unambiguous answers: person, place, object and purpose.
STORIES = {
 'values': [
  ('Ada, sınıfta arkadaşına bir kalem verdi. Arkadaşının yazı yazmasına yardım etmek istedi.', 'Ada','sınıf','kalem','Arkadaşına yardım etmek'),
  ('Ali, parkta bulduğu çantayı görevliye teslim etti. Çantanın sahibine ulaşmasını istedi.', 'Ali','park','çanta','Çantanın sahibine ulaşmasını sağlamak'),
  ('Ece, okul bahçesinde arkadaşına bir şemsiye uzattı. Arkadaşını yağmurdan korumak istedi.', 'Ece','okul bahçesi','şemsiye','Arkadaşını yağmurdan korumak')],
 'ataturk': [
  ('Elif, sınıfta 23 Nisan için bir şiir okudu. Çocuk Bayramı sevincini arkadaşlarıyla paylaşmak istedi.', 'Elif','sınıf','şiir','Çocuk Bayramı sevincini paylaşmak'),
  ('Can, okul bahçesinde 29 Ekim için bir bayrak taşıdı. Cumhuriyet Bayramı kutlamasına katılmak istedi.', 'Can','okul bahçesi','bayrak','Cumhuriyet Bayramı kutlamasına katılmak'),
  ('Duru, kütüphanede Atatürk hakkında bir kitap okudu. Atatürk hakkında bilgi edinmek istedi.', 'Duru','kütüphane','kitap','Atatürk hakkında bilgi edinmek')],
 'nature': [
  ('Ece, okul bahçesinde bir fidan dikti. Bahçenin daha yeşil olmasını istedi.', 'Ece','okul bahçesi','fidan','Bahçeyi yeşillendirmek'),
  ('Aras, parkta bir çöp torbası taşıdı. Yerdeki çöpleri toplayarak çevreyi temizlemek istedi.', 'Aras','park','çöp torbası','Çevreyi temizlemek'),
  ('Defne, evde bir saksı hazırladı. Yeni çiçeğini uygun bir yere dikmek istedi.', 'Defne','ev','saksı','Çiçeğini dikmek')],
 'books': [
  ('Ada, kütüphanede bir masal kitabı seçti. Yeni bir öykü okumak istedi.', 'Ada','kütüphane','masal kitabı','Yeni bir öykü okumak'),
  ('Emir, sınıfta bir sözlük kullandı. Bilmediği sözcüğün anlamını öğrenmek istedi.', 'Emir','sınıf','sözlük','Bir sözcüğün anlamını öğrenmek'),
  ('İpek, evde bir ayraç yaptı. Okuduğu sayfayı kolayca bulmak istedi.', 'İpek','ev','ayraç','Okuduğu sayfayı kolayca bulmak')],
 'talent': [
  ('Zeynep, sınıfta bir resim çizdi. Hayalindeki bahçeyi renklerle anlatmak istedi.', 'Zeynep','sınıf','resim','Hayalindeki bahçeyi anlatmak'),
  ('Ali, müzik odasında bir flüt çaldı. Öğrendiği ezgiyi arkadaşlarına dinletmek istedi.', 'Ali','müzik odası','flüt','Öğrendiği ezgiyi dinletmek'),
  ('Eylül, okul bahçesinde bir top kullandı. Arkadaşlarıyla oyun becerilerini geliştirmek istedi.', 'Eylül','okul bahçesi','top','Oyun becerilerini geliştirmek')],
 'science': [
  ('Kerem, sınıfta bir büyüteç kullandı. Bir yaprağın ayrıntılarını incelemek istedi.', 'Kerem','sınıf','büyüteç','Yaprağın ayrıntılarını incelemek'),
  ('Elif, kütüphanede bir uzay kitabı okudu. Gezegenler hakkında bilgi edinmek istedi.', 'Elif','kütüphane','uzay kitabı','Gezegenler hakkında bilgi edinmek'),
  ('Can, evde bir takvim hazırladı. Tohumunun büyümesini gün gün kaydetmek istedi.', 'Can','ev','takvim','Tohumun büyümesini gün gün kaydetmek')],
 'culture': [
  ('Duru, müzede bir kilim resmi çizdi. Geleneksel desenleri defterine kaydetmek istedi.', 'Duru','müze','kilim resmi','Geleneksel desenleri kaydetmek'),
  ('Aras, evde bir aile albümü inceledi. Ailesinin geçmişini öğrenmek istedi.', 'Aras','ev','aile albümü','Ailesinin geçmişini öğrenmek'),
  ('İpek, okul bahçesinde bir mendil taşıdı. Arkadaşlarıyla mendil kapmaca oynamak istedi.', 'İpek','okul bahçesi','mendil','Mendil kapmaca oynamak')],
 'rights': [
  ('Ada, sınıfta bir görev çizelgesi hazırladı. Herkesin sorumluluğunu hatırlamasını istedi.', 'Ada','sınıf','görev çizelgesi','Sorumlulukları hatırlatmak'),
  ('Emir, parkta bir uyarı kartı hazırladı. Oyun araçlarının sırayla kullanılmasını istedi.', 'Emir','park','uyarı kartı','Oyun araçlarını sırayla kullanmayı hatırlatmak'),
  ('Defne, evde bir okul çantası hazırladı. Ertesi günkü derse hazır olmak istedi.', 'Defne','ev','okul çantası','Derse hazır olmak')],
 'child': [
  ('Ece, parkta bir uçurtma uçurdu. Rüzgârlı günün tadını çıkarmak istedi.', 'Ece','park','uçurtma','Rüzgârlı günün tadını çıkarmak'),
  ('Ali, evde bir kukla yaptı. Kardeşine küçük bir gösteri hazırlamak istedi.', 'Ali','ev','kukla','Kardeşine bir gösteri hazırlamak'),
  ('Ada, okul bahçesinde bir tebeşir kullandı. Arkadaşlarıyla oynamak için seksek çizmek istedi.', 'Ada','okul bahçesi','tebeşir','Seksek çizmek')],
 'sport': [
  ('Can, spor salonunda bir ip kullandı. İp atlama çalışması yapmak istedi.', 'Can','spor salonu','ip','İp atlama çalışması yapmak'),
  ('Elif, parkta bir su şişesi taşıdı. Yürüyüşten sonra su içmek istedi.', 'Elif','park','su şişesi','Yürüyüşten sonra su içmek'),
  ('Emir, evde bir havlu hazırladı. Spor sonrası temizlenmek istedi.', 'Emir','ev','havlu','Spor sonrası temizlenmek')],
}


def turkish_bank(topic):
    title = topic['title'].casefold().replace('ı','i').replace('\u0307','')
    checks = [('ataturk',('atatürk','mustafa','mücadele','kahraman')),
        ('nature',('doğa','çevre','evren')),('books',('kitap','okuma','bilgi hazinemiz')),
        ('talent',('yetenek',)),('science',('bilim','mucit','kâşif')),
        ('culture',('kültür','atalar')),('rights',('hak','sorumluluk')),
        ('child',('çocuk dünyasi',)),('sport',('sağlik','spor')),
        ('values',('davraniş','değer','erdem'))]
    group = next((key for key, words in checks if any(w in title for w in words)), None)
    if group is None: raise ValueError('Türkçe teması eşleştirilmedi: '+topic['title'])
    result = []
    for passage, person, place, obj, purpose in STORIES[group]:
        questions = [
            ('Metinde anlatılan kişi kimdir?', person, ['Deniz','Burak','Seda']),
            ('Olay nerede geçmektedir?', place, ['tren istasyonu','pazar yeri','otobüs durağı']),
            ('Metinde hangi nesneden söz edilmektedir?', obj, ['pusula','eldiven','saat']),
            ('Metindeki kişinin amacı nedir?', purpose,
                ['Bir bilet satın almak','Bir yemek tarifi öğrenmek','Bir yolculuğa çıkmak'])]
        for prompt, answer, distractors in questions:
            result.append(question(topic, passage+'\n\n'+prompt, answer, distractors,
                f'Metindeki bilgiye göre doğru cevap: {answer}.', 'reading_'+group))
    return result


def number_question(topic, text, answer, concept, explanation):
    # Numeric distractors are distinct, non-negative and never change the result.
    choices = [answer + 1, answer + 2, max(0, answer - 1), answer + 3]
    if topic['grade']==1 and concept in ('number_order','number_pattern'):
        choices=[n for n in (answer-1,answer+1,answer-2,answer+2,answer-3,answer+3) if 0<=n<=20]
    q = question(topic, text, answer, choices, explanation, concept)
    q['expected_number'] = answer
    return q


def math_bank(topic):
    g, i = topic['grade'], topic['unit_index']; result=[]
    def add(text, answer, concept, explanation):
        result.append(number_question(topic,text,answer,concept,explanation))
    if (g<4 and i==0):
        maximum = {1:20,2:100,3:1000}[g]
        start = {1:2,2:21,3:201}[g]
        for j in range(12):
            n = start+j
            add(f'{n} sayısından sonra hangi doğal sayı gelir?',n+1,'number_order',f'{n} sayısından bir fazla olan sayı {n+1} olur.')
            add(f'{n} sayısından önce hangi doğal sayı gelir?',n-1,'number_order',f'{n} sayısından bir eksik olan sayı {n-1} olur.')
            a,b,c=n,n+2,n+4
            add(f'{a}, {b}, {c}, …\nİkişer artan örüntüde sıradaki sayı kaçtır?',c+2,'number_pattern',f'Her adımda 2 eklenir: {c} + 2 = {c+2}.')
        if g>1:
            for n in range(start,start+12):
                add(f'{n} sayısının onlar basamağındaki rakam kaçtır?',(n//10)%10,'place_value',f'{n} sayısının onlar basamağında {(n//10)%10} vardır.')
        # Grade-one patterns use only numbers within 20.
        if g==1:result=[q for q in result if q['expected_number']<=maximum]
        return result
    operations = (g==1 and i in (2,3)) or (g in (2,3) and i==2) or (g==4 and i==0)
    if operations:
        for j in range(1,21):
            a = (j%9)+2 if g==1 else j+10 if g==2 else j*7+100 if g==3 else j*137+1000
            b = (j%5)+1 if g==1 else j%15+2 if g==2 else j*3+12 if g==3 else j*17+50
            add(f'{a} + {b} işleminin sonucu kaçtır?',a+b,'addition',f'{a} + {b} = {a+b}.')
            add(f'{a} kalemin {b if b<a else 1} tanesi veriliyor. Kaç kalem kalır?',a-(b if b<a else 1),'subtraction',f'{a} − {b if b<a else 1} = {a-(b if b<a else 1)}.')
            if g>=2:
                x,y=j%5+1,j%4+2
                add(f'{x} kutunun her birinde {y} boncuk var. Toplam kaç boncuk vardır?',x*y,'multiplication',f'{x} × {y} = {x*y}.')
                add(f'{x*y} boncuk {x} çocuğa eşit paylaştırılıyor. Her çocuk kaç boncuk alır?',y,'division',f'{x*y} ÷ {x} = {y}.')
        if g==1 and i==2:
            for n in (1,5,10,20,50,100,200):
                add(f'Üzerinde {n} TL yazan paranın değeri kaç TL’dir?',n,'money',f'Paranın üzerinde yazan değer {n} TL’dir.')
        return result
    data = (g<4 and i==len([t for t in __import__('curriculum_practice').topics(g) if t['subject']=='Matematik'])-1) or (g==4 and i==2)
    if data:
        for j in range(1,13):
            a,b,c=j%4+1,j%4+3,j%4+5
            table=f'Sınıfın sevdiği meyveler:\nElma: {a} öğrenci\nArmut: {b} öğrenci\nMuz: {c} öğrenci'
            result.append(question(topic,table+'\nEn çok seçilen meyve hangisidir?','Muz',['Elma','Armut','Üçü de eşit'],f'{c}, diğer sayılardan büyüktür; en çok muz seçilmiştir.','data_max'))
            result.append(question(topic,table+'\nEn az seçilen meyve hangisidir?','Elma',['Armut','Muz','Üçü de eşit'],f'{a}, diğer sayılardan küçüktür; en az elma seçilmiştir.','data_min'))
            add(table+'\nMuz seçenlerin sayısı elma seçenlerden kaç fazladır?',c-a,'data_difference',f'{c} − {a} = {c-a}.')
            add(table+'\nTabloda toplam kaç öğrencinin tercihi vardır?',a+b+c,'data_total',f'{a} + {b} + {c} = {a+b+c}.')
        # Deduplicate repeated small tables while keeping both reading and calculation.
        return list({q['qkey']:q for q in result}.values())
    if g==1 and i==1:
        result=concept_bank(topic,'measure1')
        for j in range(1,11):
            add(f'Bir masanın uzunluğu {j+2} karıştır. Bir sıranın uzunluğu {j} karıştır. Masa kaç karış daha uzundur?',2,'nonstandard_length',f'{j+2} − {j} = 2 karış.')
        return result
    if (g in (2,3) and i==1) or (g==4 and i==1):
        result=concept_bank(topic,'measure' if g!=3 else 'fractions_time')
        for j in range(1,13):
            if g==2:
                add(f'{j} tane 5 TL toplam kaç TL eder?',j*5,'money',f'{j} × 5 = {j*5} TL.')
                add(f'Saat {j:02d}.00 iken 1 saat sonra saat kaç olur?',j+1,'time',f'{j:02d}.00 saatinden 1 saat sonrası {j+1:02d}.00 olur.')
            elif g==3:
                add(f'{j*4} eş parçalı bir bütünün yarısı kaç parçadır?',j*2,'half',f'Yarım, bütünün iki eş parçasından biridir: {j*4} ÷ 2 = {j*2}.')
                add(f'{j} hafta kaç gündür?',j*7,'time',f'1 hafta 7 gündür. {j} × 7 = {j*7}.')
            else:
                add(f'{j} metre kaç santimetredir?',j*100,'length',f'1 m = 100 cm. {j} × 100 = {j*100} cm.')
                add(f'{j} kilogram kaç gramdır?',j*1000,'mass',f'1 kg = 1000 g. {j} × 1000 = {j*1000} g.')
        return result
    if g==1 and i==4:return concept_bank(topic,'spatial')
    if g==1 and i==5:return concept_bank(topic,'shapes')
    if g in (2,3) and i==3:return concept_bank(topic,'solids')+concept_bank(topic,'shapes')
    if g in (2,3) and i==4:return concept_bank(topic,'symmetry')+concept_bank(topic,'spatial' if g==2 else 'measure')
    if g==4 and i==3:
        result=concept_bank(topic,'geometry4')
        for side in range(2,18):
            add(f'Bir kenarı {side} cm olan karenin çevresi kaç cm’dir?',side*4,'perimeter',f'Karenin 4 eş kenarı vardır: 4 × {side} = {side*4} cm.')
        return result
    raise ValueError('Matematik teması eşleştirilmedi: '+str((g,i,topic['title'])))


GROUPS.update({
 'measure1':[
  ('Karış','Başparmak ile serçe parmak açıldığında arada kalan uzunlukla ölçme.'),
  ('Adım','Yürürken attığımız adımları sayarak uzunluk ölçme.'),
  ('Daha uzun','İki nesneden uzunluğu daha büyük olan.'),
  ('Daha kısa','İki nesneden uzunluğu daha küçük olan.'),
  ('Daha ağır','İki nesneden kütlesi daha büyük olan.'),
  ('Daha hafif','İki nesneden kütlesi daha küçük olan.')],
 'measure':[
  ('Metre','Uzunluğu ölçmede kullanılan, 100 santimetreye eşit birim.'),
  ('Kilogram','Kütleyi ölçmede kullanılan, 1000 grama eşit birim.'),
  ('Litre','Sıvıların miktarını ölçmede kullanılan birim.'),
  ('Saat','60 dakikaya eşit zaman birimi.'),
  ('Yarım','Bir bütünün iki eş parçasından biri.'),
  ('Çeyrek','Bir bütünün dört eş parçasından biri.')],
 'fractions_time':[
  ('Yarım','Bir bütünün iki eş parçasından biri.'),
  ('Çeyrek','Bir bütünün dört eş parçasından biri.'),
  ('Pay','Kesirde ayrılan veya alınan eş parça sayısını gösteren sayı.'),
  ('Payda','Kesirde bütünün kaç eş parçaya ayrıldığını gösteren sayı.'),
  ('Dakika','60 saniyeye eşit zaman birimi.'),
  ('Hafta','7 günden oluşan zaman birimi.')],
 'spatial':[
  ('Üstünde','Bir nesnenin daha yukarısındaki konumu anlatan söz.'),
  ('Altında','Bir nesnenin daha aşağısındaki konumu anlatan söz.'),
  ('İçinde','Bir nesnenin sınırlarının iç tarafındaki konumu anlatan söz.'),
  ('Dışında','Bir nesnenin sınırlarının dış tarafındaki konumu anlatan söz.'),
  ('Önünde','Bir kişinin baktığı yönde, kendisinden ileride bulunan konum.'),
  ('Arkasında','Bir kişinin baktığı yönün ters tarafındaki konum.')],
 'shapes':[
  ('Üçgen','Üç kenarı ve üç köşesi olan düzlemsel şekil.'),
  ('Kare','Dört eş kenarı ve dört dik açısı olan düzlemsel şekil.'),
  ('Kare olmayan dikdörtgen','Dört dik açısı bulunan, iki uzun ve iki kısa kenarı olan dörtgen.'),
  ('Çember','Düzlemde bir merkezden eşit uzaklıktaki noktaların oluşturduğu kapalı çizgi.'),
  ('Köşe','Bir çokgende iki kenarın birleştiği nokta.'),
  ('Kenar','Bir çokgenin sınırını oluşturan doğru parçalarından biri.')],
 'solids':[
  ('Küp','Altı yüzü de eş kare olan geometrik cisim.'),
  ('Küp olmayan dikdörtgenler prizması','Altı yüzü dikdörtgensel bölge olan, bütün ayrıtları eşit olmayan geometrik cisim.'),
  ('Küre','Topa benzeyen, köşesi ve düz yüzü olmayan geometrik cisim.'),
  ('Silindir','İki eş dairesel tabanı ve eğri yan yüzü olan geometrik cisim.'),
  ('Koni','Bir dairesel tabanı ve bir tepe noktası olan geometrik cisim.'),
  ('Üçgen prizma','İki üçgensel tabanı ve üç dikdörtgensel yan yüzü olan geometrik cisim.')],
 'symmetry':[
  ('Simetri doğrusu','Şekli katladığımızda iki eş parçayı üst üste getiren doğru.'),
  ('Simetrik parçalar','Simetri doğrusunun iki tarafında birbirinin aynası gibi duran parçalar.'),
  ('Karenin simetri doğruları','Karede toplam dört tane bulunan simetri doğruları.'),
  ('Eş uzaklık','Simetrik iki noktanın simetri doğrusuna olan uzaklıkları arasındaki ilişki.'),
  ('Yatay doğru','Sayfada soldan sağa uzanan doğru.'),
  ('Dikey doğru','Sayfada yukarıdan aşağıya uzanan doğru.')],
 'geometry4':[
  ('Doğru','İki yönde de sonsuza uzadığı düşünülen düz çizgi.'),
  ('Doğru parçası','İki uç noktası olan düz çizgi bölümü.'),
  ('Işın','Bir başlangıç noktası olup bir yönde sonsuza uzadığı düşünülen çizgi.'),
  ('Dik açı','Ölçüsü 90 derece olan açı.'),
  ('Dar açı','Ölçüsü 0 dereceden büyük, 90 dereceden küçük olan açı.'),
  ('Geniş açı','Ölçüsü 90 dereceden büyük, 180 dereceden küçük olan açı.')],
})


def bank(topic):
    if topic['subject']=='Matematik':return math_bank(topic)
    if topic['subject']=='Türkçe':return turkish_bank(topic)
    return concept_bank(topic,group_for(topic))
