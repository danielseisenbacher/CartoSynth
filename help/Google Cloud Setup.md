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

Install miniconda:
# 1. Download the Miniconda installer
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh

# 2. Run the installer
bash Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda3

# 3. Initialize it for your shell
~/miniconda3/bin/conda init bash

# 4. VERY IMPORTANT: Restart your shell
source ~/.bashrc

weiter:
conda create -n dnts python=3.8 -y
conda activate dnts
pip install torch==2.1.2 torchvision==0.16.2 torchaudio==2.1.2 \
  --index-url https://download.pytorch.org/whl/cu121 \
  --force-reinstall
cd detectron2
pip install -e .

bei fail:
# 1. Update the package list
sudo apt update

# 2. Install the compiler and build tools
sudo apt install build-essential ninja-build -y

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

ResNet50 pretrained for Finetune on CTW1500:

```
pip install gdown
cd ~/DNTextSpotter/pretrained_models
gdown 1ODBueatGswUcD24M48GQL-6ZBCTdwH0D
```

# Upload image

locally:
```
mkdir ~/DNTextSpotter/demo/input/
scp h1_w7.jpg seisi3322@EXTERNALIP:~/DNTextSpotter/demo/input/
```

# Finetuning Setup

## Struktur erstellen
mkdir -p datasets/synthmaps/train_images
mkdir -p datasets/synthmaps/annotations

in annotations: train_96voc.json


## Register your dataset in adet/data/builtin.py:

Find the block with totaltext_train and add:
python "synthmaps_train": ("synthmaps/train_images", "synthmaps/annotations/train_96voc.json"),

## Rename your annotation file:
cp datasets/synthmaps/annotations/annotation.json datasets/synthmaps/annotations/train_96voc.json

## Create your config:
nano configs/R_50/custom_finetune.yaml
Paste this:
yaml_BASE_: "Base_det.yaml"
MODEL:
  WEIGHTS: "/home/seisi3322/DNTextSpotter/pretrained_models/totaltext_res50.pth"
DATASETS:
  TRAIN: ("synthmaps_train",)
  TEST: ("synthmaps_train",)
SOLVER:
  IMS_PER_BATCH: 2
  BASE_LR: 2e-5
  LR_BACKBONE: 2e-6
  WARMUP_ITERS: 0
  STEPS: (8000,)
  MAX_ITER: 10000
  CHECKPOINT_PERIOD: 1000
TEST:
  EVAL_PERIOD: 1000
OUTPUT_DIR: "output/R50/synthmaps/finetune"

## Rebuild
python setup.py build develop

# irgendwas mit conda versionen 
export LD_PRELOAD=/opt/conda/envs/dnts/lib/libstdc++.so.6

## Train
python tools/train_net.py --config-file configs/R_50/custom_finetune.yaml --num-gpus 1

## now really train

python tools/train_net.py \
  --config-file configs/R_50/custom_finetune.yaml \
  --num-gpus 1 \
  SOLVER.IMS_PER_BATCH 2 \
  INPUT.CROP.ENABLED False


# demo



## Gemma Setup
mkdir gemma4

conda:
conda create -n gemma4 python=3.12
conda activate gemma4

# Install PyTorch & other libraries
!pip install torch accelerate

# Install the transformers library
!pip install transformers





