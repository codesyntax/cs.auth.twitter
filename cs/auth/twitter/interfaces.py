from zope.interface import Interface
from zope.publisher.interfaces.browser import IDefaultBrowserLayer

class ITwitterLoginLayer(IDefaultBrowserLayer):
    """
    Zope 3 browser layer for collective.facebooklogin.
    """


class ITwitterUser(Interface):
    """
    Marker interface for Users logged in through Twitter

    """

class ICSTwitterPlugin(Interface):
    """
    Marker interface
    """