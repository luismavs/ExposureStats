
from pathlib import Path
import pandas as pd
import xmltodict
from tqdm import tqdm
import os
from config import *

# %%
def read_one_image(file_path):
    
    with open(file_path, 'rb') as f:
        d1 = xmltodict.parse(f)

    d2 = d1['x:xmpmeta']['rdf:RDF']['rdf:Description']
    
    #
    try:
        d3 = {k : d2[v] for k, v in FIELDS_TO_READ.items()}
        
        for k, v in FIELDS_TO_PROCESS.items():
            if v == 'strip':
                d3[k] = str(d3[k]).strip()

        image_name = file_path.name.replace(FILE_TYPE, '')[:-1]
        d3['name'] = image_name
        
    except KeyError as e:
        print(f'key not in dict: {e}')
        print(f'do some editing in Exposure to register this properly')
        print(file_path)
        print(f'\n')
#        print(FIELDS_TO_READ)
#        for k in d2.keys():
#            print(k,' :: ',d2[k])
        d3 = {}
    
    
    return d3

def read_dir(path):
    
    # recursively find all exposure files
    imgs = []
    files_list = []
    for (dirpath, dirnames, filenames) in os.walk(path):
        if dirpath.split('/')[-1].lower() not in DIRS_TO_AVOID:
            files = [Path(dirpath) / f for f in filenames if f.endswith(FILE_TYPE)]
            files_list.extend(files)
        
    for f in tqdm(files_list):
        img = read_one_image(f)
        if img != {}:
            imgs.append(img)


    # list of dicts to formatted df
    df = pd.DataFrame(imgs)
    
    df['CreateDate'] = pd.to_datetime(df['CreateDate'])
    #df['FocalLength'] = df['FocalLength'].str.replace('/1', 'mm')
    df['FocalLength'] = df['FocalLength'].apply(eval)
    df['FocalLength'] = df['FocalLength'].round(0).astype(int)
    #df['FocalLength'] = df['FocalLength'].astype(str) + 'mm'
    df['FNumber'] = df['FNumber'].str.replace('/1', '').apply(eval)
    df.loc[df['FNumber'] > 90, 'FNumber'] = df.loc[df['FNumber'] > 90, 'FNumber'] / 100. 
    # probably for manual lens
    df.loc[df['FNumber'] > 90, 'FNumber'] = df.loc[df['FNumber'] > 90, 'FNumber'] / 100. 
    df['Flag'] = df['Flag'].astype(int)
    
    df['Camera'] = df['Camera'].str.rstrip()
    #df['CropFactor'] = 2
    #df.loc[df['Camera'] == 'NIKON D3300', 'CropFactor'] = 1.5
    df.loc[df['Camera'] == 'OLYMPUS E-M5 MARK III', 'CropFactor'] = 2
    #df['FocalLength_'] = df['FocalLength'].str.replace('mm','').astype(float) 
    df['FocalLength_'] = df['FocalLength']
    df['EquivalentFocalLength'] = df['FocalLength_'].mul(df['CropFactor'])
    df['EquivalentFocalLength'] = df['EquivalentFocalLength'].astype(str) + 'mm'
    df = df.drop(columns=['FocalLength_'])
    df['Date'] = df['CreateDate'].dt.date
    
    # filter df
    for k,v in DROP_FILTERS.items():
        df = df.loc[~df[k].isin(v), :]
        
    print(f'{len(df)} photos in library')
    
    return df

def library_as_df(path):    
    path = Path(path)
    
    df = read_dir(path)
    
    return df