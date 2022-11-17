# Author: Tiantian Feng
# USC SAIL lab, tiantiaf@usc.edu
import pdb
import glob
import copy
import torch
import random
import pickle
import os, sys
import argparse
import scipy.io
import wfdb, ast
import numpy as np
import os.path as osp


from tqdm import tqdm
from pathlib import Path

sys.path.append(os.path.join(str(Path(os.path.realpath(__file__)).parents[1])))
from feature_manager import feature_manager

# Define logging console
import logging
logging.basicConfig(
    format='%(asctime)s %(levelname)-3s ==> %(message)s', 
    level=logging.INFO, 
    datefmt='%Y-%m-%d %H:%M:%S'
)

def parse_args():
    parser = argparse.ArgumentParser(description='Extract 6+6 lead features')
    parser.add_argument(
        "--raw_data_dir",
        type=str,
        default="/media/data/public-data/Health/ptb-xl",
        help="Raw data path of ptb-xl data set",
    )
    
    parser.add_argument(
        '--output_dir', 
        default='/media/data/projects/speech-privacy/fed-multimodal/',
        type=str, 
        help='output feature directory'
    )
    
    parser.add_argument(
        "--dataset", 
        type=str,
        default="ptb-xl",
        help="dataset name",
    )
    
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    # Read args
    args = parse_args()

    # Iterate over folds
    I_to_AVF_output_data_path = Path(args.output_dir).joinpath(
        'feature', 
        'I_to_AVF', 
        args.dataset
    )

    V1_to_V6_output_data_path = Path(args.output_dir).joinpath(
        'feature', 
        'V1_to_V6', 
        args.dataset
    )

    Path.mkdir(I_to_AVF_output_data_path, parents=True, exist_ok=True)
    Path.mkdir(V1_to_V6_output_data_path, parents=True, exist_ok=True)
    data_path = Path(args.raw_data_dir).joinpath(
        'ptb-xl-a-large-publicly-available-electrocardiography-dataset-1.0.1'
    )
    
    # initialize feature processer
    fm = feature_manager(args)
    
    # fetch all files for processing
    partition_dict = fm.fetch_partition()
    logging.info(f'Reading data from folder: {args.raw_data_dir}')
    logging.info(f'Total number of clients found: {len(partition_dict.keys())}')
    
    # extract data
    for client_id in partition_dict:
        I_to_AVF_dict = copy.deepcopy(partition_dict[client_id])
        V1_to_V6_dict = copy.deepcopy(partition_dict[client_id])
        
        # iterate over keys
        for idx in tqdm(range(len(I_to_AVF_dict))):
            # 0. initialize file path
            file_path = I_to_AVF_dict[idx][1]
            
            data = wfdb.rdsamp(str(data_path.joinpath(file_path)))
            sig_names = data[1]['sig_name']
            I_to_AVF_idx = [
                sig_names.index('I'), 
                sig_names.index('II'), 
                sig_names.index('III'), 
                sig_names.index('AVR'), 
                sig_names.index('AVL'), 
                sig_names.index('AVF')
            ]

            V1_to_V6_idx = [
                sig_names.index('V1'), 
                sig_names.index('V2'), 
                sig_names.index('V3'), 
                sig_names.index('V4'), 
                sig_names.index('V5'), 
                sig_names.index('V6')
            ]
            
            # 1.1 read I_to_AVF data
            I_to_AVF_features = data[0][:, I_to_AVF_idx]
            # 1.2 normalize I_to_AVF data
            mean, std = np.mean(I_to_AVF_features, axis=0), np.std(I_to_AVF_features, axis=0)
            I_to_AVF_features = (I_to_AVF_features - mean) / (std + 1e-5)
            I_to_AVF_dict[idx].append(copy.deepcopy(I_to_AVF_features))

            # 2.1 read V1_to_V6 data
            V1_to_V6_features = data[0][:, V1_to_V6_idx]
            
            # 2.2 normalize V1_to_V6 data
            mean, std = np.mean(V1_to_V6_features, axis=0), np.std(V1_to_V6_features, axis=0)
            V1_to_V6_features = (V1_to_V6_features - mean) / (std + 1e-5)
            V1_to_V6_dict[idx].append(copy.deepcopy(V1_to_V6_features))
            # pdb.set_trace()
            
        # very important: final feature output format
        # [key, idx, label, feature]
        with open(I_to_AVF_output_data_path.joinpath(f'{client_id}.pkl'), 'wb') as handle:
            pickle.dump(I_to_AVF_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)
        with open(V1_to_V6_output_data_path.joinpath(f'{client_id}.pkl'), 'wb') as handle:
            pickle.dump(V1_to_V6_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)
