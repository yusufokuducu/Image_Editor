# PyxelEdit

![PyxelEdit Demo](Kayıt%202025-04-25%20171443.gif)

## Advanced Layer-Based Python Image Editor

PyxelEdit is an open-source raster image editor developed for Windows with a modern PyQt6 interface, powerful layer management, advanced filter/effect infrastructure, and flexible architecture. It provides a fast, modular, and extensible platform for graphic designers, pixel artists, and software developers.

### Key Features

- **Modern PyQt6 Interface:** Fast, intuitive, and scalable user experience
- **Layer System:** Unlimited layer addition, deletion, copying, moving, visibility control, and merging
- **Advanced Selection Tools:** Rectangle, ellipse, and free (lasso) selection modes
- **Layer Panel:** Select layers from list, drag-and-drop ordering, quick copy/paste
- **Filters & Effects:**
  - Blur (user-adjustable level)
  - Sharpen
  - Edge Highlight
  - Grayscale
  - Add Noise (user-adjustable level)
  - Brightness/Contrast/Saturation/Hue adjustment
- **Undo/Redo:** Comprehensive undo/redo with command history for all operations
- **Shortcuts:** Extensive and customizable keyboard shortcuts for quick access
- **Layer-Based Processing:** Effects and filters can be applied only to selected/active layer
- **Extensible Infrastructure:** New filters, tools, or layer features can be easily added
- **Debugging & Logging:** Automatic logging and error management
- **Multiple Image Format Support:** PNG, JPEG, BMP, GIF, and more

### Installation

1. **Python 3.10+** must be installed
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Quick Start

```bash
python src/main.py
```

### User Guide

#### Basic Functions

- **Open/Save Image:** From File menu or with Ctrl+O/Ctrl+S
- **Add/Delete Layer:** From Layers menu or panel
- **Move/Copy Layer:** Up/down arrows or copy/paste buttons in layer panel
- **Apply Effect:** From Filters menu, with level selection for blur and noise
- **Selection Tools:** Rectangle/ellipse/lasso selection from Selection menu
- **Undo/Redo:** Ctrl+Z / Ctrl+Y
- **Layer Visibility:** From layer panel or with Ctrl+H
- **Merge Layers:** Merge all visible layers into a single layer with Ctrl+M
- **Add Text:** Add text to layers with the text tool, select font and size

#### Advanced Features

- **Layer-Based Effects:** Each filter and effect is applied only to the selected layer, other layers remain unaffected
- **Live Preview:** Real-time preview support for filter and effect applications
- **Command History:** Detailed undo/redo support and operation history for all actions
- **Multiple Image Formats:** Export and save in different formats
- **Comprehensive Shortcuts:** Customizable shortcuts for all basic and advanced operations

### Keyboard Shortcuts

| Operation                  | Shortcut          |
|----------------------------|-------------------|
| **File Operations**        |                   |
| Open Image                 | Ctrl+O            |
| Save Image                 | Ctrl+S            |
| Save As                    | Ctrl+Shift+S      |
| Exit                       | Ctrl+Q            |
| **Edit Operations**        |                   |
| Undo                       | Ctrl+Z            |
| Redo                       | Ctrl+Y            |
| **Selection**              |                   |
| Select All                 | Ctrl+A            |
| Clear Selection            | Ctrl+D            |
| Make Selection             | Alt+Drag          |
| Add to Selection           | Alt+Shift+Drag    |
| Subtract from Selection    | Alt+Ctrl+Drag     |
| **Layer Operations**       |                   |
| New Layer                  | Ctrl+Shift+N      |
| Delete Layer               | Del               |
| Move Layer Up/Down         | Ctrl+Up / Ctrl+Down |
| Merge Layers               | Ctrl+M            |
| Layer Visibility           | Ctrl+H            |
| **Tools**                  |                   |
| Selection Tool             | V                 |
| Brush Tool                 | B                 |
| Pencil Tool                | P                 |
| Eraser Tool                | E                 |
| Fill Tool                  | G                 |
| Text Tool                  | T                 |
| **Zoom & Navigation**      |                   |
| Zoom In                    | Ctrl++            |
| Zoom Out                   | Ctrl+-            |
| Fit to Window              | Ctrl+0            |
| Reset Zoom                 | R                 |
| Pan (temporary)            | Space (hold)      |
| Filter Menu                | F                 |

### Architecture and Developer Notes

- **Modular Code:**
  - `src/main.py`: Main application and interface launcher
  - `src/layers.py`: Layer management and merging
  - `src/layer_panel.py`: Layer panel and user interaction
  - `src/filters.py`: Filter and effect functions
  - `src/transform.py`: Transformation and resizing operations
  - `src/image_io.py`: Image loading/saving, QPixmap conversions
  - `src/history.py`: Command-based undo/redo infrastructure
  - `src/image_view.py`: Viewing and selection tools
  - `src/text_options.py`: Text tool and font management
- **Extensibility:** Extend relevant modules to add new filters, tools, or layer functions
- **Logging:** All main operations are logged to `pyxeledit.log` file

### Tests

- Verify basic functionality with test modules included with the project
- For tests:
  ```bash
  pytest
  ```

