# PyxelEdit

**Gelişmiş, Katman Destekli Python Görüntü Editörü**

PyxelEdit Pro; modern arayüzü, güçlü katman yönetimi ve esnek filtre/efekt seçenekleriyle Windows için geliştirilmiş açık kaynaklı bir raster imaj editörüdür.

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
- **Geri Al/Yinele (Undo/Redo):** Tüm işlemler için komut geçmişi.
- **Kısa Yollar:** Hızlı erişim için kapsamlı klavye kısayolları.
- **Katman Bazlı İşlem:** Efekt ve filtreler sadece seçili/aktif katmana uygulanabilir.
- **Geliştirilebilir Altyapı:** Yeni filtre, araç veya katman özelliği kolayca eklenebilir.

---

## Kurulum

1. **Python 3.10+** kurulu olmalı.
2. Bağımlılıkları yükleyin:
   ```bash
   pip install -r requirements.txt
   ```

---

## Çalıştırma

```bash
python src/main.py
```

---

## Kullanım

- **Resim Aç/Kaydet:** Dosya menüsünden veya Ctrl+O/Ctrl+S ile.
- **Katman Ekle/Sil:** Katmanlar menüsünden veya panelden.
- **Katmanı Taşı/Kopyala:** Katman panelinde yukarı/aşağı oklar veya kopyala/yapıştır butonları.
- **Efekt Uygulama:** Filtreler menüsünden, bulanıklık ve noise için seviye seçimiyle.
- **Seçim Araçları:** Seçim menüsünden dikdörtgen/elips/lasso seçimi.
- **Undo/Redo:** Ctrl+Z / Ctrl+Y.

---

## Kısayollar

| İşlem                       | Kısayol           |
|-----------------------------|-------------------|
| Geri Al (Undo)              | Ctrl+Z            |
| Yinele (Redo)               | Ctrl+Y            |
| Yeni Katman                 | Ctrl+Shift+N      |
| Katmanı Sil                 | Del               |
| Katmanı Yukarı/Aşağı Taşı   | Ctrl+Up / Ctrl+Down |
| Katmanları Birleştir        | Ctrl+M            |
| Katman Görünürlüğü          | Ctrl+H            |

---

## Geliştirici Notları

- Kod modülerdir: `src/` klasöründe ana bileşenler (main, layers, layer_panel, image_view, filters, transform, history, image_io) ayrı dosyalardadır.
- Yeni filtreler veya araçlar eklemek için ilgili modülü genişletin.
- Katman paneli ve komut altyapısı kolayca geliştirilebilir.

---

## Lisans

MIT Lisansı altında açık kaynak.

---

## Katkı ve Geri Bildirim

Pull request ve issue açarak katkıda bulunabilirsiniz!

Geliştirici: faust-lvii[yusufokuducu](mailto:k.yusufokuducu@gmail.com)  

---
