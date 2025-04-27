# Kodun Modülerleştirilmesi ve Bölme Planı

Bu dokümanda, `src/main.py` dosyasının daha sürdürülebilir ve okunabilir bir yapıya kavuşturulması için önerilen modülerleştirme/bölme planı yer almaktadır.

---

## 1. Ana Pencere ve Uygulama Girişi
- `main.py` sadece uygulama giriş noktası (`main()` fonksiyonu ve `if __name__ == '__main__':` bloğu) ve ana pencereyi başlatacak kodu içerecek.
- `MainWindow` sınıfı ayrı bir dosyaya alınacak: `main_window.py`

## 2. Diyaloglar ve UI Bileşenleri
- `FilterSliderDialog` gibi özel diyaloglar ayrı bir dosyaya taşınacak: `dialogs.py`
- Diğer özel UI bileşenleri (ör: katman paneli, efekt paneli) zaten ayrı dosyalarda, bu yapı korunacak.

## 3. Menü ve Eylemler
- Menü ve eylem (action) tanımlamaları, ana pencereyle ilgili oldukları için `main_window.py` içinde kalabilir.
- Eğer menü çok karmaşıksa, menü oluşturma fonksiyonları ayrı bir dosyaya (ör: `menu.py`) alınabilir.

## 4. Filtre ve Görüntü İşlemleri
- Filtre uygulama, önizleme, görsel işleme gibi fonksiyonlar ayrı bir yardımcı dosyada toplanacak: `image_processing.py` veya `filter_utils.py`
- Her bir filtre veya işlem için ayrı fonksiyonlar ve yardımcılar burada bulunacak.

## 5. Katman ve Geçmiş Yönetimi
- Katman yönetimi (`LayerManager`), geçmiş yönetimi (`History`, `Command`) zaten ayrı dosyalarda, bu yapıyı koruyun.

## 6. Yardımcı Fonksiyonlar ve Sabitler
- Sık kullanılan yardımcı fonksiyonlar ve sabitler için `utils.py` veya `constants.py` gibi dosyalar oluşturulabilir.

---

### Önerilen Dosya Yapısı

```
src/
│
├── main.py                # Sadece uygulama giriş noktası
├── main_window.py         # MainWindow ve UI kurulumları
├── dialogs.py             # Özel diyaloglar (ör: FilterSliderDialog)
├── menu.py                # Menü oluşturma (isteğe bağlı)
├── image_processing.py    # Filtre ve görsel işlemler yardımcıları
├── utils.py               # Yardımcı fonksiyonlar
├── constants.py           # Sabitler (isteğe bağlı)
├── image_io.py
├── image_view.py
├── filters.py
├── transform.py
├── history.py
├── layers.py
├── layer_panel.py
├── effects_panel.py
└── ...
```

---

### Sonraki Adımlar
1. Öncelikle `MainWindow` ve diyalog sınıflarını kendi dosyalarına taşıyın.
2. Filtre ve görsel işleme ile ilgili fonksiyonları yardımcı dosyaya ayırın.
3. Gerekirse menü ve yardımcı fonksiyonlar için ek dosyalar oluşturun.
4. Her dosyada uygun import ve bağlantıları güncelleyin.

---

Bu plan, projenin daha sürdürülebilir, okunabilir ve geliştirilebilir olmasını amaçlamaktadır.

---

## Prompt Format (EN/TR)

### English Prompt

You are given a large and monolithic `src/main.py` file from a Python PyQt6 image editor project. Your task is to modularize and refactor the codebase for better maintainability and readability. Use the following plan as a guideline:

1. Move the application entry point (`main()` function and `if __name__ == '__main__':` block) to `main.py` only, and move the `MainWindow` class to a new file: `main_window.py`.
2. Move special dialogs (such as `FilterSliderDialog`) to a separate file: `dialogs.py`.
3. Keep menu and action definitions in `main_window.py`, but if the menu logic is too complex, move it to a dedicated file (e.g., `menu.py`).
4. Collect all filter application, preview, and image processing functions into a helper file: `image_processing.py` or `filter_utils.py`.
5. Keep layer and history management in their own files as they already are.
6. Create `utils.py` or `constants.py` for common helpers and constants if needed.

Recommended directory structure:

```
src/
│
├── main.py                # Only the application entry point
├── main_window.py         # MainWindow and UI setup
├── dialogs.py             # Custom dialogs (e.g., FilterSliderDialog)
├── menu.py                # Menu creation (optional)
├── image_processing.py    # Image processing helpers
├── utils.py               # Utility functions
├── constants.py           # Constants (optional)
├── image_io.py
├── image_view.py
├── filters.py
├── transform.py
├── history.py
├── layers.py
├── layer_panel.py
├── effects_panel.py
└── ...
```

Follow these steps:
1. Move `MainWindow` and dialog classes to their own files.
2. Move filter/image processing functions to a helper file.
3. Create additional files for menu or utilities as needed.
4. Update imports and references accordingly.

This plan aims to make the project more maintainable, readable, and extensible.

---

### Türkçe Prompt

Elinizde büyük ve tek parça bir `src/main.py` dosyası bulunan bir Python PyQt6 görüntü editörü projesi var. Kod tabanını daha sürdürülebilir ve okunabilir hale getirmek için modülerleştirmeniz ve yeniden düzenlemeniz isteniyor. Aşağıdaki planı rehber olarak kullanın:

1. Uygulama giriş noktasını (`main()` fonksiyonu ve `if __name__ == '__main__':` bloğu) sadece `main.py` dosyasında bırakın, `MainWindow` sınıfını ise yeni bir dosyaya (`main_window.py`) taşıyın.
2. Özel diyalogları (ör. `FilterSliderDialog`) ayrı bir dosyaya (`dialogs.py`) taşıyın.
3. Menü ve eylem tanımlarını `main_window.py` içinde tutun, ancak menü çok karmaşıksa ayrı bir dosyaya (`menu.py`) taşıyın.
4. Filtre uygulama, önizleme ve görsel işleme fonksiyonlarını yardımcı bir dosyada (`image_processing.py` veya `filter_utils.py`) toplayın.
5. Katman ve geçmiş yönetimi zaten ayrı dosyalarda ise bu yapıyı koruyun.
6. Sık kullanılan yardımcı fonksiyonlar ve sabitler için `utils.py` veya `constants.py` gibi dosyalar oluşturun.

Önerilen dizin yapısı:

```
src/
│
├── main.py                # Sadece uygulama giriş noktası
├── main_window.py         # MainWindow ve UI kurulumları
├── dialogs.py             # Özel diyaloglar (ör: FilterSliderDialog)
├── menu.py                # Menü oluşturma (isteğe bağlı)
├── image_processing.py    # Filtre ve görsel işlemler yardımcıları
├── utils.py               # Yardımcı fonksiyonlar
├── constants.py           # Sabitler (isteğe bağlı)
├── image_io.py
├── image_view.py
├── filters.py
├── transform.py
├── history.py
├── layers.py
├── layer_panel.py
├── effects_panel.py
└── ...
```

Şu adımları izleyin:
1. `MainWindow` ve diyalog sınıflarını kendi dosyalarına taşıyın.
2. Filtre ve görsel işleme fonksiyonlarını yardımcı dosyaya ayırın.
3. Gerekirse menü ve yardımcı fonksiyonlar için ek dosyalar oluşturun.
4. Her dosyada uygun import ve bağlantıları güncelleyin.

Bu plan, projenin daha sürdürülebilir, okunabilir ve geliştirilebilir olmasını amaçlamaktadır.
