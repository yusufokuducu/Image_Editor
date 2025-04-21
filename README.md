# Image_Editor

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-brightgreen.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)

## 📋 İçerik

- [Genel Bakış](#genel-bakış)
- [Özellikler](#özellikler)
- [Ekran Görüntüleri](#ekran-görüntüleri)
- [Kurulum](#kurulum)
- [Kullanım](#kullanım)
- [Araçlar](#araçlar)
- [Proje Yapısı](#proje-yapısı)
- [Yol Haritası](#yol-haritası)
- [Katkı Sağlama](#katkı-sağlama)
- [Lisans](#lisans)
- [İletişim](#iletişim)

## 🔭 Genel Bakış

Image_Editor, Python ile geliştirilmiş, profesyonel kalitede bir görüntü düzenleme uygulamasıdır. CustomTkinter, PIL (Pillow), NumPy ve OpenCV gibi güçlü kütüphaneleri temel alan bu uygulama, gelişmiş görüntü işleme özellikleri ve kullanıcı dostu arayüzüyle öne çıkar.

Bu proje, hem profesyonel fotoğrafçılar hem de hobi olarak fotoğrafçılıkla ilgilenenler için kapsamlı bir görüntü düzenleme çözümü sunmayı amaçlamaktadır.

## ✨ Özellikler

### Görüntü İşleme
- **Temel Düzenlemeler**: Kırpma, döndürme, çevirme, yeniden boyutlandırma
- **Renk Ayarlamaları**: Parlaklık, kontrast, doygunluk, renk tonu
- **Katmanlar**: Çoklu katman desteği, karıştırma modları, opaklık ayarları
- **Filtreler**: Bulanıklaştırma, keskinleştirme, kenar algılama, gürültü azaltma
- **Seçim Araçları**: Dikdörtgen, elips, serbest el ve renk tabanlı seçiciler

### Kullanıcı Arayüzü
- **Modern Tasarım**: CustomTkinter ile oluşturulmuş çağdaş arayüz
- **Özelleştirilebilir Çalışma Alanı**: Panel yerleşimlerini özelleştirme
- **Karanlık/Açık Mod**: Sistem ayarlarına uyumlu tema seçenekleri
- **Araç Çubukları**: Sezgisel olarak organize edilmiş araçlar

### Dosya İşlemleri
- **Birden Çok Format Desteği**: JPG, PNG, TIFF, BMP, GIF, WebP
- **Proje Dosyaları**: Katmanlar ve düzenleme geçmişini içeren kaydetme/yükleme
- **Toplu İşleme**: Birden çok dosya üzerinde aynı işlemleri uygulama

## 📸 Ekran Görüntüleri

*Ekran görüntüleri ekleme yeri*

## 🚀 Kurulum

### Gereksinimler
- Python 3.8 veya üstü
- pip (Python paket yöneticisi)

### Kurulum Adımları

1. Repo'yu klonlayın:
   ```bash
   git clone https://github.com/kullanıcıadı/Image_Editor.git
   cd Image_Editor
   ```

2. Sanal ortam oluşturun (isteğe bağlı):
   ```bash
   python -m venv venv
   # Windows'ta
   venv\Scripts\activate
   # macOS/Linux'ta
   source venv/bin/activate
   ```

3. Gerekli paketleri yükleyin:
   ```bash
   pip install -r requirements.txt
   ```

4. Uygulamayı başlatın:
   ```bash
   python main.py
   ```

## 📖 Kullanım

### Temel Kullanım
1. Yeni bir görüntü oluşturun veya mevcut bir dosyayı açın
2. Araç çubuğundan istediğiniz düzenleme aracını seçin
3. Görüntü üzerinde seçilen aracı kullanın
4. Değişiklikleri uygulayın ve kaydedin

### Katmanlarla Çalışma
1. Yeni katman eklemek için katmanlar panelinden "+" düğmesine tıklayın
2. Katmanlar arasında gezinmek için katman listesinden seçim yapın
3. Karıştırma modlarını ve opaklığı ayarlamak için katman özelliklerini kullanın

### Filtre ve Efektler
1. Filtreler menüsünden istediğiniz efekti seçin
2. Ayarları özelleştirin ve önizlemeyi kontrol edin
3. Değişiklikleri uygulamak için "Uygula" düğmesine tıklayın

## 🧰 Araçlar

- **Seçim Araçları**: Dikdörtgen, elips, kement, sihirli değnek
- **Düzenleme Araçları**: Fırça, silgi, dolgu, metin, kırpma, taşıma
- **Filtreler**: Bulanıklaştırma, keskinleştirme, gürültü azaltma
- **Ayarlamalar**: Parlaklık/kontrast, HSL, seviyelendirme, eğriler

## 📂 Proje Yapısı

```
Image_Editor/
├── core/                  # Çekirdek işlevsellik
│   ├── app_state.py       # Uygulama durum yönetimi
│   ├── image_handler.py   # Görüntü işleme işlevleri
│   └── layer_manager.py   # Katman yönetimi
├── ui/                    # Kullanıcı arayüzü
│   ├── canvas.py          # Düzenleme tuvali
│   ├── main_window.py     # Ana uygulama penceresi
│   ├── menubar.py         # Uygulama menüsü
│   ├── toolbar.py         # Araç çubuğu
│   └── panels/            # UI panelleri
├── operations/            # Görüntü işleme operasyonları
│   ├── adjustments/       # Renk ayarlamaları
│   ├── effects/           # Görsel efektler
│   ├── filters/           # Filtreler
│   └── transformations/   # Dönüşümler
├── tools/                 # Düzenleme araçları
├── resources/             # Uygulama kaynakları
├── utils/                 # Yardımcı işlevler
├── config/                # Yapılandırma dosyaları
├── main.py                # Ana giriş noktası
└── requirements.txt       # Bağımlılıklar
```

## 🗺️ Yol Haritası

- [ ] Gelişmiş seçim araçları (manyetik kement, kenar algılama)
- [ ] Ayarlama katmanları ve yıkıcı olmayan düzenleme desteği
- [ ] Katman maskeleri ve efektleri
- [ ] Fırça motoru iyileştirmeleri
- [ ] Makro ve eylem kaydetme
- [ ] İçerik duyarlı dolgu ve silme
- [ ] GPU hızlandırma
- [ ] Renk profilleri desteği
- [ ] Eklenti sistemi
- [ ] Komut dosyası otomasyonu

## 👥 Katkı Sağlama

Katkıda bulunmak isterseniz:

1. Repo'yu forklayın
2. Özellik dalı oluşturun (`git checkout -b feature/amazing-feature`)
3. Değişikliklerinizi commitleyin (`git commit -m 'Add some amazing feature'`)
4. Dalınıza pushlayın (`git push origin feature/amazing-feature`)
5. Pull Request açın

## 📄 Lisans

Bu proje MIT Lisansı altında lisanslanmıştır - ayrıntılar için [LICENSE](LICENSE) dosyasına bakın.

## 📞 İletişim

Proje Yöneticisi - [@kullanıcıadı](https://github.com/kullanıcıadı)

Proje Linki: [https://github.com/kullanıcıadı/Image_Editor](https://github.com/kullanıcıadı/Image_Editor) 