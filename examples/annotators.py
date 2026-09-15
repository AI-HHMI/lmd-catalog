import lmd_catalog as lmd
from rich import print as pprint

data = []
ann = set()
desired_annotators = {'Brie', 'Brie Yarbrough'}
for x in lmd.all():
    a = set((y.annotator for y in x.tracked_by))
    ann |= a
    if a & desired_annotators:
        data.append(x)

pprint(data) ## All VolumeEntry that have a GT annotation done by Brie. 
pprint(ann)  ## All possible annotators
