from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'muwonder.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^$', include("soundcloudapi.urls", namespace="soundcloudapi")),
    url(r'^soundcloudapi/', include("soundcloudapi.urls", namespace="soundcloudapi")),
    url(r'^admin/', include(admin.site.urls))
)
