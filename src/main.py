import sys
import logging
from PyQt6.QtWidgets import QApplication, QMessageBox
# Add parent directory to Python path to allow imports from src package
sys.path.append("..")
from src.main_window import MainWindow # Import MainWindow from its new location

def main():
    try:
        # Hata ayıklama seviyesini ayarla
        logging.basicConfig(level=logging.INFO,
                           format='%(asctime)s [%(levelname)s] %(message)s',
                           handlers=[
                               logging.FileHandler("pyxeledit.log"),
                               logging.StreamHandler()
                           ])

        # Uygulama başlatma
        app = QApplication(sys.argv)

        # Ana pencereyi oluştur (Import edilen sınıfı kullan)
        window = MainWindow()
        window.show()

        # Uygulama döngüsünü başlat
        sys.exit(app.exec())
    except Exception as e:
        logging.critical(f"Uygulama başlatılırken kritik hata: {e}")
        # Hata mesajını göster (app değişkeni burada tanımlı olmayabilir, None kontrolü ekle)
        try:
            QMessageBox.critical(None, 'Kritik Hata',
                               f'Uygulama başlatılırken beklenmeyen bir hata oluştu:\n{e}\n\n'
                               f'Lütfen pyxeledit.log dosyasını kontrol edin.')
        except RuntimeError: # QApplication instance might not exist if error is very early
             print(f"Kritik Hata (QApplication başlatılamadı): {e}")


if __name__ == '__main__':
    main()
