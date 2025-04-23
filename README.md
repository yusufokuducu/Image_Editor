# Pro Image Editor (Gelişmiş Görsel Düzenleyici)

Python ve customtkinter ile geliştirilmiş, modern tasarımlı, güçlü bir görsel düzenleme uygulaması.

![Pro Image Editor](resources/app_icon.png)

## Özellikler

- **Modern Karanlık Arayüz**: Customtkinter ile özelleştirilmiş, kullanıcı dostu arayüz
- **Dosya İşlemleri**:
  - Görsel açma (JPEG, PNG, BMP ve diğer formatlar)
  - Düzenlenen görseli farklı formatlarda kaydetme 
  - Orijinal görsele dönme
  
- **Temel Görsel Ayarları**:
  - Parlaklık kontrolü (0.0 - 2.0)
  - Kontrast kontrolü (0.0 - 2.0)
  - Doygunluk kontrolü (0.0 - 2.0)
  
- **Dönüştürme Seçenekleri**:
  - Sola/sağa 90° döndürme
  - Yatay/dikey çevirme
  
- **Temel Filtreler**:
  - Bulanıklaştırma (Blur)
  - Keskinleştirme (Sharpen)
  - Kontur (Contour)
  - Kabartma (Emboss)
  - Siyah-Beyaz
  - Negatif (Renk Tersine Çevirme)
  
- **Gelişmiş Filtreler**:
  - **Sepya Tonu**: Nostaljik bir görünüm için ayarlanabilir yoğunluk
  - **Çizgi Film Efekti**: Animasyon benzeri görünüm, kenar belirginliği ve renk sadeleştirme ayarları
  - **Vinyet Efekti**: Köşe kararma efekti ile dramatik odaklama
  - **Pikselleştirme**: Piksel boyutu ayarlanabilir mozaik efekti
  - **Renk Sıçratma**: Seçilen renk kanalını koruyarak diğer kanalları siyah-beyaz yapma
  - **Yağlı Boya**: Fırça boyutu ve detay seviyesi ayarlanabilir yağlı boya efekti
  - **Gürültü Efekti**: Çeşitli tipte (Uniform, Gaussian, Salt & Pepper) gürültü efektleri ve kanal seçimleri
  
- **Efekt Uygulaması**:
  - Önizleme özelliği ile değişiklikler uygulanmadan görüntüleme
  - Ayarlanabilir efekt parametreleri
  - Çoklu iş parçacığı (multithreading) desteği ile yüksek performans

## Gereksinimler

- Python 3.7 veya üzeri
- Gerekli paketler:
  - customtkinter >= 5.2.0
  - Pillow >= 10.0.0
  - numpy >= 1.24.0
  - opencv-python >= 4.8.0

## Kurulum

1. Sisteminizde Python'un kurulu olduğundan emin olun
2. Gerekli paketleri yükleyin:

```
pip install -r requirements.txt
```

3. Uygulamayı çalıştırın:

```
python run.py
```

## Kullanım

1. **Görsel Açma**: "Dosya Aç" düğmesine tıklayarak bir görsel açın
2. **Temel Ayarlar**: Parlaklık, kontrast ve doygunluk kaydırıcılarını kullanarak temel ayarları yapın
3. **Temel Filtreler**: Filtreler bölümündeki düğmelere tıklayarak doğrudan uygulayın
4. **Gelişmiş Filtreler**: 
   - İstediğiniz efekti seçin (örn. "Yağlı Boya", "Gürültü" vb.)
   - Yan panelde açılan ayarlar ile efekt parametrelerini yapılandırın
   - Önizleme seçeneğini işaretleyerek sonucu görebilirsiniz
   - "Efekti Uygula" düğmesine tıklayarak kalıcı olarak uygulayın
5. **Dönüştürme İşlemleri**: Döndürme ve çevirme düğmelerini kullanarak görselin yönünü değiştirin
6. **Kaydetme**: "Kaydet" düğmesi ile düzenlenen görseli istediğiniz formatta kaydedin
7. **Sıfırlama**: "Sıfırla" düğmesi ile orijinal görsele geri dönün

## Modüler Yapı

Uygulama, bakım ve geliştirme kolaylığı için modüler bir yapıda tasarlanmıştır:

```
image_editor_app/           # Ana paket dizini
├── __init__.py             # Paket başlatıcı
├── app.py                  # Ana ImageEditor sınıfı
├── core/                   # Çekirdek işlevler
│   ├── __init__.py
│   ├── basic_adjustments.py
│   ├── effect_processing.py
│   ├── file_operations.py
│   └── image_display.py
├── ui/                     # Kullanıcı arayüzü bileşenleri
│   ├── __init__.py
│   ├── effects.py
│   ├── main_view.py
│   └── sidebar.py
├── utils/                  # Yardımcı işlevler
│   ├── __init__.py
│   ├── constants.py
│   ├── advanced_effects.py
│   ├── app_icon.py
│   └── image_effects.py
└── widgets/                # Özel arayüz bileşenleri
    ├── __init__.py
    ├── effect_intensity.py
    ├── toggle_button.py
    └── tooltip.py
```

## Lisans

Bu yazılım açık kaynaklıdır ve MIT lisansı altında dağıtılmaktadır. 