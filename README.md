# PyxelEdit

**Gelişmiş, Katman Destekli Python Görüntü Editörü**

PyxelEdit; modern PyQt6 arayüzü, güçlü katman yönetimi, gelişmiş filtre/efekt altyapısı ve esnek mimarisiyle Windows için geliştirilmiş açık kaynaklı bir raster imaj editörüdür. Grafik tasarımcılar, piksel sanatçılar ve yazılım geliştiriciler için hızlı, modüler ve geliştirilebilir bir platform sunar.

---

## Özellikler

- **Modern PyQt6 Arayüzü:** Hızlı, sezgisel ve ölçeklenebilir kullanıcı deneyimi.
- **Katman Sistemi:** Sınırsız katman ekleme, silme, kopyalama, taşıma, görünürlük ve birleştirme.
- **Gelişmiş Seçim Araçları:** Dikdörtgen, elips ve serbest (lasso) seçim modları.
- **Katman Paneli:** Katmanları listeden seçme, sürükle-bırak ile sıralama, hızlı kopyalama/yapıştırma.
- **Filtreler & Efektler:**
  - Bulanıklaştır (kullanıcı ayarlı seviye)
  - Keskinleştir
  - Kenar Vurgula
  - Gri Ton
  - Noise Ekle (kullanıcı ayarlı seviye)
  - Parlaklık/Kontrast/Doygunluk/Açı ayarı
- **Geri Al/Yinele (Undo/Redo):** Tüm işlemler için komut geçmişiyle tam kapsamlı geri alma/yineleme.
- **Kısa Yollar:** Hızlı erişim için kapsamlı ve özelleştirilebilir klavye kısayolları.
- **Katman Bazlı İşlem:** Efekt ve filtreler sadece seçili/aktif katmana uygulanabilir.
- **Geliştirilebilir Altyapı:** Yeni filtre, araç veya katman özelliği kolayca eklenebilir.
- **Hata Ayıklama & Loglama:** Otomatik loglama ve hata yönetimi.
- **Çoklu Görüntü Formatı Desteği:** PNG, JPEG, BMP, GIF ve daha fazlası.

---

![PyxelEdit Kullanım Örneği](Kayıt%202025-04-25%20171443.gif)

---

## Kurulum

1. **Python 3.10+** kurulu olmalı.
2. Bağımlılıkları yükleyin:
   ```bash
   pip install -r requirements.txt
   ```

---

## Hızlı Başlangıç

```bash
python src/main.py
```

---

## Kullanım Kılavuzu

### Temel İşlevler

- **Resim Aç/Kaydet:** Dosya menüsünden veya Ctrl+O/Ctrl+S ile.
- **Katman Ekle/Sil:** Katmanlar menüsünden veya panelden.
- **Katmanı Taşı/Kopyala:** Katman panelinde yukarı/aşağı oklar veya kopyala/yapıştır butonları.
- **Efekt Uygulama:** Filtreler menüsünden, bulanıklık ve noise için seviye seçimiyle.
- **Seçim Araçları:** Seçim menüsünden dikdörtgen/elips/lasso seçimi.
- **Undo/Redo:** Ctrl+Z / Ctrl+Y.
- **Katman Görünürlüğü:** Katman panelinden veya Ctrl+H ile.
- **Katmanları Birleştir:** Ctrl+M ile tüm görünür katmanları tek katmanda birleştir.
- **Metin Ekleme:** Metin aracıyla katmanlara yazı ekleyin, yazı tipi ve boyutunu seçin.

### Gelişmiş Özellikler

- **Katman Bazlı Efektler:** Her filtre ve efekt sadece seçili katmana uygulanır, diğer katmanlar etkilenmez.
- **Canlı Önizleme:** Filtre ve efekt uygulamalarında gerçek zamanlı önizleme desteği.
- **Komut Geçmişi:** Tüm işlemler için detaylı geri al/yinele desteği ve işlem geçmişi.
- **Çoklu Görüntü Formatı:** Farklı formatlarda dışa aktarım ve kaydetme.
- **Kapsamlı Kısayollar:** Tüm temel ve gelişmiş işlemler için özelleştirilebilir kısayollar.

---

## Klavye Kısayolları

| İşlem                       | Kısayol           |
|-----------------------------|-------------------|
| Geri Al (Undo)              | Ctrl+Z            |
| Yinele (Redo)               | Ctrl+Y            |
| Yeni Katman                 | Ctrl+Shift+N      |
| Katmanı Sil                 | Del               |
| Katmanı Yukarı/Aşağı Taşı   | Ctrl+Up / Ctrl+Down |
| Katmanları Birleştir        | Ctrl+M            |
| Katman Görünürlüğü          | Ctrl+H            |
| Resim Aç                    | Ctrl+O            |
| Resim Kaydet                | Ctrl+S            |
| Seçim Modu (Dikdörtgen)     | R                 |
| Seçim Modu (Elips)          | E                 |
| Seçim Modu (Lasso)          | L                 |
| Metin Aracı                 | T                 |
| Filtre Menüsü               | F                 |

---

## Mimarî ve Geliştirici Notları

- **Kod Modülerdir:**
  - `src/main.py`: Ana uygulama ve arayüz başlatıcı.
  - `src/layers.py`: Katman yönetimi ve birleştirme.
  - `src/layer_panel.py`: Katman paneli ve kullanıcı etkileşimi.
  - `src/filters.py`: Filtre ve efekt fonksiyonları.
  - `src/transform.py`: Dönüşüm ve boyutlandırma işlemleri.
  - `src/image_io.py`: Görüntü yükleme/kaydetme, QPixmap dönüşümleri.
  - `src/history.py`: Komut tabanlı undo/redo altyapısı.
  - `src/image_view.py`: Görüntüleme ve seçim araçları.
  - `src/text_options.py`: Metin aracı ve yazı tipi yönetimi.
- **Genişletilebilirlik:** Yeni filtreler, araçlar veya katman fonksiyonları eklemek için ilgili modülleri genişletin.
- **Loglama:** Tüm ana işlemler `pyxeledit.log` dosyasına kaydedilir.

---

## Testler

- Proje ile birlikte gelen test modülleriyle temel işlevleri doğrulayabilirsiniz.
- Testler için:
  ```bash
  pytest
  ```

---

## Sıkça Sorulan Sorular (SSS)

**S: Katman eklerken hata alıyorum, neden?**

C: Önce bir resim açmalı veya en az bir katman oluşturmalısınız. Katman ekleme işlemi, mevcut bir taban katman gerektirir.

**S: Filtreler neden sadece seçili katmanda çalışıyor?**

C: Tüm efektler ve filtreler, esnek ve kayıpsız düzenleme için sadece aktif katmanda uygulanır. Diğer katmanlar etkilenmez.

**S: Hangi platformlarda çalışır?**

C: Şu an için Windows üzerinde tam test edilmiştir. PyQt6 ve Pillow desteğiyle Linux/Mac'te de çalışabilir, ancak arayüz farklılıkları olabilir.

---

## Lisans

MIT Lisansı altında açık kaynak.

---

## Katkı ve Geri Bildirim

Pull request ve issue açarak katkıda bulunabilirsiniz!

Geliştirici: faust-lvii - [yusufokuducu](mailto:k.yusufokuducu@gmail.com)

---
