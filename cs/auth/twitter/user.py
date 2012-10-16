from zope.interface import implements
from interfaces import ITwitterUser
from Products.PlonePAS.plugins.ufactory import PloneUser

class TwitterUser(PloneUser):
    implements(ITwitterUser)

