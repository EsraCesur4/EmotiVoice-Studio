<h1 align="center">EmotiVoice Studio</h1>


![logo](Documentation/logo/logo_large.png)

<h2 align="left"> 1. Proje Tanımı</h2>

EmotiVoice Studio, metin veya ses girdilerini kullanarak, girdinin duygusal içeriğini analiz eden ve bu duyguya uygun şekilde ifade, ses tonu ve yüz hareketi üreten bir yapay zekâ tabanlı konuşan avatar sistemidir.   

Sistem, kullanıcıdan alınan ses veya metin girdisini işleyerek:
- Girdideki duyguyu belirler,
- Eğer girdi metin ise belirlenen duyguya uygun ses üretimini gerçekleştirir,
- Duygusal sese ait ağız hareketlerini zaman çizelgesi üzerinden senkronize eder,
- Kullanıcının seçtiği fiziksel özelliklere sahip bir avatar üzerinde bu hareketleri uygular.   

Bu süreç sonunda duygusal olarak ifade eden bir avatar videosu elde edilir.

<h3 align="left"> Sistem Mimarisi</h3>
Uygulama, istemci-tabanlı bir arayüz (frontend) ile Flask tabanlı bir sunucu (backend) mimarisi üzerinde çalışır.   

![sistem mimarisi](Documentation/charts/sistem_mimarisi.png)



---

<h3 align="left">EmotiVoice Studio Canlı Platform Linki</h3>

🔗 **Tıklanabilir bağlantı:**

