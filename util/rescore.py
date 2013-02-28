import os
import sys
gpdir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.sys.path.append(gpdir)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aocr.settings")

from scoring.models import *
from scoring.views import *
from scoring.forms import *

import nltk
from difflib import SequenceMatcher

import json

from sklearn.metrics import precision_recall_fscore_support
import csv
import StringIO
import chardet

import pprint

silversubs = ParsedSubmission.objects.filter(parse_type="silver")
for silversub in silversubs:
    results = scorelables(
        unicode_csv_reader(silversub.image.silverparse.lower()),
        unicode_csv_reader(silversub.text.lower())
    )
    change = 100*results["scores"]["fscore"] - silversub.score
    if abs(change) > 0.01 and change < 0:
        print silversub.id, silversub.score, 100*results["scores"]["fscore"], (100*results["scores"]["fscore"] - silversub.score)
        oldresults = json.loads(silversub.result)
        for f in oldresults["fields"]:
            if f.lower() in results["fields"]:
                if oldresults["fields"][f] != results["fields"][f.lower()]:
                    print "NOMATCH", siversub.image.name, f, oldresults["fields"][f], results["fields"][f.lower()]
            else:
                print "NINR", f
    silversub.score = 100*results["scores"]["fscore"]
    silversub.result = json.dumps(results)
    silversub.save()

goldsubs = ParsedSubmission.objects.filter(parse_type="gold")
for goldsub in goldsubs:
    results = scorelables(
        unicode_csv_reader(goldsub.image.goldparse.lower()),
        unicode_csv_reader(goldsub.text.lower())
    )
    change = 100*results["scores"]["fscore"] - goldsub.score
    if abs(change) > 0.01 and change < 0:
        print goldsub.id, goldsub.score, 100*results["scores"]["fscore"], (100*results["scores"]["fscore"] - goldsub.score)
        oldresults = json.loads(goldsub.result)
        for f in oldresults["fields"]:
            if f.lower() in results["fields"]:
                if oldresults["fields"][f] != results["fields"][f.lower()]:
                    print "NOMATCH", goldsub.image.name, f, oldresults["fields"][f], results["fields"][f.lower()]
            else:
                print "NINR", f
    goldsub.score = 100*results["scores"]["fscore"]
    goldsub.result = json.dumps(results)
    goldsub.save()
