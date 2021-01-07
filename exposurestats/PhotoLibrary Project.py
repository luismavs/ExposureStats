# ---
# jupyter:
#   jupytext:
#     formats: py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.9.1
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %%
import pandas as pd
from pathlib import Path
import os
import xmltodict
import sys
import seaborn as sns
from tqdm import tqdm
import matplotlib.pyplot as plt


# %%
FIELDS_TO_READ = {'CreateDate': '@xmp:CreateDate',
                 'FocalLength': '@exif:FocalLength',
                  'FNumber': '@exif:FNumber',
                  'Camera': '@tiff:Model',
                  'Lens': '@alienexposure:lens',
                    }
FILE_TYPE =  'exposurex6'
PATH_IN_XML =  ['x:xmpmeta', 'rdf:RDF', 'rdf:Description']

def read_one_image(file_path):
    
    with open(file_path, 'rb') as f:
        d1 = xmltodict.parse(f)

    d2 = d1['x:xmpmeta']['rdf:RDF']['rdf:Description']
    
    d3 = {k : d2[v] for k, v in FIELDS_TO_READ.items()}
    image_name = file_path.name.replace(FILE_TYPE, '')[:-1]
    d3['name'] = image_name

    return d3

def read_dir(path):
    
    imgs = []
    files_list = []
    for (dirpath, dirnames, filenames) in os.walk(path):
        files = [Path(dirpath) / f for f in filenames if f.endswith(FILE_TYPE)]
        files_list.extend(files)
        
    for f in tqdm(files_list):
        imgs.append(read_one_image(f))

    # list of dicts to formatted df
    df = pd.DataFrame(imgs)
    
    df['CreateDate'] = pd.to_datetime(df['CreateDate'])
    #df['FocalLength'] = df['FocalLength'].str.replace('/1', 'mm')
    df['FocalLength'] = df['FocalLength'].apply(eval)
    df['FocalLength'] = df['FocalLength'].round(0).astype(int)
    #df['FocalLength'] = df['FocalLength'].astype(str) + 'mm'
    df['FNumber'] = df['FNumber'].str.replace('/1', '')
    
    df['Camera'] = df['Camera'].str.rstrip()
    #df['CropFactor'] = 2
    #df.loc[df['Camera'] == 'NIKON D3300', 'CropFactor'] = 1.5
    df.loc[df['Camera'] == 'OLYMPUS E-M5 MARK III', 'CropFactor'] = 2
    #df['FocalLength_'] = df['FocalLength'].str.replace('mm','').astype(float) 
    df['FocalLength_'] = df['FocalLength']
    df['EquivalentFocalLength'] = df['FocalLength_'].mul(df['CropFactor'])
    df['EquivalentFocalLength'] = df['EquivalentFocalLength'].astype(str) + 'mm'
    df = df.drop(columns=['FocalLength_'])
        
    return df

def library_as_df(path):    
    path = Path(path)
    
    df = read_dir(path)
    
    return df


def volume_plot(df, variable):

    plt.rcParams["axes.labelsize"] = 30
    
    vals = pd.Series(df[variable].unique()).sort_values(ascending=True)

    #print(vals)
    #sys.exit('here')
    p = sns.catplot(x=variable, kind="count", 
                #palette="ch:.25",
                data=df,
                height=6, 
                aspect=4,
                   order=vals)

    _, xlabels = plt.xticks()
    _, ylabels = plt.yticks()
    p.set_xticklabels(xlabels, size=20)
    p.set_yticklabels(ylabels, size=20)
    p.set_xticklabels(rotation=45)

    plt.show()

    return


def focal_lengths(df, camera=None, lens=None):
    
    if camera is not None:
        df = df[df['Camera']==camera]

    if lens is not None:
        df = df[df['Lens']==lens]
        
    volume_plot(df, 'FocalLength')
    
    return

def lens(df, camera=None):
    
    if camera is not None:
        df = df[df['Camera']==camera]
    
    volume_plot(df, 'Lens')
    
    print(df['Lens'].unique())
    
    return



# %%
path = '/Users/luis/Pictures/PhotosExp'
print('path to get stats:', path)
df = library_as_df(path)

focal_lengths(df, camera='E-M5MarkIII')

lens(df, camera='E-M5MarkIII')

focal_lengths(df, camera='E-M5MarkIII', lens='OLYMPUS M.12-45mm F4.0')


# %%

# %%

# %%