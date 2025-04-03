#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time   : 2025/3/7 8:25
# @Author : yuyeqing
# @File   : run_dock.py
# @IDE    : PyCharm
import os
import yaml
import json
import click
import shutil
import subprocess
from tqdm import tqdm
import pandas as pd
from vina import Vina
from pathlib import Path
from dataclasses import dataclass
from multiprocessing import Pool
from smiles_to_pdbqt import one_smiles_to_pdbqt_string_v2
from utils.adgpu_output_xml_parser import extract_free_nrg_binding


@dataclass
class TaskParam:
    conf_yaml_file: str
    receptor_pdbqt: str
    ligand_name: str
    ligand_pdbqt_file: str = None
    ligand_pdbqt_string: str = None
    output_dir: str = "./output"
    task_id: int = None
    output_result: bool = True
    output_pdbqt: bool = True
    cur_dir: str = str(Path("./").absolute())


def process_one_task_gpu(param: TaskParam):
    out_log = ""
    ret = dict()
    with open(param.conf_yaml_file, 'r') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    ligand_name = param.ligand_name
    temp_dir = Path(param.output_dir) / f"{ligand_name}_temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    try:
        # copy receptor to temp dir
        shutil.copy(param.receptor_pdbqt, temp_dir / "receptor.pdbqt")
        # prepare ligand
        if param.ligand_pdbqt_file:
            shutil.copy(param.ligand_pdbqt_file, temp_dir / f"{ligand_name}.pdbqt")
        elif param.ligand_pdbqt_string:
            with open(temp_dir / f"{ligand_name}.pdbqt", 'w') as f:
                f.write(param.ligand_pdbqt_string)
        else:
            raise ValueError("No ligand provided.")

        os.chdir(temp_dir)
        # prepare gpf
        gpf_file = f"{ligand_name}.gpf"
        gpf_result = subprocess.run([
                        'prepare_gpf4',
                        '-r', 'receptor.pdbqt',
                        '-l', f"{ligand_name}.pdbqt",
                        '-o', gpf_file,
                        '-p', f"npts={','.join(map(str, config['npts']))}",
                        '-p', f"gridcenter={','.join(map(str, config['center']))}",
                        '-p', f"spacing={config['spacing']}"],
                        check=True
                    )
        if gpf_result.returncode != 0:
            raise RuntimeError(gpf_result.stderr)

        # autogrid
        ag_result = subprocess.run([
                        'autogrid4',
                        '-p', gpf_file,
                        '-l', f"{ligand_name}.log"],
                        check=True
                    )
        if ag_result.returncode != 0:
            raise RuntimeError(ag_result.stderr)

        # run autodock gpu
        best_struct_file = Path(param.output_dir) / f"{ligand_name}-best.pdbqt"
        if best_struct_file.exists():
            best_struct_file.unlink()
        adgpu_result = subprocess.run([
                        'adgpu',
                        '--ffile', "receptor.maps.fld",
                        '--lfile', f"{ligand_name}.pdbqt",
                        '--devnum', f'{config.get("gpu_device", 0) + 1}',
                        '--nrun', "20",
                        '--gbest', '--rlige'
                        '--seed', str(config.get("seed", 42)),],
                        check=True
                    )
        if adgpu_result.returncode != 0:
            raise RuntimeError(adgpu_result.stderr)

        # parse output xml
        xml_file = f"{ligand_name}.xml"
        energies = extract_free_nrg_binding(xml_file)
        opt_energy = energies[0][0]
        out_log += f" Optimal energy: {opt_energy}"
        shutil.move(f"{ligand_name}-best.pdbqt", param.output_dir)
        ret = {
            "task_id": param.task_id,
            "ligand_name": param.ligand_name,
            "opt_energy": opt_energy,
            "energies": energies,
            "log": out_log
        }
    except Exception as e:
        out_log = str(e)
        ret['log'] = out_log

    os.chdir(param.cur_dir)
    shutil.rmtree(temp_dir)
    print(f"task {param.task_id}: ", out_log)
    if param.output_result:
        with open(Path(param.output_dir) / f"{param.ligand_name}_log.json", 'w') as fp:
            ret_str = json.dumps(ret, indent=4)
            fp.write(ret_str)
    return ret


