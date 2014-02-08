# Create your views here.

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect,HttpResponseNotFound,HttpResponse
from django.core.urlresolvers import reverse

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
            if "aocr:regiontype" not in rheader:
                rsingleregion = True
            for i in range(len(rheader)):
                rheader[i] = rheader[i].strip()
            continue
        rdict = dict(zip(rheader,r))
        for f in rdict.keys():
            v = rdict[f].strip()
            # pbh: remove outside quotes if any
            if v.startswith('"') and v.endswith('"'): v = v[1:-1]
            if len(v) == 0:
                del rdict[f]
            else:
                rdict[f] = v
        if (len(rdict.keys()) > 0):
            if rsingleregion:
                rlabels["primary"] = rdict
            else:
                if "aocr:regiontype" in rdict:
                    lr = rdict["aocr:regiontype"]
                    if lr not in rlabels:
                        del rdict["aocr:regiontype"]
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
                rval = rlabels[ka[0]][ka[1]]
                tval = tlabels[ka[0]][ka[1]]
                try:
                    rval = float(rval)
                    tval = float(tval)
                except:
                    rval = rlabels[ka[0]][ka[1]]
                    tval = tlabels[ka[0]][ka[1]]                    
                if rval == tval:
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

def home(request):
    datasets = Dataset.objects.all().select_related()
    return render(request,"home.html",{ "datasets": datasets })

def listimages(request):
    parsed = ParsedSubmission.objects.order_by('score')[:10]
    ocr = OcrSubmission.objects.order_by('score')[:10]
    return render(request,"list.html",{ "parsed": parsed, "ocr": ocr })
    
def view_parse(request,parse_id=None):
    parsed = None
    try:
        parsed = ParsedSubmission.objects.get(id=parse_id)
    except Image.DoesNotExist, e:
        return HttpResponseNotFound()
    return render(request,"view-parse.html",{ "parsed": parsed })
    
def view_ocr(request,ocr_id=None):
    ocr = None
    try:
        ocr = OcrSubmission.objects.get(id=ocr_id)
    except Image.DoesNotExist, e:
        return HttpResponseNotFound()
    return render(request,"view-ocr.html",{ "ocr": ocr }) 

def submit_ocr(request,image_name=None):
    image = None
    form = None
    if image_name:
        try:
            image = Image.objects.get(name__exact=image_name)
        except Image.DoesNotExist, e:
            try:
                image = Image.objects.get(uuid__exact=image_name)
            except Image.DoesNotExist, e:
                return HttpResponseNotFound()
    else:
        return HttpResponseNotFound()
    
    if request.method == "POST":           
        form = OcrSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            ocrsub = form.save(commit=False)
            ocrsub.image = image
            if 'file' in request.FILES:
                rawdata = request.FILES['file'].read()
                cdresult = chardet.detect(rawdata)
                charenc = cdresult['encoding']
                ocrsub.text = rawdata.decode(charenc)

                    
            human_tokens = nltk.word_tokenize(image.humantext.lower())
            ocr_tokens = nltk.word_tokenize(ocrsub.text.lower())

            s = SequenceMatcher(None,human_tokens,ocr_tokens)
            ocrsub.result = json.dumps({
                "matches": s.get_matching_blocks(),
				"tokens": ocr_tokens,
                "score": {
                    "ratio": s.ratio()
                }
            })
            ocrsub.score = 100*s.ratio()
            ocrsub.save()
            if 'json' in request.GET:
                r = {
                    "url": ocrsub.get_absolute_url(),
                    "result": json.loads(ocrsub.result)
                }
                return HttpResponse(json.dumps(r), content_type="application/json")
            else:
                return HttpResponseRedirect(ocrsub.get_absolute_url())       
    else:
        form = OcrSubmissionForm() 
        
    return render(request,"ocr-form.html", {
        "form": form,
        "image": image
    })

def submit_silver_parse(request,image_name=None):
    image = None
    form = None
    if image_name:
        try:
            image = Image.objects.get(name__exact=image_name)
        except Image.DoesNotExist, e:
            try:
                image = Image.objects.get(uuid__exact=image_name)
            except Image.DoesNotExist, e:
                return HttpResponseNotFound()
    else:
        return HttpResponseNotFound()
    
    if request.method == "POST":
        form = ParsedSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            silversub = form.save(commit=False)
            silversub.image = image
            silversub.parse_type = "silver"
            if 'file' in request.FILES:
                rawdata = request.FILES['file'].read()
                cdresult = chardet.detect(rawdata)
                charenc = cdresult['encoding']
                silversub.text = rawdata.decode(charenc)
            
            results = scorelables(
                unicode_csv_reader(image.silverparse.lower()),
                unicode_csv_reader(silversub.text.lower())
            )
            silversub.score = 100*results["scores"]["fscore"]
            silversub.result = json.dumps(results)
            silversub.save()
            if 'json' in request.GET:
                r = {
                    "url": silversub.get_absolute_url(),
                    "result": json.loads(silversub.result)
                }
                return HttpResponse(json.dumps(r), content_type="application/json")
            else:            
                return HttpResponseRedirect(silversub.get_absolute_url())
    else:
        form = ParsedSubmissionForm() 
        
    return render(request,"parse-form.html", {
        "form": form,
        "image": image
    })
    
def submit_gold_parse(request,image_name=None):
    image = None
    form = None
    if image_name:
        try:
            image = Image.objects.get(name__exact=image_name)
        except Image.DoesNotExist, e:
            try:
                image = Image.objects.get(uuid__exact=image_name)
            except Image.DoesNotExist, e:
                return HttpResponseNotFound()
    else:
        return HttpResponseNotFound()
    
    if request.method == "POST":
        form = ParsedSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            silversub = form.save(commit=False)
            silversub.image = image
            silversub.parse_type = "gold"
            if 'file' in request.FILES:
                rawdata = request.FILES['file'].read()
                cdresult = chardet.detect(rawdata)
                charenc = cdresult['encoding']
                silversub.text = rawdata.decode(charenc)
                    
            results = scorelables(
                unicode_csv_reader(image.goldparse.lower()),
                unicode_csv_reader(silversub.text.lower())
            )
            silversub.score = 100*results["scores"]["fscore"]
            silversub.result = json.dumps(results)
            silversub.save()
            if 'json' in request.GET:
                r = {
                    "url": silversub.get_absolute_url(),
                    "result": json.loads(silversub.result)
                }
                return HttpResponse(json.dumps(r), content_type="application/json")
            else:            
                return HttpResponseRedirect(silversub.get_absolute_url())
    else:
        form = ParsedSubmissionForm() 
        
    return render(request,"parse-form.html", {
        "form": form,
        "image": image
    })    
