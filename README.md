# Para-dock
Scripts to parallel running Autodock-Vina or Autodock-GPU

## Get the code
clone https://github.com/DStarEpoch/para-dock.git

## Build the Environment
```
cd para-dock
mamba env create -f ./env.yaml
conda activate para-dock
pip install -e .
```

## Runing with AutoDock-GPU
To run AutoDock-GPU, download the executable from https://github.com/ccsb-scripps/AutoDock-GPU. For example, obtain the precompiled binary adgpu-v1.6_linux_x64_cuda12_128wi suitable for your system:
```
mkdir -p adgpu
cd adgpu
wget https://github.com/ccsb-scripps/AutoDock-GPU/releases/download/v1.6/adgpu-v1.6_linux_x64_cuda12_128wi
```
Create a symbolic link and add it to your PATH:
```
ln -s adgpu-v1.6_linux_x64_cuda12_128wi adgpu
export PATH=$PATH:$(pwd)
```
This setup allows you to run AutoDock-GPU using the adgpu command.
