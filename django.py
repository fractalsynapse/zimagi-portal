from django.conf import settings

from settings.config import Config

#
# Portal API
#
PORTAL = Config.dict('ZIMAGI_PORTALS')
DEFAULT_PORTAL = Config.string('ZIMAGI_DEFAULT_PORTAL', 'development')
