# %%
##TO DO : remove unwanted photos

FIELDS_TO_READ = {'CreateDate': '@xmp:CreateDate',
                 'FocalLength': '@exif:FocalLength',
                  'FNumber': '@exif:FNumber',
                  'Camera': '@tiff:Model',
                  'Lens': '@alienexposure:lens',
                  'Flag': '@alienexposure:pickflag'
                    }

FIELDS_TO_PROCESS = {'Lens':'strip'}

FILE_TYPE =  'exposurex6'
PATH_IN_XML = ['x:xmpmeta', 'rdf:RDF', 'rdf:Description']
DIRS_TO_AVOID = ['recycling']

#
#FILTERS = {'remove__rejected' = {'alienexposure:pickflag' : 2}}
DROP_FILTERS = {'Flag' : [2]}

DEFAULT_PATH = '/Users/luis/Pictures/Lisboa 2020-'