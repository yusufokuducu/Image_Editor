import sys
import logging
import argparse
from PyQt6.QtWidgets import QApplication, QMessageBox
sys.path.append("..")
from src.main_window import MainWindow  
from src.resize_dialog import ResizeDialog  
from src.gpu_utils import configure_gpu, use_cpu_fallback, check_cuda_availability
def main():
    try:
        parser = argparse.ArgumentParser(description='Image Editor with GPU Acceleration')
        parser.add_argument('--gpu', type=int, help='GPU ID to use (default: 0)', default=0)
        parser.add_argument('--cpu', action='store_true', help='Force CPU mode')
        parser.add_argument('--debug', action='store_true', help='Enable DEBUG log level')
        args = parser.parse_args()
        log_level = logging.DEBUG if args.debug else logging.INFO
        logging.basicConfig(level=log_level,
                           format='%(asctime)s [%(levelname)s] %(message)s',
                           handlers=[
                               logging.FileHandler("pyxeledit.log"),
                               logging.StreamHandler()
                           ])
        logging.info("=" * 50)
        logging.info("PyxelEdit Başlatılıyor")
        logging.info(f"Python Sürümü: {sys.version}")
        logging.info(f"PyQt6 import edildi")
        try:
            import torch
            logging.info(f"PyTorch Sürümü: {torch.__version__}")
            if torch.cuda.is_available():
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
        if not args.cpu:
            logging.info(f"GPU kurulumu yapılıyor (aranan GPU ID: {args.gpu})")
            gpu_available = configure_gpu(args.gpu)
            if not gpu_available:
                logging.warning("GPU not available or configuration failed, using CPU instead")
        else:
            logging.info("Forcing CPU mode as requested")
            use_cpu_fallback()
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        logging.critical(f"Uygulama başlatılırken kritik hata: {e}")
        try:
            QMessageBox.critical(None, 'Kritik Hata',
                               f'Uygulama başlatılırken beklenmeyen bir hata oluştu:\n{e}\n\n'
                               f'Lütfen pyxeledit.log dosyasını kontrol edin.')
        except RuntimeError: 
             print(f"Kritik Hata (QApplication başlatılamadı): {e}")
if __name__ == '__main__':
    main()