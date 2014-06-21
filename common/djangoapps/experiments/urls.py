from django.conf.urls import include, patterns, url
from django.views.generic import TemplateView
from xmodule.modulestore import parsers

# urlpatterns = patterns(
#     'experiments.views',
#         #url(r'(?ix)^experiments', 'experiments_handler', name='experiments_handler'),
#     url(r'(?ix)^experiments/{}$'.format(parsers.URL_RE_SOURCE), 'experiments_handler'),
#     url(r'(?ix)^duplicatesection/{}$'.format(parsers.URL_RE_SOURCE), 'block_clone_handler'),
# )