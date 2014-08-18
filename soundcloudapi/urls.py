from django.conf.urls import patterns, url, include
from soundcloudapi import views

urlpatterns = patterns(
    '',
    url(r'^$', views.index, name="index"),
    url(r'^recommends/$', views.RecommendApi.recommends),
    url(r'^criticize_pattern/$', views.RecommendApi.get_criticize_pattern)
)
