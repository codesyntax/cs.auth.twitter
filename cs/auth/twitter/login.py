from zope.component import getUtility
from plone.registry.interfaces import IRegistry
import json
import urllib

from zope.publisher.browser import BrowserView

from collective.beaker.interfaces import ISession

from Products.statusmessages.interfaces import IStatusMessage

from cs.auth.twitter import TWMessageFactory as _
from cs.auth.twitter.plugin import SessionKeys

import oauth2 as oauth

from urlparse import parse_qsl


TWITTER_REQUEST_TOKEN_URL = 'https://api.twitter.com/oauth/request_token'
TWITTER_ACCESS_TOKEN_URL = 'https://api.twitter.com/oauth/access_token'

TWITTER_AUTH_URL = 'https://api.twitter.com/oauth/authorize'

class AuthorizationTokenKeys:
    """Constants used to look up authorization keys
    """
    
    oauth_token              = "cs.auth.twitter.oauth_token"
    oauth_token_secret       = "cs.auth.twitter.oauth_token_secret"
    oauth_callback_confirmed = "cs.auth.twitter.oauth_callback_confirmed"


class TwitterLogin(BrowserView):
    """This view implements the Twitter OAuth login protocol.

    The user may access the view via a link in an action or elsewhere. He
    will then be immediately redirected to Twitter, which will ask him to
    authorize this as an application.
    
    Assuming that works, Twitter will redirect the user back to this same
    view, with a code in the request.
    """
    
    def __call__(self):
        registry = getUtility(IRegistry)
        TWITTER_CONSUMER_KEY = registry.get('cs.auth.twitter.controlpanel.ITwitterLoginSettings.twitter_consumer_key').encode()
        TWITTER_CONSUMER_SECRET = registry.get('cs.auth.twitter.controlpanel.ITwitterLoginSettings.twitter_consumer_secret').encode()


        oauth_consumer = oauth.Consumer(key=TWITTER_CONSUMER_KEY,
                                        secret=TWITTER_CONSUMER_SECRET)
        
        oauth_client = oauth.Client(oauth_consumer)

        args = {
                'oauth_callback' : self.context.absolute_url() + '/@@twitter-login-verify',                
            }
        body = urllib.urlencode(args)

        resp, content = oauth_client.request(TWITTER_REQUEST_TOKEN_URL, 'POST', body=body)

        if resp.get('status', '999') != '200':
            IStatusMessage(self.request).add(_(u"Error getting the authorization token from Twitter. Try again please"), type="error")
            self.request.response.redirect(self.context.absolute_url())
            return u""
        else:
            request_token = dict(parse_qsl(content))
            session = ISession(self.request)
            session[AuthorizationTokenKeys.oauth_token] = request_token['oauth_token']
            session[AuthorizationTokenKeys.oauth_token_secret] = request_token['oauth_token_secret']
            session[AuthorizationTokenKeys.oauth_callback_confirmed] = request_token['oauth_callback_confirmed']
            session.save()
            args = {
                'oauth_token' : request_token['oauth_token'],                
            }

            self.request.response.redirect(
                    "%s?%s" % (TWITTER_AUTH_URL, urllib.urlencode(args),)
                )


class TwitterLoginVerify(BrowserView):

    def __call__(self):
        
        session = ISession(self.request)
        token = oauth.Token(session[AuthorizationTokenKeys.oauth_token],
                            session[AuthorizationTokenKeys.oauth_token_secret],
                            )
        registry = getUtility(IRegistry)
        TWITTER_CONSUMER_KEY = registry.get('cs.auth.twitter.controlpanel.ITwitterLoginSettings.twitter_consumer_key').encode()
        TWITTER_CONSUMER_SECRET = registry.get('cs.auth.twitter.controlpanel.ITwitterLoginSettings.twitter_consumer_secret').encode()

        consumer = oauth.Consumer(key=TWITTER_CONSUMER_KEY,
                                 secret=TWITTER_CONSUMER_SECRET)
        client = oauth.Client(consumer, token)    
        resp, content = client.request(TWITTER_ACCESS_TOKEN_URL, 'GET')
        if resp.get('status', '999') != '200':
            IStatusMessage(self.request).add(_(u"Error authenticating with Twitter. Please try again."), type="error")
            self.request.response.redirect(self.context.absolute_url())
            return u""

        access_token = dict(parse_qsl(content))
        
        # Save the data in the session so that the extraction plugin can 
        # authenticate the user to Plone
        
        session = ISession(self.request)
        session[SessionKeys.user_id]            = access_token['user_id']
        session[SessionKeys.screen_name]        = access_token['screen_name']
        session[SessionKeys.oauth_token]        = access_token['oauth_token']
        session[SessionKeys.oauth_token_secret] = access_token['oauth_token_secret']
        
        session.save()
        
        IStatusMessage(self.request).add(_(u"Welcome. You are now logged in."), type="info")
        self.request.response.redirect(self.context.absolute_url())