def process_one_task(param: TaskParam):
    out_log = ""
    ret = dict()
    with open(param.conf_yaml_file, 'r') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    try:
        v = Vina(sf_name='vina', cpu=config.get("cpu", 1), seed=config.get("seed", 42), verbosity=1)

        v.set_receptor(param.receptor_pdbqt)
        if param.ligand_pdbqt_file:
            v.set_ligand_from_file(param.ligand_pdbqt_file)
            out_log += f" Load ligand {param.ligand_name} from {param.ligand_pdbqt_file}"
        elif param.ligand_pdbqt_string:
            v.set_ligand_from_string(param.ligand_pdbqt_string)
            out_log += f" Load ligand pdbqt string of {param.ligand_name}"
        else:
            raise ValueError("No ligand provided.")

        v.compute_vina_maps(center=config['center'],
                            box_size=config['box_size'],
                            spacing=config['spacing'])

        v.dock(exhaustiveness=config.get('exhaustiveness', 8), n_poses=config.get('n_poses', 5))

        opt_energy = v.score()[0]
        energies = v.energies(n_poses=config.get('n_poses', 5)).tolist()

        if param.output_pdbqt:
            output_pdbqt_file = Path(param.output_dir) / f"{param.ligand_name}_out.pdbqt"
            v.write_poses(pdbqt_filename=str(output_pdbqt_file.absolute()),
                          n_poses=config.get('n_poses', 5), overwrite=True)
        out_log += f" Optimal energy: {opt_energy}"

        ret = {
            "task_id": param.task_id,
            "ligand_name": param.ligand_name,
            "opt_energy": opt_energy,
            "energies": energies,
            "log": out_log
        }
        if param.output_result:
            with open(Path(param.output_dir) / f"{param.ligand_name}_log.json", 'w') as fp:
                ret_str = json.dumps(ret, indent=4)
                fp.write(ret_str)

    except Exception as e:
        out_log = str(e)

    print(f"task {param.task_id}: ", out_log)
    return ret


@click.command("dock-run")
@click.argument("conf_yaml_file", type=click.Path(exists=True))
@click.argument("smiles_csv", type=click.Path(exists=True))
@click.argument("receptor_pdbqt", type=click.Path(exists=True))
@click.option("-o", "--out_dir", "out_dir", help="output directory", default="./output")
@click.option("-n", "--nproc", "nproc", default=3, help="number of processes", show_default=True)
@click.option("-c", "--chunksize", "chunksize", default=1, help="chunksize of multiprocess", show_default=True)
@click.option('--use-gpu', is_flag=True, help='Use AutoDock-GPU to run docking', show_default=True)
def para_run_dock(conf_yaml_file: str, smiles_csv: str, receptor_pdbqt: str,
                  out_dir: str="./output", nproc: int = 3, chunksize: int = 1, use_gpu: bool = False):
    click.echo(f"conf_yaml_file: {conf_yaml_file}")
    click.echo(f"smiles_csv: {smiles_csv}")
    click.echo(f"receptor_pdbqt: {receptor_pdbqt}")
    click.echo(f"out_dir: {out_dir}")
    click.echo(f"nproc: {nproc}")
    click.echo(f"chunksize: {chunksize}")
    click.echo(f"use_gpu: {use_gpu}")

    df = pd.read_csv(smiles_csv)
    task_params = []
    if out_dir is not None:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

    for i in range(len(df.index)):
        name = df.name[i]
        if not name:
            continue
        print(f"Processing {name}")
        try:
            smiles = df.SMILES[i]
            sl = smiles.split(".")
            max_len = 0
            for s in sl:
                if len(s) > max_len:
                    smiles = s
                    max_len = len(s)

            ligand_pdbqt_string = one_smiles_to_pdbqt_string_v2(smiles)
            task_params.append(
                                TaskParam(
                                     conf_yaml_file=conf_yaml_file,
                                     receptor_pdbqt=receptor_pdbqt,
                                     ligand_name=name,
                                     ligand_pdbqt_string=ligand_pdbqt_string,
                                     output_dir=str(out_dir.absolute()),
                                     task_id=i,
                                     cur_dir=str(Path("./").absolute())
                                    )
                                )
        except Exception as e:
            print(f"{name} Error: {e}")

    import time
    if nproc <= 1:
        start = time.time()
        for param in task_params:
            if use_gpu:
                results = process_one_task_gpu(param)
            else:
                results = process_one_task(param)
        end = time.time()
        print(f"Time: {end - start}")
    else:
        with Pool(nproc) as p:
            if use_gpu:
                results = list(tqdm(p.imap_unordered(process_one_task_gpu, task_params, chunksize=chunksize),
                                    total=len(task_params)))
            else:
                results = list(tqdm(p.imap_unordered(process_one_task, task_params, chunksize=chunksize),
                                    total=len(task_params)))
        # results = list(p.map(process_one_task, task_params, chunksize=chunksize))

    # return results
