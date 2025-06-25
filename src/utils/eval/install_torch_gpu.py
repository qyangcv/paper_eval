#!/usr/bin/env python
import os
import platform
import subprocess
import sys

def install_torch_gpu():
    """
    Install the appropriate GPU version of PyTorch based on the system's configuration.
    Using Tsinghua mirror for faster downloads in China.
    """
    print("Installing PyTorch GPU version using Tsinghua mirror...")
    
    # Tsinghua PyPI mirror URL
    tsinghua_pypi = "https://pypi.tuna.tsinghua.edu.cn/simple"
    
    # Check if CUDA is available
    try:
        nvidia_smi_output = subprocess.check_output(["nvidia-smi"], stderr=subprocess.STDOUT, text=True)
        print("NVIDIA GPU detected:")
        print(nvidia_smi_output.split("\n")[0])
        
        # Try to determine CUDA version from nvidia-smi output
        cuda_version = None
        for line in nvidia_smi_output.split("\n"):
            if "CUDA Version:" in line:
                cuda_version = line.split("CUDA Version:")[1].strip().split()[0]
                break
                
        if cuda_version:
            print(f"Detected CUDA version: {cuda_version}")
        else:
            print("Could not automatically detect CUDA version.")
            cuda_version = input("Please enter your CUDA version (e.g., 11.8, 12.1): ")
    except (subprocess.SubprocessError, FileNotFoundError):
        print("NVIDIA GPU not detected or nvidia-smi not available.")
        print("If you have an NVIDIA GPU and CUDA installed, please check your drivers.")
        cuda_version = input("Please enter your CUDA version (e.g., 11.8, 12.1), or press Enter to use CPU version: ")
        if not cuda_version:
            install_command = f"pip install torch>=2.0.0 -i {tsinghua_pypi}"
            print(f"Installing PyTorch CPU version: {install_command}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "torch>=2.0.0", "-i", tsinghua_pypi])
            return

    # Major CUDA versions supported by PyTorch
    cuda_major = cuda_version.split('.')[0]
    
    # For specific CUDA versions, we need to use PyTorch's index as primary for torch packages
    if cuda_major == "12":
        # For CUDA 12.x
        print("Installing PyTorch for CUDA 12.x")
        # First uninstall any existing torch installations to avoid conflicts
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "uninstall", "torch", "torchvision", "torchaudio", "-y"])
        except:
            pass

        # 使用清华源镜像的PyTorch CUDA版本
        pytorch_mirror = "https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/pytorch/linux-64/"
        cmd = [
            sys.executable, "-m", "pip", "install",
            "torch", "torchvision", "torchaudio",
            "--index-url", "https://download.pytorch.org/whl/cu121"
        ]
        
    elif cuda_major == "11":
        # For CUDA 11.x
        print("Installing PyTorch for CUDA 11.x")
        # First uninstall any existing torch installations to avoid conflicts
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "uninstall", "torch", "torchvision", "torchaudio", "-y"])
        except:
            pass

        cmd = [
            sys.executable, "-m", "pip", "install",
            "torch", "torchvision", "torchaudio",
            "--index-url", "https://download.pytorch.org/whl/cu118"
        ]
        
    else:
        print(f"CUDA version {cuda_version} may not be officially supported by PyTorch.")
        print("Will try to install for CUDA 11.8 which has wide compatibility.")
        # First uninstall any existing torch installations to avoid conflicts
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "uninstall", "torch", "torchvision", "torchaudio", "-y"])
        except:
            pass

        cmd = [
            sys.executable, "-m", "pip", "install",
            "torch", "torchvision", "torchaudio",
            "--index-url", "https://download.pytorch.org/whl/cu118"
        ]
    
    print(f"Running: {' '.join(cmd)}")
    
    # Execute the installation command
    subprocess.check_call(cmd)
    
    # Install other packages using Tsinghua mirror
    print("Installing other requirements using Tsinghua mirror...")
    req_cmd = [
        sys.executable, "-m", "pip", "install",
        "-i", tsinghua_pypi,
        "numpy>=1.24.0", "tqdm>=4.65.0", "pandas>=2.0.0"
    ]
    subprocess.check_call(req_cmd)
    
    # Verify installation
    print("\nVerifying PyTorch installation:")
    verify_script = """
import torch
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"CUDA version: {torch.version.cuda}")
    print(f"GPU device: {torch.cuda.get_device_name(0)}")
else:
    print("WARNING: CUDA is not available! Check your installation.")
"""
    subprocess.run([sys.executable, "-c", verify_script])
    print("\nPyTorch GPU installation completed.")

if __name__ == "__main__":
    install_torch_gpu() 