### Frequently Asked Questions (FAQ)

**Q: I'm getting an error when adding a layer, why?**

A: You must first open an image or create at least one layer. Layer addition requires an existing base layer.

**Q: Why do filters only work on the selected layer?**

A: All effects and filters are applied only to the active layer for flexible and lossless editing. Other layers remain unaffected.

**Q: On which platforms does it run?**

A: It has been fully tested on Windows. It may also work on Linux/Mac with PyQt6 and Pillow support, but there may be interface differences.

### GPU Support

This project now supports external GPU acceleration, providing significant speed improvements in image processing and filtering operations.

#### Using GPU Features

- The program automatically detects and uses available GPU at startup
- To change GPU settings, follow "Settings → GPU Settings" in the top menu
- If multiple GPUs are available, select your preferred GPU from "GPU Settings → Select GPU Device" menu
- To completely disable GPU usage, uncheck the "Use GPU" option

#### Command Line Parameters

You can use command line parameters to start the program with a specific GPU or disable GPU usage:

```bash
# To start with a specific GPU (ID number starts from 0)
python src/main.py --gpu 0

# To disable GPU usage
python src/main.py --cpu
```

#### System Requirements for GPU Support

- NVIDIA CUDA compatible GPU
- CUDA Toolkit (11.x or higher recommended)
- PyTorch 2.0.0 or higher
- CuPy library

### License

Open source under MIT License.

### Contribution and Feedback

Contribute by opening pull requests and issues!

Developer: faust-lvii - [yusufokuducu](mailto:k.yusufokuducu@gmail.com)

---

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
| **Dosya İşlemleri**         |                   |
| Resim Aç                    | Ctrl+O            |
| Resim Kaydet                | Ctrl+S            |
| Farklı Kaydet               | Ctrl+Shift+S      |
| Çıkış                       | Ctrl+Q            |
| **Düzenleme İşlemleri**     |                   |
| Geri Al (Undo)              | Ctrl+Z            |
| Yinele (Redo)               | Ctrl+Y            |
| **Seçim**                   |                   |
| Tümünü Seç                  | Ctrl+A            |
| Seçimi Temizle              | Ctrl+D            |
| Seçim Yap                   | Alt+Sürükle       |
| Seçime Ekle                 | Alt+Shift+Sürükle |
| Seçimden Çıkar              | Alt+Ctrl+Sürükle  |
| **Katman İşlemleri**        |                   |
| Yeni Katman                 | Ctrl+Shift+N      |
| Katmanı Sil                 | Del               |
| Katmanı Yukarı/Aşağı Taşı   | Ctrl+Up / Ctrl+Down |
| Katmanları Birleştir        | Ctrl+M            |
| Katman Görünürlüğü          | Ctrl+H            |
| **Araçlar**                 |                   |
| Seçim Aracı                 | V                 |
| Fırça Aracı                 | B                 |
| Kalem Aracı                 | P                 |
| Silgi Aracı                 | E                 |
| Doldurma Aracı              | G                 |
| Metin Aracı                 | T                 |
| **Zoom ve Gezinme**         |                   |
| Yakınlaştır                 | Ctrl++            |
| Uzaklaştır                  | Ctrl+-            |
| Pencereye Sığdır            | Ctrl+0            |
| Zoom Sıfırla                | R                 |
| Gezinme (geçici)            | Space (basılı tut)|

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

## GPU Desteği

Bu proje artık harici GPU ile çalışabilir, bu da görüntü işleme ve filtreleme işlemlerinde önemli ölçüde hız artışı sağlar.

### GPU Özelliklerinin Kullanımı

- Program başlangıçta otomatik olarak mevcut GPU'yu tespit eder ve kullanır
- GPU ayarlarını değiştirmek için üst menüdeki "Ayarlar → GPU Ayarları" yolunu izleyin
- Birden fazla GPU varsa, "GPU Ayarları → GPU Cihazı Seç" menüsünden istediğiniz GPU'yu seçebilirsiniz
- GPU kullanımını tamamen kapatmak için "GPU Kullan" seçeneğinin işaretini kaldırın

### Komut Satırı Parametreleri

Programı belirli bir GPU ile başlatmak veya GPU kullanımını devre dışı bırakmak için komut satırı parametrelerini kullanabilirsiniz:

```bash
# Belirli bir GPU ile başlatmak için (ID numarası 0'dan başlar)
python src/main.py --gpu 0

# GPU kullanımını devre dışı bırakmak için
python src/main.py --cpu
```

### Sistem Gereksinimleri

GPU desteği için aşağıdaki gereksinimler gereklidir:

- NVIDIA CUDA uyumlu bir GPU
- CUDA Toolkit (11.x veya üzeri önerilen)
- PyTorch 2.0.0 veya üzeri
- CuPy kütüphanesi

---

## Lisans

MIT Lisansı altında açık kaynak.

---

## Katkı ve Geri Bildirim

Pull request ve issue açarak katkıda bulunabilirsiniz!

Geliştirici: faust-lvii - [yusufokuducu](mailto:k.yusufokuducu@gmail.com)
