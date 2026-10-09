"""Repair known legacy Turkish spellings locally; preserve question identifiers."""
import re
import unicodedata

_CORRECTED = """
açıklama açıklamayı adım ağaç akıcı akışkan akışkanlık alışveriş altı anlamadım
anlatım anlatımı anlatır araç aracın araçlar araçların araçta araçtaki aşağıdaki
ayakkabı aynı bahçede bahçedeki bahçemizdeki balıklar balıkların bardağa bardağın
basamakları başarıya başlatılıyor batı boş boşlukları bulunduğu çalışmak canlılar
canlıların çanta çözümü doğru doğu doğum etrafı geçerli geçersiz geçiş gökyüzünden
görselde görseldeki görseli göze gözlerini gözlerinizi gündüzleri güneş güneşin güney
günlük güvenli hatırlayalım hızlı içilebilen içtiğimiz ikinci ilkokul incelenen ipucu
işlem kâğıt kahvaltıda karpuzu karşı katı katıların kırmızı kitaplık kontrollü
konuşarak koşarak köyümüzdeki küçük kuş kuşlar kuşların kuşun kütüphaneye
mutluluğa öğrenci öğrenme olduğunuz önceki örnek paydaları payları saksıda seçili
şehir şehirlerarası sıcak şimdi sınıf sınıfımızdaki sınıfımızın sınıfın sıvı sıvılar
sosu sürücülerin süt toprağı tümünü üret üretilen vücudumuzu yakıt yalnızca
yardım yeşil yolcuların yön yönler yüzler yüzme açar açıkla açılamadı açlığını
adı adım ağaca akışkan akşamları alanı alanıdır alanın alanında alanını alanının
aldığı aldığınızda algılanmadı alınamadı alındığında alır alıştırma almaktadır
alması anahtarı anlamına anlatım anlatımı anlayalım anlayamadım araca aracılığıyla
araçların araçta aralarındaki arası arasına arasında arasındaki artıran artırır
aşağı aşağıdaki aşağıdakilerden atlattığını atması aygıtı ayırıp ayırmak ayırmaktan
aylarında aynı ayrılan ayrılır ayrılmıştır bağlantısı bağlantıyı bağlayarak bağlıdır
bahçesinin bakalım bakıldığında bakıp bakman balığın balığının balık balıkların
balkondaki bardağa bardağı bardağın başına basınç başındaki başka başla başlamadan
başlayan batı batısındadır battığı biçimini bırakın bırakırız böldüğünde böldüğündeki
böldüklerine bölersek bölge bölgeleridir bölmek bölmekten bölümü bölümüne
bölündüğünde bölündüğündeki bölündüğündekinden bölünen bölünene bölünmüş
bölünmüştür bölünür bölüştürmek bölüştürmekten bölüştürürsen boş boyanmış
buğday bulduğumuz bulunamadı bulunduğu bulundukları bulunmaktadır bütün bütünden
bütüne bütünlerde bütünü büyüdükçe büyük büyüklüğe büyüklükteki büyüktür büyümek
büyümesi çalış çalışmak çalıştır camı canlı canlıların canlının çantası
çarpmalardan çatlar çay çelişme çeşitli cevabı cevabın cevabında cevaplandı çevreye
çiçeğimizi çiçeğini çiçekleri çiftini çıkıp çıkmak çikolatadan çikolatanın çıktıktan
çizebilirsin çizgi çizgilerle çok çözüm cümlesiyle çünkü değeri değil değildir
değiştirmeyen değiştir diğer diğerinden diğerini dış dışarıdan dışı doğal doğduğu
doğru doğrudur doğu doğudadır doğusundadır doğuyu dökeriz döküldüğünde dolduğu
doldurduğumuz doldurulduğunda doldurursan dön döndürdü dönün dosyasını dükkânımız
durduğundan durmasını duruşlarda duruşu duruşunu düşer düşmesini düşün düşünelim
düşünün düzenli eğilimindedir ekipmanıdır elmayı eşit etmeliyiz etrafı etrafımızı
ettiği farklı gagasıyla gazdır geçemedi geçen geçer geçerken geçerlidir geçersiz
geçidi geçidinde geçidinden geçidini geçidinin geçilmiyor geçiş geçitleri geçme
geçmek geçmeli geçmesi geçmeye geldiğinde gelişmesi gelişmesinde geniş
genişleyerek geniştir gerektiğini giriş gökyüzündeki göllerde göre görebildiği
görmek görsel görseli görselindeki görseline görselle görülebilen görünmeyen görüp
göster gösterdiği gösterdiğinden gösteren gösterildiği gösterilen gösteriminde
gösterir gösteriyorsa göstermek gözlük güç gücü gücünü gün günde güneş güneşin
güney güneyinde güneyindedir günlük günü güvenle güvenli güvenliğimiz güvenliğimizi
güvenliğini güvenlik güzel hakkı hakkına hâldedir hâli hâlindedir hâlindeyken hâline
hâlini hâlleri hâllerinden hapsedildiğinde hatırla hatırlatır hatırlayın hayatını
hayvanın hazır hazırla hazırlanamadı hazırlanıyor hazırlanmalı henüz
hızala hızını hızlanır hızlı içeceklerin içeriyi içilen için içinde içindeki içindir
içine içini ihtiyaç ihtiyacını ilişkisi ilk ışığı ışığın ışığına ışığında ışığının
ışık ışıkta ısıtan işlem istediğin istediğini isteği kabın kaç kafesine kahvaltısı
karşı karşıdan karşılamalıyız karşılaştırarak karşılaştırılırsa karşılaştırılması
karşılaştırma karşısına karşıya kaşık katıdır katılar kaydedilmedi kayıtlı kaynağı
kaynağıdır kaynaktır kazanır kazanması kenarındaki keşif kesildi kesildiğinde
kesildiğindekinden kilitlemek kırıntıları kırmızı kırmızıda kısa kısım kişiye kısmı
kısmın kısmına kısmını kıyasla kökleri köklerinin koltuğa koltuktaki konulduğu
koridorun koruması korunmasını köşesinde koşmalı kotası koyarız küçük küçükse
küçülür kullanılamadı kullanılan kullanıldı kullanma kullanmalıyız kulübe kumaş
küpleri kuş kuşlar kuşun küveti kuzeyindedir laboratuvarındaki miktarı miktarını
molası musluktan nasıl nasıldır noktasına öğrenci öğrenelim olduğu olduğunda
olduğundan olmadıkça olmalı olmalıdır olması olmasını olası oluşturur önce önemli
önemlidir önüne örneği örnek örnektir ortamı ortası otobüs otobüse oynatılıyor özel
özelliği özelliğine özellik parça parçacıklar parçadan parçalar parçalara parçanın
parçasını parçaya parkın payı paylaştırırken paylaştırmak pikniğe pizzanın pizzayı
planı pusulamız rahatça sarsıntılardan şarttır savrulmaması sayfalarını sayılacak
sayıları sayısı sayısından sayıyı seç seçeneğe seçeneği seçeneğin seçenek seçenekleri
seçilmeli seçilmelidir seçimine şekilde şekilleri şekli şeklini serbestçe
serbestliğini şeritlerle sertliğini sıcak sıfırdan simidi simidini sınıf sınıfındadır
sınıflandırmasını sınırı sınırlı sırada sıralanır sıran sırasında sırayla şişesini
şişip şişirdiğimiz şişiren şişirerek şişirilen şişirmeye şişkin sıvı sıvıdan sıvıdır
sıkıştırılabilir şoförün soğuk solmaması solunda söyledi söylemesin
suladığımız sularız süre sürece susuzluğa süt sürdüren takmalı takmalıdır takması
tamamladın tamamlandı tarafına tarafındadır tarafındaki tarlanın taş tasarlanmış
taşı taşın tebeşir tık tıkla tıklayabilirsin toprağın tükettiği tüm uçabilmek üçte
ulaşmak üretimi üretir üretiyor üretmesine üretmesini üst üstü uyarısıyla
uzattığımızda üzere üzerinde üzerindeki üzerinden vardır yanarken yandığında
yandığını yanınca yanındaki yanıt yanıyor yanmaktadır yanmasıyla yapalım yapılan
yapılı yapısı yapmalıdır yapması yapraklarının yapraklı yaralanmaması yardım
yardımcı yardımıyla yardımlı yardımsız yarış yaşadığı yaşam yaşamak yaşaması yaşar
yaşayabilir yaşayamaz yaşayan yayaların yaydığı yayılan yayılır yayılma yazı
yerleştirilmiştir yeşil yeşilde yıkadığımız yolculuğu yolculuğuna yön yönde yöne
yöneldik yönlerden yönlerin yönü yönünde yönündedir yönüne yönünü yukarı yukarısı
yürümek yürümelidir yürümez yürürken yüzden yüzdüğü yüzerek yüzgeçlerini yüzlük
zorlanmadığı zorundadır
saksı saksıdaki sağ sağa sağında sağını sağlamak sağlar sağlayan saklaması
eşit şişkinlik şişkin şişkinliği hazırlama hazırlanması hazırlanmasını
değiştirmek değiştir değişiklik değişikliği tamamlanmış tamamlamış
yayaların solungaç solungaçlarıyla kalmamıza kalması penceresi yaya geçidi
oynamalı yapmalı hatırlatıcı hissettiğimiz gördüğümüz düşündüğümüz
""".split()
_FOLD = str.maketrans("çğıöşüÇĞİÖŞÜâîûÂÎÛ", "cgiosuCGIOSUaiuAIU")
_WORDS = {}
for _word in _CORRECTED:
    _title = _word[0].replace("i", "İ").upper() + _word[1:]
    for _correct in (_word, _title, _word.replace("i", "İ").upper()):
        _WORDS[_correct.translate(_FOLD)] = _correct


def restore_text(text):
    text = unicodedata.normalize("NFC", text)
    return re.sub(r"[^\W\d_]+", lambda match: _WORDS.get(match.group(), match.group()), text)


def restore_payload(payload):
    result = dict(payload)
    for field in ("prompt", "hint", "explanation", "example"):
        if isinstance(result.get(field), str):
            result[field] = restore_text(result[field])
    if isinstance(result.get("options"), list):
        result["options"] = [restore_text(option) for option in result["options"]]
    return result
