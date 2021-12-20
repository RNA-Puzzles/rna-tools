#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
pip install django-ipware

https://stackoverflow.com/questions/4581789/how-do-i-get-user-ip-address-in-django
"""

APP_PATH = '/home/rnamasonry/rnamasonryweb_env/rnamasonry-web/'
LIMIT_PER_USER = 5  # 2
POWER_USERS = ['iamb@genesilico.pl', 'azyla@genesilico.pl', 'magnus@genesilico.pl']

from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.utils.datastructures import MultiValueDictKeyError
from web import settings
from os import sep, makedirs, listdir, umask

from django.db.models import Q

from configparser import ConfigParser
import re
import uuid
import subprocess
import sys
import tempfile
import shutil
import json
import os,re,sys
import zipfile
from io import StringIO
from django.http import JsonResponse

try:
    from app.models import Job, JOB_STATUSES, SAXS_FORMATS
except:
    print("App is missing")

#from lib.yapdb_parser.pdb_parser_lib import *
#from lib.rna_pdb_edit_occupancy import rna_pdb_edit_occupancy
#from lib.rna_pdb_tools.rna_pdb_tools.utils.rna_convert_pseudoknot_formats.rna_ss_pk_to_simrna import get_multiple_lines, is_pk

import string

CORES = 80

intervals = (
    ('weeks', 604800),  # 60 * 60 * 24 * 7
    ('days', 86400),    # 60 * 60 * 24
    ('hours', 3600),    # 60 * 60
    ('minutes', 60),
    ('seconds', 1),
)


def display_time(seconds, granularity=2):
    result = []

    for name, count in intervals:
        value = seconds // count
        if value:
            seconds -= value * count
            if value == 1:
                name = name.rstrip('s')
            result.append("{} {}".format(value, name))
    return ', '.join(result[:granularity])


def home(request):
    print('request.path', request.path)
    error = ''
    return render_to_response('home.html', RequestContext(request, {
        'load': ''
    }))

def tools(request):
    ids = []
    for i in range(0, 10):
        id = str(uuid.uuid4()).split('-')[0]  # name plus hash
        ids.append(id)
        j = Job()
        j.job_id = id
        j.status = 0
        print('tools, make:', j)
        j.save()
        # create folder
        try:
            JOB_PATH = settings.JOBS_PATH + sep + j.job_id
            umask(0o002)
            makedirs(JOB_PATH)
        except OSError:
            pass
    return render_to_response('tools.html', RequestContext(request, {
        'ids': ids,
    }))


def stop(request, job_id):
    """Stop job based on job_id /stop/<job_id>. Get the job, change status to stopped
    and re-direct page to /job/,job_id>
    """
    try:
        j = Job.objects.get(job_id=job_id.replace('/', ''))
    except:  # DoesNotExist:  @hack
        return render_to_response('dont_exits.html', RequestContext(request, {
        }))

    # status stopped but not yet stopped
    # this is signal to demon to stop it and when processed killed
    # then set True .stopped
    # see daemon.py for more
    j.stopped = False 
    j.status = JOB_STATUSES['stopped']
    j.save()
    # shell way to kill it # tRNA_with_SAXS-d5a37d86
    return HttpResponseRedirect('http://genesilico.pl/rnamasonry/jobs/' + j.job_id + '/')  # @hack


def download_project_dir(request, job_id):


    job_dir = settings.JOBS_PATH + sep + job_id
    fname="%s.zip" % job_id

    response = HttpResponse(content_type='application/zip')
    response['Content-Disposition'] = 'filename=%s'%fname
    all_files = []


    try:
        job_status = Job.objects.get(job_id=job_id.replace('/', ''))
    except:
        job_status = None

    for root, dirs, files in os.walk(job_dir):
        for fn in files:
            abs_fn = os.path.join(root,fn)
            #print os.path.relpath(abs_fn, job_dir)
            with open(abs_fn, 'rb') as ifile:
                all_files.append( (os.path.relpath(abs_fn, job_dir), ifile.read()) )

    buffer = StringIO()
    zip = zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED)
    for name, f in all_files:
        zip.writestr( os.path.join(job_id, name), f)
    zip.close()
    buffer.flush()
    #the import detail - we return the content of the buffer
    ret_zip = buffer.getvalue()
    buffer.close()
    response.write(ret_zip)



    return response


def about(request):
    return render_to_response('about.html', RequestContext(request, {}))


def help(request):
    return render_to_response('help.html', RequestContext(request, {}))


def contact(request):
    return render_to_response('contact.html', RequestContext(request, {}))


def run(request, tool, job_id):
    print(job_id)
    try:
        j = Job.objects.get(job_id=job_id.replace('/', ''))
    except:  # DoesNotExist:  @hack
        return render_to_response('dont_exits.html', RequestContext(request, {
        }))

    import os
    job_dir = settings.JOBS_PATH + sep + job_id

    job_id = job_id.replace('/', '')

    if tool == 'cat':
        with open(job_dir + '/run.sh', 'w') as f:
             f.write('rm ' + job_id + '.pdb\n')
             f.write('cat *.pdb > ' + job_id + '.pdb 2> log.txt \n')
             f.write('ls *.pdb > log.txt\n')
             f.write("echo 'DONE' >> log.txt \n")

    if tool == 'seq':
        print('run, seq,' + job_id)
        with open(job_dir + '/run.sh', 'w') as f:
             f.write('rna_pdb_toolsx.py --get-seq *.pdb > log.txt\n')
             f.write('ls *.pdb >> log.txt\n')
             f.write("echo 'DONE' >> log.txt \n")

    if tool == 'seq-search':
        print('run, seq,' + job_id)
        seq = request.GET['seq']        
        with open(job_dir + '/run.sh', 'w') as f:
             f.write('rna_pdb_toolsx.py --get-seq *.pdb > log.txt\n')
             f.write('ls *.pdb >> log.txt\n')
             f.write("echo 'DONE' >> log.txt \n")


    if tool == 'calc-rmsd':
        print('run, seq,' + job_id)
        import glob
        import os
        files = glob.glob(job_dir + "/*pdb")
        files.sort(key=os.path.getmtime)
        files = [os.path.basename(f) for f in files]
        #print("\n".join(files))
        with open(job_dir + '/run.sh', 'w') as f:
             f.write("""
