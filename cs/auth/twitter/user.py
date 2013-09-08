from interfaces import ITwitterUser
from Products.PlonePAS.plugins.ufactory import PloneUser
from zope.interface import implements


class TwitterUser(PloneUser):
    implements(ITwitterUser)
