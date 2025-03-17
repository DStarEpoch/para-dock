#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time   : 2025/3/14 15:26
# @Author : yuyeqing
# @File   : adgpu_output_xml_parser.py
# @IDE    : PyCharm
import argparse
import xml.etree.ElementTree as ET

def extract_free_nrg_binding(xml_file):
    # 解析 XML 文件
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # 找到所有 <run> 元素
    runs = root.findall('runs/run')

    ret = list()
    # 提取每个 <run> 中的 free_NRG_binding
    for run in runs:
        free_nrg_binding = float(run.find('free_NRG_binding').text.strip())
        final_intermol_nrg = float(run.find('final_intermol_NRG').text.strip())
        internal_ligand_nrg = float(run.find('internal_ligand_NRG').text.strip())
        torsonial_free_nrg = float(run.find('torsonial_free_NRG').text.strip())
        ret.append((free_nrg_binding, final_intermol_nrg, internal_ligand_nrg, torsonial_free_nrg))
        # print(f"Run ID: {run_id}, Free Energy of Binding: {free_nrg_binding} kcal/mol")

    return ret


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Parse AutoDock-GPU output XML file.")
    parser.add_argument("xml_file", help="Path to the AutoDock-GPU output XML file.")
    args = parser.parse_args()

    results = extract_free_nrg_binding(args.xml_file)
    for r in results:
        print(r)