rna_calc_rmsd.py -t %s %s &> log.txt\n
""" % (files[0], ' '.join(files[1:])))
             f.write('ls *.pdb >> log.txt\n')
             f.write("echo 'DONE' >> log.txt \n")

    if tool == 'extract':
        from urllib.parse import unquote
        #url = unquote(request.POST['extract'])
        opt = request.GET['extract']
        with open(job_dir + '/run.sh', 'w') as f:
             f.write("""
for i in *.pdb; do rna_pdb_toolsx.py --extract '%s' $i > ${i/.pdb/_extract.pdb}; done;
""" % opt)
             f.write('ls *.pdb >> log.txt\n')
             f.write("echo 'DONE' >> log.txt \n")

    os.system('cd %s && chmod +x run.sh && ./run.sh &' % job_dir)
    j.status = JOB_STATUSES['running']
    j.save()

    return JsonResponse({'post':'false'})

def file_upload(request, job_id):
    if request.method == 'POST':
        my_file=request.FILES.get('file')
        fn = re.sub(r'[\\/*?:"<>|]',"", str(my_file))
        with open(settings.JOBS_PATH + sep + job_id + '/' + fn , 'wb+') as destination:
            for chunk in my_file.chunks():
                destination.write(chunk)
    return JsonResponse({'post':'false'})


def ajax_job_status(request, job_id):

    job_dir = settings.JOBS_PATH + sep + job_id
    load = ''

    response_dict = {'reload': False}

    #try:
    if 1:
        j = Job.objects.get(job_id=job_id.replace('/', ''))

        #if j.status == JOB_STATUSES['running']:
        #    response_dict['reload']=False
        if j.status == JOB_STATUSES['finished'] or j.status == JOB_STATUSES['stopped']:
            response_dict['reload'] = False
            return JsonResponse({'post':'false'})

        try:
            with open(os.path.join(settings.JOBS_PATH, job_id, 'run.sh')) as f:
                 log = f.read() + '\n'
        except FileNotFoundError:
            log = ''

        try:
            log_filename = os.path.join(settings.JOBS_PATH, job_id, 'log.txt')
            with open(log_filename, 'r') as ifile:
                l = ifile.read()
                log += re.sub(r"[\n]", "</br>", l)

                # --> Clustering
                #log = re.sub(r"[\-]+> Clustering[\w\s]+\d+\%[\s\|#]+ETA:\s+[(\d\-)\:]+\r", "", log)
                # --> Annealing
                #log = re.sub(r"[-]+> Annealing[\w\s]+\d+\%[\s\|#]+ETA:[\d\s\:\-]+\r", "", log)
                # --> Preparing data
                #log = re.sub(r"[\s]{5,}\d+\%[\s\|#]+ETA:[\d\s\:\-]+\r", "", log)
                #log = re.sub(r"[\-]+>[\w\s]+\d+\%[\s\|#]+ETA:\s+[(\d\-)\:]+\r[^\Z]", "", log)
                #log = re.sub(r"[\s]{4,}\d+\%[\s\|#]+ETA:\s+[(\d\-)\:]+\r[^\Z]", "", log)

                # response_dict['log'] = log.replace(' ', '&nbsp')
                response_dict['log'] = log
                if 'DONE' in log:
                    print('Done')
                    j = Job.objects.get(job_id=job_id.replace('/', ''))
                    j.status = JOB_STATUSES['finished']
                    j.save()
                    response_dict['reload'] = True # fix it
        except FileNotFoundError:
            pass
        
    #except:
    #    response_dict['log'] = ""

    print(json.dumps(response_dict))
    return HttpResponse(json.dumps(response_dict), "application/json")

def tool(request, tool, job_id):
    try:
        j = Job.objects.get(job_id=job_id.replace('/', ''))
    except:  # DoesNotExist:  @hack
        return render_to_response('dont_exits.html', RequestContext(request, {
        }))

    try:
        with open(os.path.join(settings.JOBS_PATH, job_id, 'run.sh')) as f:
                 log = f.read() + '\n'

        log_filename = os.path.join(settings.JOBS_PATH, job_id, 'log.txt')
        with open(log_filename, 'r') as ifile:
            log = ifile.read()
            log = re.sub(r"[\n]", "</br>", log)
    except:
        log = ''
    
    return render_to_response(tool + '.html', RequestContext(request, {
        'j': j,
        'log' : log
        }))
