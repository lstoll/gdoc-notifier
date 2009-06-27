from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template.loader import get_template
from django.contrib.auth.decorators import login_required
from ragendja.auth.decorators import staff_only
from django.template import Context
from django.core.cache import cache
from app.models import *

#@login_required # Registerd google user requried
#@staff_only # App developer/admin required
def index(request):
  return render_to_response('index.html')
