from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template.loader import get_template
from django.contrib.auth.decorators import login_required
from ragendja.auth.decorators import staff_only
from django.template import Context
from django.core.cache import cache
from app.models import *
import gdata.service
import gdata.alt.appengine
from gdata.auth import AuthSubToken
from gdata.docs.service import *
from gdata.service import NonAuthSubToken
from gdata.service import RequestError
import logging
from app.gdata_token_store import TokenStore

@login_required # Registerd google user requried
#@staff_only # App developer/admin required
def index(request):
  client = gdata_client(request.user)
  if not validate_users_authsub_token(request.user):
    # no token, send to link to generate
    return_url = request.build_absolute_uri('/authsub_return/')
    url = client.GenerateAuthSubURL(return_url,
          ('http://docs.google.com/feeds/',), secure=False, session=True, domain='lstoll.net') #TODO - domain configurable?
    return HttpResponseRedirect(url)
  
  q = DocumentQuery(categories=['document'])
  logging.debug(q.ToUri())
  feed = client.GetDocumentListFeed(q.ToUri())
  for entry in feed.entry:
    logging.debug(entry.updated)
  return HttpResponse(feed)
  #return render_to_response('index.html')
  
@login_required
def authsub_return(request):
  """Processes return for authsub request"""
  client = gdata_client(request.user)
  
  session_token = None
  auth_token = gdata.auth.extract_auth_sub_token_from_url(request.get_full_path())
  if auth_token:
    # Upgrade the single-use AuthSub token to a multi-use session token.
    session_token = client.upgrade_to_session_token(auth_token)
  if session_token:
    client.token_store.add_token(session_token)
    return HttpResponseRedirect('/')
  else:
    # TODO Error somewhere - handle better
    return HttpResponse("<h1>token not saved..</h1><a href=\"/\">try again</a>")
  

  
def validate_users_authsub_token(user):
  """Validates the given users authsub token"""
  client = gdata_client(user)
  try:
    # Catching the exception should be enough to detect expiry.
    info = client.AuthSubTokenInfo()
    return True
  except NonAuthSubToken:
    return False
  except RequestError:
    # todo if error.status = 403 we need a new token, else transient and handle so.
    return False
    
def gdata_client(user):
  """Gets a GDATA client"""
  client = DocsService()
  gdata.alt.appengine.run_on_appengine(client)
  client.token_store = TokenStore(user)
  return client
    

