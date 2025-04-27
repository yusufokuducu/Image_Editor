from PyQt6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QPushButton, QHBoxLayout, QLabel, QScrollArea, QFrame
from PyQt6.QtCore import Qt
import logging
from . import filters # Efektleri almak için

class EffectsPanel(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.label = QLabel('Efektler ve Ayarlamalar')
        self.layout.addWidget(self.label)

        # Efektler için kaydırılabilir bir alan oluşturalım
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        self.effects_layout = QVBoxLayout(scroll_content)
        self.effects_layout.setAlignment(Qt.AlignmentFlag.AlignTop) # Öğeleri yukarı hizala
        scroll_area.setWidget(scroll_content)
        self.layout.addWidget(scroll_area)

        self.populate_effects()

    def populate_effects(self):
        """ Mevcut efektleri panele ekler. """
        # Mevcut widget'ları temizle (varsa)
        for i in reversed(range(self.effects_layout.count())):
            widget = self.effects_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        # Filtre modülündeki fonksiyonları al
        available_effects = filters.get_available_filters()

        if not available_effects:
            self.effects_layout.addWidget(QLabel("Kullanılabilir efekt yok."))
            return

        for name, func in available_effects.items():
            # Her efekt için bir buton oluştur
            # TODO: Daha sonra buraya efekt parametreleri için kontroller (slider vb.) eklenebilir.
            btn = QPushButton(name.replace('_', ' ').title())
            # Butona tıklandığında hangi fonksiyonun çağrılacağını belirle
            # Add sharpen and grayscale to the list of effects requiring dialogs
            if name in ['blur', 'noise', 'brightness', 'contrast', 'saturation', 'hue', 'sharpen', 'grayscale']:
                # Parametre gerektirenler için MainWindow'daki diyalog fonksiyonunu çağır
                dialog_method_name = f"{name}_dialog"
                if hasattr(self.main_window, dialog_method_name):
                    dialog_method = getattr(self.main_window, dialog_method_name)
                    # Lambda kullanmadan doğrudan metodu bağla
                    btn.clicked.connect(dialog_method)
                else:
                    logging.warning(f"MainWindow'da {dialog_method_name} metodu bulunamadı.")
                    btn.setEnabled(False) # Metod yoksa butonu devre dışı bırak
            else:
                # Parametre gerektirmeyenler için doğrudan apply_filter'ı çağıracak metodu bağla
                # Lambda içinde effect_name'i doğru şekilde yakalamak önemli
                btn.clicked.connect(lambda checked, effect_name=name: self.apply_direct_effect(effect_name))

            self.effects_layout.addWidget(btn)

        logging.info(f"{len(available_effects)} efekt panele eklendi.")


    def apply_direct_effect(self, effect_name):
        """ Parametre gerektirmeyen efektleri doğrudan uygular. """
        if not self.main_window or not hasattr(self.main_window, 'layers') or not self.main_window.layers.get_active_layer():
            logging.warning(f"Efekt ({effect_name}) uygulamak için aktif katman bulunamadı.")
            # Kullanıcıya uyarı gösterilebilir (QMessageBox)
            return

        try:
            logging.debug(f"Doğrudan efekt uygulanıyor: {effect_name}")
            # MainWindow'daki apply_filter metodunu efekt adıyla çağır
            self.main_window.apply_filter(effect_name)
            logging.info(f"Doğrudan efekt başarıyla uygulandı: {effect_name}")
        except Exception as e:
            logging.error(f"Doğrudan efekt ({effect_name}) uygulanırken hata: {e}")
            # Kullanıcıya hata mesajı gösterilebilir.

    def refresh(self):
        """ Paneli yenilemek için (gerekirse). """
        # Şimdilik sadece efektleri yeniden dolduruyoruz, ileride daha karmaşık olabilir.
        self.populate_effects()
        logging.debug("Efekt paneli yenilendi.")
