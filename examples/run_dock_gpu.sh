#!/bin/bash

if command -v adgpu >/dev/null 2>&1; then
    para-dock dock-run ./conf.yaml ./ligands.csv ./protein.pdbqt -n 2 --out_dir ./output_gpu --use-gpu
else
    echo "adgpu not found!" >&2
    exit 1
fi
