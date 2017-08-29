import cyclone.web
import api_doc
from twisted.internet.tcp import _AbortingMixin
from wiapi import api_manager
from front.handlers import home
from front.handlers import user

from local_settings import DEBUG

url_patterns = [
    (r'/', home.HomeHandler),
    # (r'/active/', home.ActiveHandler),
    # (r'/startup/', home.StartupHandler),
    # (r'/sync/', home.SyncHandler),
    # (r'/guide/', guide.GuideHandler),
    # (r'/syncdb/', home.SyncdbHandler),
    # (r'/flushdb/', home.FlushdbHandler),

    (r'/crossdomain\.xml', home.CrossdomainHandler),
    (r'/crossdomain\.xml', cyclone.web.RedirectHandler,
     {'url': '/static/crossdmain.xml'}),
]
if DEBUG == True:
    apiurls = api_manager.get_urls() + url_patterns + [(r"/doc$", api_doc.ApiDocHandler), (r"/map$", api_doc.ApiMapHandler),]
else:
    apiurls = url_patterns
