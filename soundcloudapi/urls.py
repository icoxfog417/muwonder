from django.conf.urls import patterns, url, include
from soundcloudapi import views

urlpatterns = patterns(
    '',
    url(r'^$', views.index, name="index"),
    url(r'^recommends/$', views.RecommendApi.recommends),
    url(r'^criticize_pattern/$', views.RecommendApi.get_criticize_pattern),
    url(r'^require_auth/$', views.require_auth),
    url(r'^authorized/$', views.authorized),
    url(r'^is_connect/$', views.is_connect),
    url(r'^disconnect/$', views.disconnect),
    url(r'^make_playlist/$', views.make_playlist)
)
