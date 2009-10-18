from django.conf.urls.defaults import *
from ragendja.urlsauto import urlpatterns
from ragendja.auth.urls import urlpatterns as auth_patterns

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = auth_patterns + patterns('',
    (r'^$', 'app.views.index'),
    (r'^authsub_return/', 'app.views.authsub_return'),
    (r'^poller', 'app.views.poller'),
    (r'^document/(.*)', 'app.views.document'),
    
    # Example:
    # (r'^tetherme_django/', include('tetherme_django.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    #(r'^django-admin/(.*)', admin.site.root),
) + urlpatterns
