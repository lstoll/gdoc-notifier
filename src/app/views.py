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
import iso8601
from google.appengine.api import mail

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
  return render_to_response('index.html')
  
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
  
@staff_only
def poller(request):
  # grab each user.
  for user in User.all().fetch(1000):
    # check if their authsub token is OK. if not, mail them.
    if not validate_users_authsub_token(request.user):
      #email them to visit site to re-auth
      break
    # get all their documents
    client = gdata_client(user)
    q = DocumentQuery(categories=['document'])
    logging.debug(q.ToUri())
    feed = client.GetDocumentListFeed(q.ToUri())
    for entry in feed.entry:
      # Just strip all TZ info, to be consistent.
      last_updated = iso8601.parse_date(entry.updated.text).replace(tzinfo=None)
      # find the doc in the datastore
      docs = Document.all().filter("user =", user).filter("doc_id =", entry.id.text).fetch(1)
      if len(docs) > 0:
        # if existing, and modified differs, update and send mail
        if last_updated > docs[0].last_updated:
          # updated
          docs[0].last_updated = last_updated
          docs[0].title = entry.title.text
          docs[0].put()
          # send mail.
          message = mail.EmailMessage(sender="Docs Notification <lstoll@lstoll.net>",
                                      subject="Document %s has been updated" % (docs[0].title))

          message.to = user.email
          message.body = """
          Document '%s' has been updated in the last hour. To view:

          %s
          """ % (docs[0].title, docs[0].link)

          message.send()
      else:
        # if new, send notification, and save
        doc = Document(doc_id = entry.id.text, user=user, author_email=entry.author[0].email.text,
              last_updated=last_updated, link = entry.GetHtmlLink().href,
              title=entry.title.text)
        doc.put()
        #email
        message = mail.EmailMessage(sender="Docs Notification <lstoll@lstoll.net>",
                                    subject="Document %s has been added" % (doc.title))

        message.to = user.email
        message.body = """
        Document '%s' has been added. To view:

        %s
        """ % (doc.title, doc.link)

        message.send()
  return HttpResponse("Completed")
    
  
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
    