[EmotiVoice Studio - Hugging Face Spaces](https://huggingface.co/spaces/esracesur/EmotiVoice)  

[![Hugging Face Spaces Status](https://img.shields.io/badge/Spaces%20Status-Online-brightgreen?logo=huggingface&logoColor=white)](https://huggingface.co/spaces/esracesur/EmotiVoice)



<h3 align="left">EmotiVoice Studio Kullanım Videosu</h3>

[![EmotiVoice Studio Demo](https://img.youtube.com/vi/y06m1b8iHmA/0.jpg)](https://youtu.be/y06m1b8iHmA "EmotiVoice Studio Demo")


---

<h2 align="left"> Proje Sahibi </h2>

| Proje Grubu | GitHub Profili | İsim | Sosyal Medya |
|----------------|--------------------|------------|----------------|
| **ArtWiz** | ![GitHub Profile](https://github.com/EsraCesur4.png?size=80) | **Esra Cesur** | [Kaggle](https://www.kaggle.com/esracesur0) · [LinkedIn](https://www.linkedin.com/in/esracesur4) · [Medium](https://medium.com/@esracesur20) |


---

<h2 align="left"> 2. Proje Yeniliği ve Orijinalliği</h2>

Projenin yenilikçi yönü, klasik metin veya ses analizlerinin ötesine geçip, duygusal iletişimi dijital ortama taşımayı başarmasıdır. Bu sayede durağan bir metin bile sistem tarafından duygusal ses, yüz ifadesi ve konuşma animasyonu ile yeniden canlandırılabilmektedir.

![Proje Yeniliği](Documentation/charts/proje_yeniligi.png)

| Proje Yenilikleri ve Özellikleri |
|--------------------------------------|
| **1. Ses ve Metin Girdilerini Destekleyen Esnek Yapı**<br>Sistem hem ses kaydı yüklenmesine hem de doğrudan metin girilmesine olanak tanır.<br>- Ses girişi durumunda, kayıt öncelikle **Whisper** modeliyle metne dönüştürülür; ardından **RoBERTa** tabanlı model, bu metin üzerinden duygu analizi yapar.<br>- Metin girişi durumunda ise **RoBERTa** modeli doğrudan metnin duygusal içeriğini belirler.<br><br>Bu iki yönlü destek sayesinde, platform farklı veri tiplerinden gelen girdileri tek bir duygusal analiz sürecinde birleştirir ve kullanıcıya geniş bir kullanım esnekliği sunar. |
| **2. Metinlerden Ses Üretimi (Text-to-Speech Entegrasyonu)**<br>EmotiVoice Studio, yalnızca metinleri analiz etmekle kalmaz, metinleri seslendirerek hayata geçirir. Sistem, tespit edilen duygunun tonuna uygun şekilde **Edge-TTS** aracılığıyla metni ses çıktısına dönüştürür. Bu özellik sayesinde yazılı ifadeler, duygusal bir ses deneyimi olarak dinlenebilir hale gelir. |
| **3. Duyguların Görselleştirilmesi: “Metinden İfade’ye”**<br>Sistem yalnızca duyguyu tespit etmekle kalmaz; bu duyguyu görsel olarak ifade eden bir avatar üretir. Modelin tahmin ettiği duygu sonucuna göre avatarın göz, ağız ve yüz ifadeleri dinamik olarak değişir ve seçilir. Böylece kullanıcıya yalnızca analiz sonucu değil, duygusal olarak yaşayan bir karakter sunulur. Bu özellik, duygu analizi sonuçlarını soyut bir sayıdan çıkarıp görsel olarak hissedilebilir hale getirir. |
| **4. Türkçe ve İngilizce Duygu Analizini Destekleyen Çift Dilli Model**<br>EmotiVoice Studio, hem **Türkçe hem İngilizce** metinlerle çalışabilmektedir. Aynı mimarinin iki dilde de çalışabilmesi, sistemi çok dilli iletişim teknolojilerine hazır hale getirir. |


---

<h2 align="left"> 3. Çevresel ve Sosyal Etki</h2>

![Sosyal Etki](Documentation/charts/cevresel_sosyal_etki.png)

**Sosyal Etki**
- **İletişim Engellerini Aşma:** Konuşma güçlüğü yaşayan kullanıcılar, metin tabanlı ifadelerini duygusal ses ve avatar destekli mesajlara dönüştürerek kendilerini daha etkili şekilde ifade edebilir.
- **Kişisel İfade ve Sosyalleşme:** Sosyal medya ve mesajlaşma platformlarında kullanıcılar, kendi tarzlarına uygun kişiselleştirilebilir avatarlar aracılığıyla duygularını daha doğal ve yaratıcı biçimde yansıtabilir.
- **Etkileşimde Eğlence Unsuru:** Duygu tabanlı konuşan avatarlar, çevrim içi sohbetlere ve içerik üretimine eğlence ve samimiyet katarak daha etkileşimli dijital ortamlar oluşturur.

**Çevresel Etki**
- **Tamamen Dijital Çözüm:** Fiziksel kaynak tüketimi olmadan çalışır, çevresel ayak izini minimumda tutar.
- **Uzaktan Etkileşimi Teşvik:** Dijital ortamlarda duygu aktarımını kolaylaştırarak fiziksel etkileşim ihtiyacını azaltır, dolaylı olarak karbon salınımını düşürür.

---

<h2 align="left"> 4. Uygulanabilirlik ve Yaygınlaştırma</h2>

![Uygulanabilirlik](Documentation/charts/uygulanabilirlik.png)

EmotiVoice Studio, konsept aşamasını aşmış, doğrudan kullanılabilir nitelikte bir yapay zekâ tabanlı platformdur. Sistem; ses, metin, duygu analizi, seslendirme ve avatar üretimini tek bir çalışma zincirinde birleştirerek uçtan uca entegre bir çözüm sunar. Modüler yapısı, farklı alanlarda kolay entegrasyon ve ölçeklenebilirlik sağlar.

**Uygulanabilirlik**
- **Hazır Altyapı:** Sistem, Flask tabanlı sunucu ve web tabanlı kullanıcı arayüzüyle birlikte tamamen işlevsel bir şekilde yapılandırılmıştır; ek yazılım veya donanım gerektirmez.
- **Platform Bağımsız Kullanım:** Tüm bileşenler Python tabanlıdır ve hem yerel ortamda hem bulut sistemlerinde (ör. Hugging Face, Streamlit, web sunucuları) kolayca dağıtılabilir.
- **Kullanıcı Etkileşimi Odaklı Tasarım:** Arayüz, teknik bilgiye sahip olmayan kullanıcıların bile kolayca video üretmesini sağlar.
- **Modüler Genişletilebilirlik:** Yeni diller, ses stilleri, yüz ifadeleri veya kurum temalı avatar setleri kolayca eklenebilir; bu da sistemi kurumsal ölçekli uyarlamalara hazır hale getirir.
- **Uygulama Alanı Esnekliği:** Aynı sistem, hem bireysel kullanımda hem de müşteri hizmetleri, eğitim, içerik üretimi gibi profesyonel ortamlarda doğrudan uygulanabilir-.

**Yaygınlaştırma Potansiyeli**
- **Mesajlaşma Uygulamaları:** Kullanıcılar, metin veya ses mesajlarını duygusal sesli avatar videolarına dönüştürerek daha etkili iletişim kurabilir.
- **Sosyal Medya ve İçerik Üretimi:** Yaratıcı içerik üreticileri, kendi tarzlarına uygun duygusal konuşan avatarlar oluşturarak izleyicileriyle daha güçlü bir bağ kurabilir.
- **Müşteri Hizmetleri ve Chatbot’lar:** Kurumsal platformlarda duygusal tepkiler veren avatar tabanlı asistanlar ile kullanıcı deneyimi geliştirilebilir.
- **Anında Entegrasyon:** Web tabanlı mimarisi sayesinde mevcut uygulamalara API veya iframe olarak kolayca eklenebilir.
- **Çok Dilli Destek:** Türkçe ve İngilizce modeller, sistemi ulusal ve uluslararası platformlarda kullanılabilir hale getirir.
- **Toplumsal Yaygınlık:** Günlük dijital iletişimde metin mesajlarının duygusal boyut kazanması, platformun eğlence, eğitim ve sosyal iletişim alanlarında geniş kullanıcı kitlesine ulaşmasını sağlar.



---


<h2 align="left"> 5. Proje ve Zaman Yönetimi</h2>

Proje, toplam 8 haftalık bir geliştirme sürecinde, sprint tabanlı (haftalık) planlama yaklaşımıyla yürütülmüştür. Her sprint belirli bir modüle odaklanmış; haftalık değerlendirmeler, çıktıların test edilmesi ve sonraki aşamanın planlanması ile tamamlanmıştır. Süreç boyunca zaman yönetimi, öncelik sırasına göre yürütülmüş ve bağımlı modüller ardışık olarak geliştirilmiştir.

---

<h3 align="left">Planlama Stratejisi</h3>

Proje planı, yapay zekâ modeli, görsel tasarım ve kullanıcı arayüzü gibi bağımsız fakat birbirini besleyen bileşenlerin paralel ilerleyebileceği şekilde tasarlanmıştır. Bu sayede model eğitimi sürerken avatar tasarımları hazırlanmış, sonraki sprintlerde pipeline entegrasyonu hızlı bir şekilde tamamlanmıştır. Her sprint sonunda geliştirilen modül test edilerek geri bildirim döngüsü oluşturulmuştur.


<p><i>🔽 Her sprint detayını görmek için üstüne tıklayın.</i></p>

<details>
<summary><b>Sprint 1 - Veri ve Model Temelleri</b></summary>

**Amaç:** Projenin altyapısını oluşturmak için yöntem seçimi, veri seti hazırlığı ve ilk model eğitimini tamamlamak.
**Başlıca Çalışmalar:**
- Literatür ve benzer projelerdeki yöntemlerin incelenmesi
- İngilizce veri setlerinin araştırılması ve etiket yapılarının incelenmesi
- Kullanılacak 7 temel duygu etiketinin belirlenmesi
- 4 İngilizce veri setinin toplanması, filtrelenmesi ve birleştirilmesi
- RoBERTa modelinin İngilizce birleşik veri setinde eğitilmesi
- Modelin hiperparametre optimizasyonu ve performans değerlendirmesi
**Çıktı:** İngilizce veriler üzerinde optimize edilmiş ilk duygu analizi modeli ve sağlam bir veri temeli.

</details>

<details>
<summary><b>Sprint 2 - Görsel ve Zamanlama Altyapısı</b></summary>

**Amaç:** Duygu analizi sonuçlarını görsel olarak temsil edecek dinamik bir avatar ve zaman tabanlı dudak hareketi sistemi oluşturmak.
**Başlıca Çalışmalar:**
- İlk avatar tasarımı ve yüz ifadelerinin oluşturulması
- Viseme (dudak hareketi) yapılarının araştırılması ve çizimi
- Text’ten viseme çıkarma ve zaman çizelgesi oluşturma sistemi
- Ağız hareketlerinin zaman bazlı video birleştirmesi
- Video optimizasyonu (fps, çözünürlük ve senkronizasyon ayarları)
- Model, ses, viseme ve video modüllerinin birleştirilmesi

</details>

<details>
<summary><b>Sprint 3 - Avatar Tasarımı ve Görsel Entegrasyon</b></summary>

**Amaç:** Kullanıcıya daha fazla çeşitlilik sunmak amacıyla avatar sistemini ölçeklendirmek ve kişiselleştirilebilir hale getirmek.
**Başlıca Çalışmalar:**
- Avatarların çoğaltılması (4 kadın, 3 erkek)
- Avatar görsellerinin katmanlara ayrılması (saç, göz, ağız, duygular vb.)
- Saç rengi, göz rengi ve yüz ifadeleri için özelleştirme seçeneklerinin eklenmesi
- Her duyguya ve cinsiyete özel dudak hareketlerinin çizilmesi
- Yeni oluşturulmuş avatarların pipeline'a entegrasyonu ve test aşamaları
**Çıktı:** Kişiselleştirilebilir, cinsiyet ve duygu bazlı varyasyonlara sahip tam ölçekli avatar sistemi.

</details>

<details>
<summary><b>Sprint 4 - Pipeline ve Uygulama Geliştirme</b></summary>

**Amaç:** Kullanıcıyla etkileşim sağlayacak arayüzlerin geliştirilmesi, backend sistemlerinin entegrasyonu ve sistemin hem İngilizce hem Türkçe çalışmasını sağlamak,
**Başlıca Çalışmalar:**
- Flask backend ve API yapısının kurulumu
- Frontend demo sayfalarının geliştirilmesi (mesajlaşma, sosyal medya, müşteri hizmetleri)
- Genel kullanım arayüzü ve kontrol panelinin geliştirilmesi
- Text-to-Speech (Edge-TTS) entegrasyonu
- Sadece metin tabanlı modun eklenmesi
- Türkçe veriseti araştırması ve verilerin toplanması
- Roberta modelinin türkçe veri üzerinde eğitimi
- Türkçe modelin sisteme entegrasyonu
**Çıktı**: Hem İngilizce hem Türkçe metin veya ses girişlerini destekleyen, etkileşimli bir kullanıcı arayüzüne ve çok dilli yapay zekâ pipeline’ına sahip sistem.

</details>

<details>
<summary><b>Sprint 5 - Ürünleştirme ve Yayınlama</b></summary>

**Amaç:** Projeyi son kullanıcıya hazır, dağıtılabilir hale getirmek.
**Başlıca Çalışmalar:**
- Docker yapılandırması ve containerlaştırma
- Hugging Face Spaces üzerinde canlı sürümün yayınlanması
- HTML arayüz düzenlemeleri ve performans optimizasyonu
- Proje sunumu, README ve GitHub sayfasının hazırlanması
**Çıktı:** Yayınlanabilir, dokümante edilmiş ve kullanıcı tarafından test edilebilir bir
</details>

---

<h3 align="left"> Zaman Yönetimi</h3>

![Zaman Yönetimi Grafiği](Documentation/charts/zaman_yonetimi.png)


---


<h2 align="left"> 6. Teknik Bileşenler</h2>
<h3 align="left"> 6.1 Kullanıcı Arayüzü (Frontend)</h3>

EmotiVoice Studio arayüzü, kullanıcıya hem sezgisel hem de modüler bir çalışma alanı sunan iki ana panelden oluşur:     

1. Girdi ve Özelleştirme Paneli (sol kısım)   
2. Kullanım Senaryosu Paneli (sağ kısım)

![Frontend](Documentation/charts/frontend.png)

 ---

<h3 align="left"> 6.2 Model Katmanı</h3>

Bu sistemde duygu tespiti (Emotion Recognition from Text) için **iki farklı RoBERTa tabanlı model** geliştirilmiştir:  
biri **Türkçe**, diğeri **İngilizce** veri kümeleriyle eğitilmiştir.  
Her iki model, 7 temel duyguyu sınıflandırmak üzere optimize edilmiştir:    

![Etiketler](Documentation/charts/etiketler.png)

**Model çıktıları:**
anger, sadness, joy, surprise, fear, neutral, disgust

Geliştirdiğim iki modeli de Hugging Face'e yükledim. Linkleri aşağıda yer almaktadır.

**Model Linkler:**

| Dil | Model | Hugging Face Linki | Doğruluk (Accuracy) |
|------|--------|--------------------|----------------------|
| İngilizce | RoBERTa | [esracesur/roberta_weighted](https://huggingface.co/esracesur/roberta_weighted) | 0.7733 |
| Türkçe | RoBERTa | [esracesur/roberta_turkish_emotion_recognition](https://huggingface.co/esracesur/roberta_turkish_emotion_recognition) | 0.8923 |


<details>
<summary><b>Model Performansı (Confusion Matrix)</b></summary>

<table>
  <tr>
    <td><img src="model_training/English/Evaluation/emotion-dataset_test_cm.png" width="400"></td>
    <td><img src="model_training/English/Evaluation/emotions-description_cm.png" width="400"></td>
  </tr>
  <tr>
    <td><img src="model_training/English/Evaluation/meld_test_cm.png" width="400"></td>
    <td><img src="model_training/English/Evaluation/text-sentiment_cm.png" width="400"></td>
  </tr>
</table>

</details>




---

<h4 align="left"> Kullanılan Veri Setleri</h4>

Toplamda **11 farklı veri kümesi** kullanılmıştır. Veriler; diyaloglar, tweet’ler, kullanıcı yorumları, kısa cümleler ve hikâye tanımları gibi çok farklı metin kaynaklarından alınmıştır.
Her iki model için yalnızca 7 hedef etiket (anger, sadness, joy, fear, disgust, surprise, neutral) filtrelenmiş ve bu etiketlere ait örnekler kullanılmıştır.

<h4 align="left"> Türkçe Veri Setleri</h4>

| # | Veri Seti Adı | Kayıt Sayısı | Açıklama | 
|---|----------------|--------------|-----------|
| 1 | **[EmotionalTurk](https://www.kaggle.com/datasets/egemenipek/emotionalturk)** | 1.533 | Türkçe metinlerden oluşturulmuş, 6 duygu etiketi içeren veri kümesi. | 
| 2 | **[Turkish Tweets Dataset](https://www.kaggle.com/datasets/anil1055/turkish-tweet-dataset)** | 4.000 | Twitter üzerinde duygu etiketleriyle hazırlanmış Türkçe kısa metinler. | 
| 3 | **[Turkish Emotion Dataset](https://www.kaggle.com/datasets/mehmetcalikus/turkish-emotion-dataset)** | 3.900 | Eğitim ve test olarak ayrılmış etiketli Türkçe duygu cümleleri. | 
| 4 | **[TREMO (Turkish Emotional Speech Dataset)](https://www.kaggle.com/datasets/ruevis/tremo-dataset)** | 27.350 | XML formatında, konuşma transkriptlerinden alınmış doğrulanmış duygu verileri. | 

Bu kaynaklardan yalnızca 7 hedef etikete (anger, sadness, joy, fear, disgust, surprise, neutral) ait kayıtlar alınmıştır. Filtreleme sonrası toplam **33.632 Türkçe örnek** kullanılmıştır.

---

<h4 align="left"> İngilizce Veri Setleri</h4>

| # | Veri Seti Adı | Kayıt Sayısı | Açıklama | 
|---|----------------|--------------|-----------|
| 1 | **[MELD (Multimodal EmotionLines Dataset)](https://www.kaggle.com/datasets/declare-lab/meld)** | 9.989 | Çoklu konuşma ortamlarında duygu etiketli İngilizce diyaloglar. |
| 2 | **[Crowdflower Dataset](https://huggingface.co/datasets/tasksource/crowdflower/viewer/text_emotion/train)** | 23,753 | Tweet tabanlı, metin-duygu eşleşmesi içeren büyük ölçekli veri kümesi. |
| 2 | **[Go Emotions Dataset](https://huggingface.co/datasets/go_emotions/viewer/raw/train)** | 16,021 | Farklı topluluklardan alınmış 58.000 Reddit yorumu |
| 2 | **[DAIR-AI Emotion Dataset](https://huggingface.co/datasets/dair-ai/emotion)** | 20,000 | Twitter, blog yorumları, haber yorumları |
| 2 | **[SemEval 2018 Task 1 Dataset](https://huggingface.co/datasets/sem_eval_2018_task_1/viewer/subtask5.english/train)** | 5,603 | Twitter paylaşımları, hashtag’ler ve kısa durum metinleri. |
| 3 | **[Emotions Description Dataset](https://www.kaggle.com/datasets/radedaevi/emotions-description)** | 7.666 | Katılımcıların duygu tanımlarıyla oluşturulmuş durum bazlı veri kümesi. | 
| 4 | **[Emotion Dataset](https://www.kaggle.com/datasets/parulpandey/emotion-dataset)** | 11.133 | Duygu etiketli kısa İngilizce cümlelerden oluşur. | 

İngilizce veri setlerinden yalnızca 7 ortak etiket korunmuş, diğer duygu kategorileri hariç tutulmuştur. Eğitim sürecinde toplam **94.165 İngilizce örnek** kullanılmıştır.

---

<h3 align="left"> 3.2 Backend (Sunucu Katmanı)</h3>

![Etiketler](Documentation/charts/backend.png)

Sunucu katmanı Python ve Flask kullanılarak yapılandırılmıştır.
Arayüzden gelen talepler şu API uç noktaları aracılığıyla yönetilir:

| Endpoint | Metot | Görev |
|-----------|--------|--------|
| `/api/process-text` | **POST** | Metin girdisini alır, RoBERTa tabanlı duygu analizini gerçekleştirir, tespit edilen duyguya uygun olarak ses üretir ve avatar dudak senkronizasyonuyla video çıktısını oluşturur. |
| `/api/process-audio` | **POST** | Kullanıcı tarafından yüklenen ses dosyasını işler, Whisper tabanlı konuşma tanıma yapar, duygusal tonlamayı analiz eder ve dudak hareketlerini çıkartarak avatar videosunu üretir. |
| `/api/progress` | **GET** | Devam eden işlemin mevcut ilerleme yüzdesini ve aşamasını döner. Frontend’deki ilerleme çubuğu bu endpoint üzerinden güncellenir. |
| `/api/get-voices` | **GET** | Sistem tarafından desteklenen metin-konuşma (TTS) ses profillerinin listesini döner. Arayüzdeki “Voice Options” menüsünü besler. |
| `/api/get-emotions` | **GET** | Duygu sınıflandırma modelinde yer alan etiketleri (`joy`, `anger`, `sadness`, vb.) döner. Renk kodlu emotion rozetleri bu veriye göre atanır. |
| `/api/avatar-config` | **GET** | Avatar oluşturma parametrelerinin (cinsiyet, saç stili, renk, göz rengi) varsayılan yapılandırmasını döner. Kullanıcı seçim ekranı bu endpoint’ten beslenir. |
| `/api/render-avatar` | **POST** | Kullanıcının seçtiği görsel özelliklere göre (gender, hair, eye) geçici bir avatar önizleme çıktısı üretir. Canvas tabanlı “Live Preview” bu uç noktayı kullanır. |
| `/api/download-result` | **GET** | Oluşturulan son video dosyasını istemciye indirme bağlantısı olarak döner. Kullanıcılar üretilen avatar videosunu bu uç nokta üzerinden dışa aktarabilir. |

Bu süreçte kullanılan temel modüller:
- Whisper: Ses dosyalarından metin ve zaman bilgisi çıkarımı,
- Transformers (RoBERTa): Metin üzerinden duygu sınıflandırması,
- Edge-TTS: Duyguya uygun ton, hız ve frekansta ses sentezi,
- MoviePy / PIL: Katman birleştirme, dudak hareketi ve video oluşturma işlemleri.

---
<h4 align="left"> Avatar Tasarım ve Video Üretim Mimarisi</h4>
Avatarlar, statik görsel katmanların (layer) üst üste bindirilmesiyle oluşturulur.

<h4 align="left"> Avatar Katman Yapısı</h4>

Her avatar; arka plandan öne doğru belirli bir sıra ile yerleştirilen 3 temel görsel katmandan (layer) oluşur:

| <img src="Documentation/charts/hair.png" width="80" alt="Saç Katmanı Görseli"/> <br> **Saç Katmanı (Hair Layer)** | <img src="Documentation/charts/eyes.png" width="80" alt="Göz Katmanı Görseli"/> <br> **Göz Katmanı (Eyes Layer)** | <img src="Documentation/charts/mouth.png" width="80" alt="Ağız Katmanı Görseli"/> <br> **Ağız Katmanı (Mouth Layer)** |
| :------------------------------------------------------------------------------------------------------------------------------------------------------------------: | :----------------------------------------------------------------------------------------------------------------------------------------: | :---------------------------------------------------------------------------------------------------------------------------------------------: |
|                                - En alt katmanda yer alır. <br> - Farklı **saç stilleri** ve **renkleri** ile özelleştirilebilir.                                |   - Saç katmanının üzerine yerleştirilir. <br> - Duygu durumuna göre (örneğin *joy*, *sadness*, *anger*) farklı göz ifadeleri kullanılır.  |                      - En üstte yer alır. <br> - **Viseme**’lere göre dudak şekilleri konuşmadaki seslerle senkronize olur.                     |

Bu katmanlar, `AvatarComposer` modülü tarafından **şeffaf arka planlı (RGBA)** PNG dosyaları olarak üst üste bindirilir (`Image.alpha_composite` metodu).  
Sonuçta, her duygu için 6 temel ağız şekli (REST, AA, IY, UW, FV, MBP) oluşturulur ve bu şekiller birleştirilerek konuşma animasyonu hazırlanır.

<h4 align="left"> Avatar Özelleştirme Seçenekleri</h4>

Kullanıcılar, platformun arayüzünden kendi avatarlarını oluşturabilir.  
Her seçenek, ayrı bir katmanda temsil edilir ve birbirleriyle kombine edilebilir.

![customize](Documentation/charts/customize.png)

<div align="center">

<table>
  <thead>
    <tr>
      <th>Özellik</th>
      <th>Seçenekler</th>
      <th>Kombinasyon Sayısı</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><b>Cinsiyet (Gender)</b></td>
      <td>2 <i>(male, female)</i></td>
      <td>2</td>
    </tr>
    <tr>
      <td><b>Saç Stili (Hair Style)</b></td>
      <td>3 erkek + 4 kadın <i>(curly, straight, wavy, short, shaved)</i></td>
      <td>7</td>
    </tr>
    <tr>
      <td><b>Saç Rengi (Hair Color)</b></td>
      <td>7 <i>(black, blonde, blue, brown, light_brown, orange, red)</i></td>
      <td>7</td>
    </tr>
    <tr>
      <td><b>Göz Rengi (Eye Color)</b></td>
      <td>4 <i>(black, blue, brown, green)</i></td>
      <td>4</td>
    </tr>
    <tr>
      <td><b>Duygu (Emotion)</b></td>
      <td>7 <i>(anger, disgust, fear, joy, neutral, sadness, surprise)</i></td>
      <td>7</td>
    </tr>
    <tr>
      <td><b>Ağız Şekli (Viseme)</b></td>
      <td>6 <i>(REST, AA, IY, UW, FV, MBP)</i></td>
      <td>6</td>
    </tr>
  </tbody>
</table>

<p><b>Toplam olası kombinasyon sayısı:</b><br>
2 (cinsiyet) × 7 (saç stili) × 7 (renk) × 4 (göz) × 7 (duygu) × 6 (ağız şekli)
= <b>16.464 farklı yüz ifadesi</b><br>
<i>(Sistem gereksiz varyasyonları eleyerek yalnızca aktif kombinasyonları üretir.)</i>
</p>

</div>


---

<h4 align="left"> Viseme Tabanlı Dudak Senkronizasyonu</h4>

EmotiVoice Studio, **viseme** tabanlı konuşma animasyonu sistemine sahiptir.  
Visemeler, sesli konuşmadaki harf seslerinin (fonemlerin) görsel karşılığı olan dudak şekilleridir.  

![viseme](Documentation/charts/viseme.png)

Örneğin:

| Ses (Fonem) | Görsel Dudak Şekli (Viseme) |
|--------------|-----------------------------|
| "AA", "AH", "AE" | Ağız geniş açık |
| "IY", "EE" | Dudak yatay gergin |
| "UW", "OO" | Dudaklar ileri ve yuvarlak |
| "F", "V" | Üst dişler alt dudağa temas eder |
| "M", "B", "P" | Dudaklar kapalı |
| – | **REST (Nötr)** konum |

<h4 align="left"> Hareketli video Çıktı üretimi</h4>

Whisper modeli, ses dosyasındaki kelimeleri ve zaman etiketlerini çıkarır.
Bu bilgiler, viseme (ağız şekli) karşılıklarına dönüştürülür.
Her viseme için uygun ağız görseli seçilerek belirli kare aralıklarında video oluşturulur.
Bu işlem sonunda zaman uyumlu bir ağız hareket dizisi elde edilir.

Örnek Çıktı

---

<h2 align="left"> 7. Gelecek Geliştirmeler</h2>

- **Hibrit Duygu Analizi:**
Sesin ton, ritim, vurgu ve frekans özelliklerini de analiz ederek duyguyu çok boyutlu biçimde tespit eden yeni bir modelin eklenmesi.
- **Gerçek Zamanlı (Live) Duygu Takibi:**
Kullanıcının konuşmasını anlık olarak analiz eden ve aynı anda avatarın yüz ifadesini senkronize eden bir canlı etkileşim modunun geliştirilmesi.
- **Konuşma Tarzı ve Persona Ayarları:**
Farklı karakter tarzlarına (örneğin “profesyonel”, “samimi”, “robotik”) göre sesin tempo, tonlama ve vurgu yapısının ayarlanabilmesi.
- **Yeni Dil Desteği:**
Türkçe ve İngilizce dışında yeni diller (örneğin Almanca, Fransızca, Arapça) için çok dilli model yapısının genişletilmesi.
- **3D Avatar ve Gerçekçi Hareketler:**
2D katman tabanlı sistemin Unity tabanlı 3D yüz ifadeleriyle geliştirilmesi; göz kırpma, nefes alma gibi mikro hareketlerin eklenmesi.
