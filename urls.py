from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('scoring.views',
    # Examples:
    url(r'^$', 'home', name='home'),
    url(r'^list$', 'listimages', name='listimages'),
    url(r'^submissions/parse/(?P<parse_id>\d*)$', 'view_parse'),
    url(r'^submissions/ocr/(?P<ocr_id>\d*)$', 'view_ocr'),
    url(r'^scoring/ocr/(?P<image_name>.*)$', 'submit_ocr'),
    url(r'^scoring/silver-parse/(?P<image_name>.*)$', 'submit_silver_parse'),
    url(r'^scoring/gold-parse/(?P<image_name>.*)$', 'submit_gold_parse'),    
)