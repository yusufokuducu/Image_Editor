import sys
import logging
import argparse
from PyQt6.QtWidgets import QApplication, QMessageBox
# Add parent directory to Python path to allow imports from src package
sys.path.append("..")
from src.main_window import MainWindow  # Import MainWindow from its new location
from src.resize_dialog import ResizeDialog  # Import ResizeDialog
from src.gpu_utils import configure_gpu, use_cpu_fallback, check_cuda_availability

def main():
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser(description='Image Editor with GPU Acceleration')
        parser.add_argument('--gpu', type=int, help='GPU ID to use (default: 0)', default=0)
        parser.add_argument('--cpu', action='store_true', help='Force CPU mode')
        parser.add_argument('--debug', action='store_true', help='Enable DEBUG log level')
        args = parser.parse_args()
        
        # Hata ayıklama seviyesini ayarla
        log_level = logging.DEBUG if args.debug else logging.INFO
        logging.basicConfig(level=log_level,
                           format='%(asctime)s [%(levelname)s] %(message)s',
                           handlers=[
                               logging.FileHandler("pyxeledit.log"),
                               logging.StreamHandler()
                           ])

        # Log system info
        logging.info("=" * 50)
        logging.info("PyxelEdit Başlatılıyor")
        logging.info(f"Python Sürümü: {sys.version}")
        logging.info(f"PyQt6 import edildi")
        
        # Torch ve GPU bilgilerini logla
        try:
            import torch
            logging.info(f"PyTorch Sürümü: {torch.__version__}")
            
            # CUDA kontrolü
            if torch.cuda.is_available():
                # CUDA bilgilerini logla
                logging.info(f"CUDA Sürümü: {torch.version.cuda}")
                logging.info(f"GPU Sayısı: {torch.cuda.device_count()}")
                for i in range(torch.cuda.device_count()):
                    logging.info(f"GPU {i}: {torch.cuda.get_device_name(i)}")
            else:
                logging.warning("CUDA kullanılamıyor - GPU desteği pasif")
        except ImportError:
            logging.error("PyTorch yüklenemedi - GPU desteği kullanılamayacak")
            args.cpu = True
        except Exception as e:
            logging.error(f"GPU kontrolü sırasında hata: {e}")
            args.cpu = True

        # Configure GPU if requested
        if not args.cpu:
            logging.info(f"GPU kurulumu yapılıyor (aranan GPU ID: {args.gpu})")
            gpu_available = configure_gpu(args.gpu)
            if not gpu_available:
                logging.warning("GPU not available or configuration failed, using CPU instead")
        else:
            logging.info("Forcing CPU mode as requested")
            use_cpu_fallback()

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
