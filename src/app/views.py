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
from urllib import urlencode
from google.appengine.api import users

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
    
  # we have a keyed user. list docs
  docs = Document.all().filter("user =", request.user).fetch(1000)
  c = {'documents': docs}
  return render_to_response('index.html', c)
  
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
    
@login_required
def document(request, document_id):
  url = request.build_absolute_uri(request.path) # not URI, so we strip query strings.
  doc = db.get(db.Key(document_id))
  
  message = request.REQUEST.get('message', False)
  if 'email' in request.REQUEST:
    if request.REQUEST['email'] == '':
      return HttpResponseRedirect(url + '?message=' + urlencode('Must provide an email address to add'))
    doc.notify.append(request.REQUEST['email'])
    doc.put()
    return HttpResponseRedirect(url)
  if 'remove' in request.REQUEST:
    doc.notify.remove(request.REQUEST['remove'])
    doc.put()
    return HttpResponseRedirect(url)
  
  c = {'doc': doc, 'notify':doc.notify, 'url': url}
  return render_to_response('document.html', c)
  
  
def poller(request):
  if not users.is_current_user_admin():
    return HttpResponse("<h1>Unauthorized</h1>")
  # grab each user.
  for user in User.all().fetch(1000):
    # check if their authsub token is OK. if not, mail them.
    if not validate_users_authsub_token(user):
      message = mail.EmailMessage(sender="Docs Notification <lstoll@lstoll.net>",
                                  subject="Authentication key not working")

      message.to = user.email
      message.body = """
      Hi, Your authentication key isn't working. Please visit to following link to re-activate:

      %s
      """ % (request.build_absolute_uri('/'))

      message.send()
      break
    # get all their documents
    client = gdata_client(user)
    q = DocumentQuery(categories=['document'])
    logging.debug(q.ToUri())
    feed = client.GetDocumentListFeed(q.ToUri())
    retrieved_ids = []
    documents = {}
    for document in Document.all().filter("user =", user).fetch(1000):
      documents[document.doc_id] = document
    for entry in feed.entry:
      retrieved_ids.append(entry.id.text)
      # Just strip all TZ info, to be consistent.
      last_updated = iso8601.parse_date(entry.updated.text).replace(tzinfo=None)
      # see if this doc was in the DB
      if entry.id.text in documents:
        doc = documents[entry.id.text]
        # if existing, and modified differs, update and send mail
        if last_updated > doc.last_updated:
          # updated
          if len(doc.notify) > 0: #only notify if there are people to notify!
            doc.last_updated = last_updated
            doc.title = entry.title.text
            doc.put()
            # send mail.
            message = mail.EmailMessage(sender="Docs Notification <lstoll@lstoll.net>",
                                        subject="Document %s has been updated" % (doc.title))

            message.to = doc.notify
            message.body = """
            Document '%s' has been updated in the last hour. To view:

            %s
            """ % (doc.title, doc.link)

            message.send()
      else:
        # if new, send notification, and save
        doc = Document(doc_id = entry.id.text, user=user, author_email=entry.author[0].email.text,
              last_updated=last_updated, link = entry.GetHtmlLink().href,
              title=entry.title.text, notify=[user.email])
        doc.put()
        documents[doc.doc_id] = doc
        #email
        message = mail.EmailMessage(sender="Docs Notification <lstoll@lstoll.net>",
                                    subject="Document %s has been added" % (doc.title))

        message.to = doc.notify
        message.body = """
        Document '%s' has been added. To view:

        %s
        """ % (doc.title, doc.link)

        message.send()
    # Reconcile docs list, delete if no longer there, and notify.
    for doc_id in documents:
      if doc_id not in retrieved_ids:
        # doc wasn't on server
        doc = documents[doc_id]
        if len(doc.notify) > 0: #only notify if there are people to notify!
          # send mail.
          message = mail.EmailMessage(sender="Docs Notification <lstoll@lstoll.net>",
                                      subject="Document %s has been deleted" % (doc.title))

          message.to = doc.notify
          message.body = """
          Document '%s' has been deleted in the last hour.
          """ % (doc.title)

          message.send()
        db.delete(documents[doc_id])
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
    

