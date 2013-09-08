from collective.beaker.interfaces import ISession
from cs.auth.twitter import TWMessageFactory as _
from cs.auth.twitter.interfaces import ICSTwitterPlugin
from cs.auth.twitter.plugin import SessionKeys
from plone.registry.interfaces import IRegistry
from Products.CMFPlone import PloneMessageFactory as pmf
from Products.PluggableAuthService.interfaces.plugins import IExtractionPlugin
from Products.statusmessages.interfaces import IStatusMessage
from urlparse import parse_qsl
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.publisher.browser import BrowserView

import oauth2 as oauth
import urllib

try:
    import json
except ImportError:
    import simplejson as json

TWITTER_REQUEST_TOKEN_URL = 'https://api.twitter.com/oauth/request_token'
TWITTER_ACCESS_TOKEN_URL = 'https://api.twitter.com/oauth/access_token'
TWITTER_AUTH_URL = 'https://api.twitter.com/oauth/authorize'
TWITTER_USER_DATA_URL = 'https://api.twitter.com/1.1/users/show.json'


class AuthorizationTokenKeys:
    """Constants used to look up authorization keys
    """

    oauth_token = "cs.auth.twitter.oauth_token"
    oauth_token_secret = "cs.auth.twitter.oauth_token_secret"
    oauth_callback_confirmed = "cs.auth.twitter.oauth_callback_confirmed"


class TwitterLogin(BrowserView):
    """This view implements the Twitter OAuth login protocol.

    The user may access the view via a link in an action or elsewhere.

    We ask twitter an authentication token, save it in session and redirect
    the user with this token to Twitter.

    The 2nd step of the process is handled by the next BrowserView

    """

    def __call__(self):
        registry = getUtility(IRegistry)
        TWITTER_CONSUMER_KEY = registry.get('cs.auth.twitter.controlpanel.ITwitterLoginSettings.twitter_consumer_key').encode()
        TWITTER_CONSUMER_SECRET = registry.get('cs.auth.twitter.controlpanel.ITwitterLoginSettings.twitter_consumer_secret').encode()

        # Create an Oauth Consumer
        oauth_consumer = oauth.Consumer(key=TWITTER_CONSUMER_KEY,
                                        secret=TWITTER_CONSUMER_SECRET)

        oauth_client = oauth.Client(oauth_consumer)

        # Set the callback URL. Be sure that callback urls are allowed in
        # Twitter App configuration. Do not leave blank the field of the
        # callback url when creating the app, otherwise this login method
        # *will not work*.
        return_args = ''
        if self.request.get('came_from', None) is not None:
            return_args = {'came_from': self.request.get('came_from')}
            return_args = '?' + urllib.urlencode(return_args)

        pps = getMultiAdapter(
            (self.context, self.request),
            name='plone_portal_state'
        )
        portal_url = pps.portal_url()

        url = portal_url + '/@@twitter-login-verify' + return_args

        args = {
                'oauth_callback': url,
            }
        body = urllib.urlencode(args)
        resp, content = oauth_client.request(
            TWITTER_REQUEST_TOKEN_URL, 'POST',
            body=body
        )

        if resp.get('status', '999') != '200':
            msg = _(u"Error getting the authorization token from Twitter. "
                    u"Try again please"
            )
            IStatusMessage(self.request).add(msg, type="error")
            self.request.response.redirect(self.context.absolute_url())
            return u""
        else:
            # The request was successful, so save the token in the session
            # and redirect the user to Twitter
            request_token = dict(parse_qsl(content))
            session = ISession(self.request)
            session[AuthorizationTokenKeys.oauth_token] = request_token['oauth_token']
            session[AuthorizationTokenKeys.oauth_token_secret] = request_token['oauth_token_secret']
            session[AuthorizationTokenKeys.oauth_callback_confirmed] = request_token['oauth_callback_confirmed']
            session.save()

            args = {
                'oauth_token': request_token['oauth_token'],
            }

            self.request.response.redirect(
                    "%s?%s" % (TWITTER_AUTH_URL, urllib.urlencode(args),)
                )


