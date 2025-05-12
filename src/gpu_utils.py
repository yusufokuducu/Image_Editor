import logging
import os
import numpy as np
import torch

# CUDA kontrolü yapıp durumu loglama
def check_cuda_availability():
    """
    CUDA kullanılabilirliğini kontrol eder ve detaylı bilgileri loglar
    
    Returns:
        bool: CUDA kullanılabilirse True, aksi halde False
    """
    try:
        if torch.cuda.is_available():
            # CUDA detay bilgilerini loglama
            device_count = torch.cuda.device_count()
            cuda_version = torch.version.cuda
            
            logging.info(f"✓ CUDA erişilebilir (sürüm: {cuda_version})")
            logging.info(f"✓ {device_count} GPU bulundu:")
            
            for i in range(device_count):
                name = torch.cuda.get_device_name(i)
                capability = torch.cuda.get_device_capability(i)
                total_memory = torch.cuda.get_device_properties(i).total_memory / 1024 / 1024
                logging.info(f"  GPU {i}: {name} (CUDA {capability[0]}.{capability[1]}, {total_memory:.0f} MB)")
                
            return True
        else:
            logging.warning("✗ CUDA kullanılamıyor")
            logging.warning("  GPU desteği devre dışı - CPU modu kullanılacak")
            if not hasattr(torch, 'version') or not hasattr(torch.version, 'cuda'):
                logging.warning("  PyTorch CUDA olmadan kurulmuş")
            else:
                logging.warning(f"  PyTorch CUDA sürümü: {torch.version.cuda}")
            return False
    except Exception as e:
        logging.error(f"✗ CUDA kontrolü sırasında hata: {e}")
        return False

# Başlangıçta bir kez CUDA kontrolü yap
CUDA_AVAILABLE = check_cuda_availability()

# Configure which GPU to use
def configure_gpu(gpu_id=None):
    """
    Configure which GPU to use.
    
    Args:
        gpu_id (int, optional): ID of the GPU to use. If None, will use the first available.
        
    Returns:
        bool: True if GPU is available and configured, False otherwise
    """
    try:
        if not CUDA_AVAILABLE:
            logging.info("CUDA not available, using CPU instead")
            return False
        
        # Get number of available GPUs
        gpu_count = torch.cuda.device_count()
        if gpu_count == 0:
            logging.info("No GPUs detected")
            return False
            
        logging.info(f"Found {gpu_count} GPUs")
        for i in range(gpu_count):
            logging.info(f"  GPU {i}: {torch.cuda.get_device_name(i)}")
        
        # Select GPU
        if gpu_id is None:
            gpu_id = 0
        
        if gpu_id >= gpu_count:
            logging.warning(f"Requested GPU {gpu_id} not available, using GPU 0 instead")
            gpu_id = 0
            
        # Set CUDA device
        torch.cuda.set_device(gpu_id)
        os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu_id)
        logging.info(f"✓ Seçilen: GPU {gpu_id}: {torch.cuda.get_device_name(gpu_id)}")
        
        # GPU belleğini test et
        try:
            # Basit bir test tensoru oluştur ve GPU'ya aktar
            test_tensor = torch.ones((100, 100), device=f"cuda:{gpu_id}")
            del test_tensor  # Belleği hemen serbest bırak
            torch.cuda.empty_cache()
            logging.info(f"✓ GPU bellek testi başarılı")
        except Exception as e:
            logging.error(f"✗ GPU bellek testi başarısız: {e}")
            return False
            
        return True
    except Exception as e:
        logging.error(f"✗ GPU yapılandırma hatası: {e}")
        return False

# Check if GPU memory is sufficient
def check_gpu_memory(required_mb=1000):
    """
    Check if GPU has sufficient free memory.
    
    Args:
        required_mb (int): Required memory in MB
        
    Returns:
        bool: True if sufficient memory is available, False otherwise
    """
    if not CUDA_AVAILABLE:
        return False
    
    try:
        # Get free memory in bytes and convert to MB
        free_memory = torch.cuda.mem_get_info()[0] / (1024 * 1024)
        has_memory = free_memory >= required_mb
        
        if not has_memory:
            logging.warning(f"✗ Yetersiz GPU belleği: {free_memory:.0f}MB mevcut, {required_mb}MB gerekli")
        
        return has_memory
    except Exception as e:
        logging.error(f"✗ GPU bellek kontrolü hatası: {e}")
        return False

# Utility to convert PIL Image to Tensor and back
def pil_to_tensor(img):
    """Convert PIL Image to PyTorch Tensor with GPU support"""
    try:
        # Convert PIL to tensor and move to GPU if available
        tensor = torch.from_numpy(np.array(img)).permute(2, 0, 1).float()
        if CUDA_AVAILABLE:
            tensor = tensor.cuda()
            logging.debug(f"✓ Görüntü GPU'ya aktarıldı (şekil: {list(tensor.shape)})")
        return tensor
    except Exception as e:
        logging.error(f"✗ PIL -> Tensor dönüşüm hatası: {e}")
        return None

def tensor_to_pil(tensor):
    """Convert PyTorch Tensor to PIL Image"""
    try:
        # Move tensor to CPU if it's on GPU
        if tensor.is_cuda:
            tensor = tensor.cpu()
            logging.debug(f"✓ Tensor CPU'ya aktarıldı (şekil: {list(tensor.shape)})")
        
        # Convert to numpy and then to PIL
        arr = tensor.permute(1, 2, 0).numpy().astype(np.uint8)
        from PIL import Image
        return Image.fromarray(arr)
    except Exception as e:
        logging.error(f"✗ Tensor -> PIL dönüşüm hatası: {e}")
        return None

# Fallback functions when GPU operations fail
def use_cpu_fallback():
    """
    Force CPU usage for this session
    """
    os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
    logging.info("⚠ GPU devre dışı bırakıldı, CPU moduna geçildi") 