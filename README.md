# Gelişmiş Görsel Düzenleyici

Python ve customtkinter ile oluşturulmuş, modern karanlık temalı bir arayüze ve gelişmiş görsel işleme özelliklerine sahip güçlü bir görsel düzenleme uygulaması.

## Özellikler

- **Modern Karanlık Arayüz**: Customtkinter ile temiz, modern arayüz
- **Temel Görsel İşlemleri**: Görsel açma, kaydetme ve sıfırlama
- **Temel Filtreler**: Bulanıklaştırma, keskinleştirme, kontur, kabartma, siyah-beyaz, ters çevirme
- **Gelişmiş Filtreler**: 
  - Sepia tonu
  - Çizgi film efekti
  - Vinyet efekti
  - Pikselleştirme
  - Renk sıçratma (kırmızı, yeşil, mavi kanallar)
  - Yağlı boya efekti
  - Gürültü (rastgele doku)
- **Ayarlanabilir Efekt Yoğunluğu**: Her efektin gücünü kaydırıcılarla kontrol etme
- **Efekt Önizleme**: Efektleri uygulamadan önce önizleme yapabilme
- **Görsel Ayarlamaları**:
  - Parlaklık kontrolü
  - Kontrast kontrolü
  - Doygunluk kontrolü
- **Dönüştürme Seçenekleri**:
  - Sola/sağa döndürme
  - Yatay/dikey çevirme

## Gereksinimler

- Python 3.6+
- Gerekli paketler:
  - customtkinter
  - Pillow (PIL)
  - numpy

## Kurulum

1. Sisteminizde Python'un kurulu olduğundan emin olun
2. Gerekli paketleri yükleyin:

```
pip install customtkinter pillow numpy
```

3. Uygulamayı çalıştırın:

```
python image_editor.py
```

## Kullanım

1. "Open Image" düğmesini kullanarak bir görsel açın
2. Temel filtreleri tek tıklamayla doğrudan uygulayın
3. Gelişmiş filtreler için:
   - Gelişmiş Filtreler bölümünden filtreyi seçin
   - Kaydırıcıları kullanarak filtre yoğunluğunu ayarlayın
   - Önizleme seçeneğini işaretleyerek efekti görebilirsiniz
   - "Efekti Uygula" düğmesine tıklayarak görselinize uygulayın
4. Parlaklık, kontrast ve doygunluğu gerektiği gibi ayarlayın
5. Düzenlediğiniz görseli "Save Image" düğmesi ile kaydedin
6. "Reset Image" düğmesi ile her zaman orijinal görsele dönebilirsiniz

## Gelişmiş Filtre Detayları

- **Sepia**: Vintage bir görünüm için sıcak kahverengi ton uygular
- **Çizgi Film**: Çizgi film benzeri bir efekt için renkleri sadeleştirir ve kenarları belirginleştirir
- **Vinyet**: Dramatik bir odak için görüntünün köşelerini karartır
- **Pikselleştirme**: Piksel boyutunu ayarlayarak bloklu bir efekt oluşturur
- **Renk Sıçratma**: Sadece seçili renk kanalını koruyarak diğerlerini gri tonlamalı yapar
- **Yağlı Boya**: Renk frekanslarını analiz ederek yağlı boya efekti oluşturur
- **Gürültü**: Görsele ayarlanabilir yoğunlukta rastgele doku/gürültü ekler

## Proje Yapısı

- `image_editor.py` - Ana uygulama dosyası
- `advanced_filters.py` - Gelişmiş filtre uygulamalarını içeren modül
- `app_icon.py` - Özel uygulama simgesi oluşturur
- `resources/` - Uygulama kaynakları için dizin 