# 🖥️ Google Cloud VM Setup Guide: DNTextSpotter

Dieses Dokument beschreibt die Konfiguration und den Aufbau der Virtual Machine für das Finetuning von DNTextSpotter.

# VM Setup

Um DNTextSpotter effizient zu trainieren, ist folgende (oder eine vergleichbare) Konfiguration in der Google Cloud Console gewählt:

    Instanz-Typ: g2-standard-4

    GPU: 1x NVIDIA L4 (24 GB VRAM) 

    CPU: 4-8 vCPUs.

    RAM: 32 GB - 64 GB.

    Boot Disk: 80 GB SSD (Ubuntu 22.04 LTS oder Debian 11).

    Image: Linux Deep Learning

    Wichtig: Falls eine N2-Maschine ohne GPU verwendet wird, muss diese über "Edit" mit einer GPU nachgerüstet werden, da das Training sonst Wochen dauern würde.


# DNTextSpotter Setup

Führe diese Schritte aus, um die isolierte Python-Umgebung und den Code einzurichten:


```
git clone https://github.com/yyyyyxie/DNTextSpotter.git
cd DNTextSpotter
conda create -n dnts python=3.8 -y
conda activate dnts
pip install torch==2.1.2 torchvision==0.16.2 torchaudio==2.1.2 \
  --index-url https://download.pytorch.org/whl/cu121 \
  --force-reinstall
cd detectron2
pip install -e .
cd ..
# First install everything except scikit-image
grep -v "scikit-image" requirements.txt | pip install -r /dev/stdin

# Then install a compatible version
pip install scikit-image==0.19.3
python setup.py build develop
```


# Pretrained Model Setup

for ResNet 50:
```
pip install gdown
cd ~/DNTextSpotter/pretrained_models
gdown 1Lg75fZKS2u7xY2EBg3WWFKCVYs11MRKQ
```

# Upload image
```
pip install gdown
scp h1_w7.jpg seisi3322@EXTERNALIP:~/DNTextSpotter/demo/input/
```

# Run DEMO


