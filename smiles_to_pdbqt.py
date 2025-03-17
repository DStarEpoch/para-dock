#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time   : 2025/3/7 10:20
# @Author : yuyeqing
# @File   : smiles_to_pdbqt.py
# @IDE    : PyCharm
import subprocess
import tempfile
from openbabel import pybel


def one_smiles_to_pdbqt_string(smiles):
    """
    将 SMILES 字符串转换为 PDBQT 字符串。

    参数:
    smiles (str): 输入的 SMILES 字符串。

    返回:
    str: 输出的 PDBQT 字符串。
    """
    # 创建一个临时文件来存储中间的 SDF 文件
    with tempfile.NamedTemporaryFile(suffix='.sdf') as sdf_file:
        # 使用 Open Babel 将 SMILES 转换为 SDF 格式
        mol = pybel.readstring("smi", smiles)
        mol.addh()  # 添加氢原子
        mol.make3D()  # 生成 3D 结构
        mol.write("sdf", sdf_file.name, overwrite=True)
        # 使用 Open Babel 将 SDF 转换为 PDBQT 格式
        with tempfile.NamedTemporaryFile(suffix='.pdbqt') as pdbqt_file:
            result = subprocess.run([
                'obabel',
                sdf_file.name,
                '-opdbqt',
                '-O',
                pdbqt_file.name,
                "-xh", # 保留非极性氢原子
                "--partialcharge", "Gasteiger",
                "-p", "7.4",
                "--gen3d",
            ], check=True)
            with open(pdbqt_file.name, 'r') as file:
                pdbqt_string = file.read()

        # 检查命令是否成功执行
        if result.returncode == 0:
            return pdbqt_string
        else:
            raise RuntimeError(result.stderr)


def one_smiles_to_pdbqt_string_v2(smiles):
    with tempfile.NamedTemporaryFile(suffix='.mol2') as mol2_file:
        mol = pybel.readstring("smi", smiles)
        mol.addh()  # 添加氢原子
        mol.make3D()  # 生成 3D 结构
        mol.write("mol2", mol2_file.name, overwrite=True)

        with tempfile.NamedTemporaryFile(suffix='.pdbqt') as pdbqt_file:
            result = subprocess.run(
                [
                    "prepare_ligand4",
                    "-l", mol2_file.name,
                    "-o", pdbqt_file.name,
                    "-U", " ",
                ], check=True)
            with open(pdbqt_file.name, 'r') as file:
                pdbqt_string = file.read()

    if result.returncode == 0:
        return pdbqt_string
    else:
        raise RuntimeError(result.stderr)


def one_smiles_to_pdbqt_file(smiles, output_file):
    """
    将 SMILES 字符串转换为 PDBQT 文件。

    参数:
    smiles (str): 输入的 SMILES 字符串。
    output_file (str): 输出的 PDBQT 文件路径。
    """
    pdbqt_string = one_smiles_to_pdbqt_string_v2(smiles)
    with open(output_file, 'w') as file:
        file.write(pdbqt_string)
