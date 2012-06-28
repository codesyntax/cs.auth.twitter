from zope import schema
from zope.interface import Interface
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.z3cform import layout

from cs.auth.twitter import TWMessageFactory as _

class ITwitterLoginSettings(Interface):
    
    twitter_consumer_key = schema.TextLine(title=_(u'Twiter Consumer Key'), 
                                description=_(u'The App ID/API Key you got when creating the app at https://dev.twitter.com/apps/new'))
    
    twitter_consumer_secret = schema.TextLine(title=_(u'Twitter Consumer Secret'), 
                                    description=_(u'The App Secret Key you got when creating the app at https://dev.twitter.com/apps/new'))

    twitter_access_token = schema.TextLine(title=_(u'Twitter Access Token'), 
                                    description=_(u'The Access Token of your app you got when creating the app at https://dev.twitter.com/apps/new'))

    twitter_access_token_secret = schema.TextLine(title=_(u'Twitter Access Token Secret'), 
                                    description=_(u'The Access Token Secret of your app you got when creating the app at https://dev.twitter.com/apps/new'))


class TwitterLoginControlPanelForm(RegistryEditForm):
    schema = ITwitterLoginSettings

TwitterLoginControlPanelView = layout.wrap_form(TwitterLoginControlPanelForm, ControlPanelFormWrapper)
TwitterLoginControlPanelView.label = _(u"Twitter Login settings")
