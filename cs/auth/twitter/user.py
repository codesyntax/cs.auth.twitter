from zope.interface import implements
from interfaces import ITwitterUser
from Products.PluggableAuthService.PropertiedUser import PropertiedUser

class TwitterUser(PropertiedUser):
    implements(ITwitterUser)

