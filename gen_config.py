#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time   : 2025/3/7 8:56
# @Author : yuyeqing
# @File   : gen_config.py
# @IDE    : PyCharm
import yaml
import click
import argparse
from pathlib import Path

def parse_grid_box_file(file_path):
    """
    解析ADT生成的grid box文件，提取中心坐标、点数和间距。
    """
    center = None
    npts = None
    spacing = None

    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith('center'):
                center = list(map(float, line.split()[1:4]))
            elif line.startswith('npts'):
                npts = list(map(int, line.split()[1:4]))
            elif line.startswith('spacing'):
                spacing = float(line.split()[1])

    if not center or not npts or not spacing:
        raise ValueError("Grid box文件格式不正确，缺少必要的信息。")

    return center, npts, spacing

def calculate_size(npts, spacing):
    """
    根据点数和间距计算grid box的尺寸。
    """
    size_x = (npts[0] - 1) * spacing
    size_y = (npts[1] - 1) * spacing
    size_z = (npts[2] - 1) * spacing
    return size_x, size_y, size_z

def generate_conf_file(center, size, spacing, cpu, exhaustiveness, seed, num_modes, npts, output_file='conf.txt'):
    """
    生成Vina的conf.txt文件。
    """
    content = f"""center_x = {center[0]}
center_y = {center[1]}
center_z = {center[2]}
size_x = {size[0]}
size_y = {size[1]}
size_z = {size[2]}
npts_x = {npts[0]}
npts_y = {npts[1]}
npts_z = {npts[2]}
spacing = {spacing}
cpu = {cpu}
exhaustiveness = {exhaustiveness}
seed = {seed}
num_modes = {num_modes}
"""

    with open(output_file, 'w') as file:
        file.write(content)

def generate_conf_yaml(center, size, spacing, cpu, exhaustiveness, seed, num_modes, npts, output_file='conf.yaml'):
    """
    生成Vina的conf.yaml文件。
    """
    content = {
        'center': center,
        'box_size': size,
        'spacing': spacing,
        'cpu': cpu,
        'exhaustiveness': exhaustiveness,
        'seed': seed,
        'n_poses': num_modes,
        'npts': npts
    }

    with open(output_file, 'w') as file:
        yaml.dump(content, file)

@click.command("gen-config")
@click.option('-f', '--input_file', type=str, required=True, help='输入的grid box文件路径')
@click.option('--cpu', type=int, default=1, help='CPU数量, 默认 1')
@click.option('--exhaustiveness', type=int, default=8, help='Exhaustiveness值, 默认 8')
@click.option('--seed', type=int, default=42, help='随机种子值, 默认42')
@click.option('--num_modes', type=int, default=5, help='生成的模式数量, 默认 5')
@click.option('--output-path', type=str, default='./', help='输出文件路径, 默认当前目录')
@click.option('--generate-yaml', is_flag=True, help='是否生成yaml类型文件')
def gen_config_inference(input_file, cpu, exhaustiveness, seed, num_modes, output_path='./', generate_yaml=False):
    try:
        center, npts, spacing = parse_grid_box_file(input_file)
        size = calculate_size(npts, spacing)
        if generate_yaml:
            outf = Path(output_path) / 'conf.yaml'
            generate_conf_yaml(center, size, spacing, cpu, exhaustiveness,
                               seed, num_modes, npts, outf)
            print(f"{outf.absolute()}文件已生成")
        else:
            outf = Path(output_path) / 'conf.txt'
            generate_conf_file(center, size, spacing, cpu, exhaustiveness,
                               seed, num_modes, outf)
            print(f"{outf.absolute()}文件已生成")
    except Exception as e:
        print(f"发生错误：{e}")

def main():
    parser = argparse.ArgumentParser(description='将ADT生成的grid box文件转换为Vina的conf.txt / conf.yaml文件。')
    parser.add_argument('-f', '--file', type=str, required=True, help='输入的grid box文件路径')
    parser.add_argument('--cpu', type=int, default=1, help='CPU数量, 默认 1')
    parser.add_argument('--exhaustiveness', type=int, default=8, help='Exhaustiveness值, 默认 8')
    parser.add_argument('--seed', type=int, default=42, help='随机种子值, 默认42')
    parser.add_argument('--num_modes', type=int, default=5, help='生成的模式数量, 默认 5')
    parser.add_argument('--generate_yaml', action='store_true', help='生成yaml类型文件')
    args = parser.parse_args()
    gen_config_inference(args.file, args.cpu, args.exhaustiveness,
                         args.seed, args.num_modes, generate_yaml=args.generate_yaml)

if __name__ == '__main__':
    main()