class TwitterLoginVerify(BrowserView):
    """
        This BrowserView handles the 2nd step of the Oauth authentication with
        Twitter.

        It checks the authentication token saved in the 1st step against
        Twitter and if it's successful saves everything in the session so that
        Plone's Authentication and Credential extraction plugin
    """
    def __call__(self):
        registry = getUtility(IRegistry)
        TWITTER_CONSUMER_KEY = registry.get('cs.auth.twitter.controlpanel.ITwitterLoginSettings.twitter_consumer_key').encode()
        TWITTER_CONSUMER_SECRET = registry.get('cs.auth.twitter.controlpanel.ITwitterLoginSettings.twitter_consumer_secret').encode()

        oauth_token = self.request.get('oauth_token')
        oauth_verifier = self.request.get('oauth_verifier')

        session = ISession(self.request)

        # Check if the provided oauth_token and the one we have from the
        # previous step are the same.
        if oauth_token != session[AuthorizationTokenKeys.oauth_token]:
            msg = _(u"Your oauth token is not correct. Please try again")
            IStatusMessage(self.request).add(msg, type="error")
            self.request.response.redirect(self.context.absolute_url())
            return u""

        # Check if the provided verifier is OK, querying Twitter API.
        token = oauth.Token(session[AuthorizationTokenKeys.oauth_token],
                            session[AuthorizationTokenKeys.oauth_token_secret],
                            )
        consumer = oauth.Consumer(key=TWITTER_CONSUMER_KEY,
                                 secret=TWITTER_CONSUMER_SECRET)
        client = oauth.Client(consumer, token)
        args = {
                'oauth_verifier': oauth_verifier,
            }
        body = urllib.urlencode(args)
        resp, content = client.request(TWITTER_ACCESS_TOKEN_URL, 'POST', body)
        if resp.get('status', '999') != '200':
            msg = _(u"Error authenticating with Twitter. Please try again.")
            IStatusMessage(self.request).add(msg, type="error")
            self.request.response.redirect(self.context.absolute_url())
            return u""

        # Save the data in the session so that the extraction plugin can
        # authenticate the user to Plone and save the oauth_token
        # for future queries to Twitter API
        access_token = dict(parse_qsl(content))
        session = ISession(self.request)
        session[SessionKeys.user_id] = str(access_token['user_id'])
        session[SessionKeys.screen_name] = access_token['screen_name']
        session[SessionKeys.oauth_token] = access_token['oauth_token']
        session[SessionKeys.oauth_token_secret] = access_token['oauth_token_secret']

        # Query Twitter API for user data
        token = oauth.Token(session[SessionKeys.oauth_token],
                            session[SessionKeys.oauth_token_secret],
                            )
        consumer = oauth.Consumer(key=TWITTER_CONSUMER_KEY,
                                  secret=TWITTER_CONSUMER_SECRET)
        client = oauth.Client(consumer, token)
        args = {
                'user_id': session[SessionKeys.user_id]
            }
        body = urllib.urlencode(args)
        url = TWITTER_USER_DATA_URL + '?' + body
        resp, content = client.request(url, 'GET')
        if resp.get('status', '999') != '200':
            msg = _(u"Error getting user information. Please try again.")
            IStatusMessage(self.request).add(msg, type="error")
            self.request.response.redirect(self.context.absolute_url())
            return u""

        us = json.loads(content)
        session[SessionKeys.screen_name] = us.get(u'screen_name', '')
        session[SessionKeys.name] = us.get(u'name', session[SessionKeys.screen_name])
        session[SessionKeys.profile_image_url] = us.get(u'profile_image_url', '')
        session[SessionKeys.description] = us.get(u'description', '')
        session[SessionKeys.location] = us.get(u'location')
        session.save()

        # Add user data into our plugin storage:
        acl = self.context.acl_users
        acl_plugins = acl.plugins
        ids = acl_plugins.listPluginIds(IExtractionPlugin)
        for id in ids:
            plugin = getattr(acl_plugins, id)
            if ICSTwitterPlugin.providedBy(plugin):
                if plugin._storage.get(session[SessionKeys.user_id], None) is None:
                    user_data = {
                        'screen_name': session[SessionKeys.screen_name],
                        'fullname': session[SessionKeys.name],
                        'profile_image_url': session[SessionKeys.profile_image_url],
                        'description': session[SessionKeys.description],
                        'location': session[SessionKeys.location]
                    }
                    plugin._storage[session[SessionKeys.user_id]] = user_data

        msg = pmf(u"Welcome. You are now logged in.")
        IStatusMessage(self.request).add(msg, type="info")

        return_args = ''
        if self.request.get('came_from', None) is not None:
            return_args = {'came_from': self.request.get('came_from')}
            return_args = '?' + urllib.urlencode(return_args)

        return_url = self.context.absolute_url() + '/logged_in' + return_args
        self.request.response.redirect(return_url)
