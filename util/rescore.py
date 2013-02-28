import os
import sys
gpdir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.sys.path.append(gpdir)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aocr.settings")

from scoring.models import *
from scoring.forms import *

import nltk
from difflib import SequenceMatcher

import json

from sklearn.metrics import precision_recall_fscore_support
import csv
import StringIO
import chardet

import pprint

def unicode_csv_reader(unicode_csv_data, **kwargs):
    # csv.py doesn't do Unicode; encode temporarily as UTF-8:
    csv_reader = csv.reader(utf_8_encoder(unicode_csv_data), **kwargs)
    for row in csv_reader:
        # decode UTF-8 back to Unicode, cell by cell:
        yield [unicode(cell, 'utf-8') for cell in row]

def utf_8_encoder(unicode_csv_string):
    for line in StringIO.StringIO(unicode_csv_string):
        yield line.encode('utf-8')

def get_labels_dict(csvreader):
    rsingleregion = False
    rlabels = {}
    rheader = None
    for r in csvreader:
        if not rheader:
            rheader = r
            if "aocr:regionType" not in rheader:
                rsingleregion = True
            for i in range(len(rheader)):
                rheader[i] = rheader[i].strip()	
            continue
        rdict = dict(zip(rheader,r))
        for f in rdict.keys():
            v = rdict[f].strip()
            if len(v) == 0:
                del rdict[f]
            else:
                rdict[f] = v
        if (len(rdict.keys()) > 0):
            if rsingleregion:
                rlabels["primary"] = rdict
            else:
                if "aocr:regionType" in rdict:
                    lr = rdict["aocr:regionType"]
                    if lr not in rlabels:
                        del rdict["aocr:regionType"]
                        rlabels[lr] = rdict
                    else:
                        print "Error, duplicate label region"
    return rlabels
    

def scorelables(rcsv,tcsv):        
    rlabels = get_labels_dict(rcsv)
    tlabels = get_labels_dict(tcsv)
        
    kl = []

    for l in rlabels.keys():
        for f in rlabels[l]:
            kl.append(l + "#" + f)
            
    for l in tlabels.keys():
        for f in tlabels[l]:
            kl.append(l + "#" + f)       

    kl = list(set(kl))
    kl.sort()
                    
    rarr = []
    tarr = []
    for k in kl:
        ka = k.split("#")
        if ka[0] in rlabels and ka[1] in rlabels[ka[0]]:
            rarr.append(1)
            if ka[0] in tlabels and ka[1] in tlabels[ka[0]]:
                pprint.pprint(k)
                pprint.pprint([rlabels[ka[0]][ka[1]], tlabels[ka[0]][ka[1]], rlabels[ka[0]][ka[1]] == tlabels[ka[0]][ka[1]]])
                if rlabels[ka[0]][ka[1]] == tlabels[ka[0]][ka[1]]:
                    tarr.append(1)
                else:
                    tarr.append(0)
            else:
                tarr.append(0)
        else:
            rarr.append(0)
            tarr.append(0)

    a = precision_recall_fscore_support(rarr, tarr,average="weighted")
    return {
        "fields": dict(zip(kl,tarr)),
        "scores": { 
            "precision": a[0],
            "recall": a[1],
            "fscore": a[2]
        }
    }
    

silversubs = ParsedSubmission.objects.filter(id=475)
for silversub in silversubs:
    results = scorelables(
        unicode_csv_reader(silversub.image.goldparse),
        unicode_csv_reader(silversub.text)
    )
    silversub.score = 100*results["scores"]["fscore"]
    silversub.result = json.dumps(results)
    silversub.save()
    
