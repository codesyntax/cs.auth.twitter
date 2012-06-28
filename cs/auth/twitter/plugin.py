from zope.app.component.hooks import getSite
from Products.CMFCore.utils import getToolByName
from zope.component import getUtility
from plone.registry.interfaces import IRegistry
import logging

from zope.interface import implements
from zope.publisher.browser import BrowserView

from zope.globalrequest import getRequest

from collective.beaker.interfaces import ISession
from collective.beaker.interfaces import ICacheManager

from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin

from Products.PluggableAuthService.interfaces.plugins import (
        IExtractionPlugin,
        IAuthenticationPlugin,
        ICredentialsResetPlugin,
        IPropertiesPlugin,
        IRolesPlugin,
        IUserEnumerationPlugin,
        IUserFactoryPlugin
    )

from twitter import Api
from cs.auth.twitter.user import TwitterUser
from cs.auth.twitter.interfaces import ITwitterUser
logger = logging.getLogger('cs.auth.twitter')

TWITTER_SEARCH_URL = 'https://api.twitter.com/1/users/search.json'

class SessionKeys:
    """Constants used to look up session keys
    """
    
    user_id            =   "cs.auth.twitter.user_id"
    screen_name        =   "cs.auth.twitter.screen_name"
    name               =   "cs.auth.twitter.name"
    profile_image_url  =   "cs.auth.twitter.profile_image_url"
    description        =   "cs.auth.twitter.description"
    location           =   "cs.auth.twitter.location"
    oauth_token        =   "cs.auth.twitter.oauth_token"
    oauth_token_secret =   "cs.auth.twitter.oauth_token_secret"

class AddForm(BrowserView):
    """Add form the PAS plugin
    """
    
    def __call__(self):
        
        if 'form.button.Add' in self.request.form:
            name = self.request.form.get('id')
            title = self.request.form.get('title')
            
            plugin = CSTwitterUsers(name, title)
            self.context.context[name] = plugin
            
            self.request.response.redirect(self.context.absolute_url() +
                    '/manage_workspace?manage_tabs_message=Plugin+added.')


class CSTwitterUsers(BasePlugin):
    """PAS plugin for authentication against Twitter.
    
    Here, we implement a number of PAS interfaces, using a session managed
    by Beaker (via collective.beaker) to temporarily store the values we
    have captured.
    """
    
    # List PAS interfaces we implement here
    implements(
            IExtractionPlugin,
            ICredentialsResetPlugin,
            IAuthenticationPlugin,
            IPropertiesPlugin,
            IRolesPlugin,
            IUserEnumerationPlugin,
            IUserFactoryPlugin,
        )
    
    def __init__(self, id, title=None):
        self.__name__ = self.id = id
        self.title = title
    #
    # IExtractionPlugin
    # 

    
    def extractCredentials(self, request):
        """This method is called on every request to extract credentials.
        In our case, that means looking for the values we store in the
        session.
        
        o Return a mapping of any derived credentials.
        
        o Return an empty mapping to indicate that the plugin found no
          appropriate credentials.
        """
        
        # Get the session from Beaker.
        
        session = ISession(request, None)
        
        if session is None:
            return None
        
        # We have been authenticated and we have a session that has not yet
        # expired:
        
        if SessionKeys.user_id in session:
            
            return {
                    'src': self.getId(),
                    'userid': session[SessionKeys.user_id],
                    'username': session[SessionKeys.screen_name],
                }
        
        return None
    
    #
    # IAuthenticationPlugin
    # 
    
    
    def authenticateCredentials(self, credentials):
        """This method is called with the credentials that have been
        extracted by extractCredentials(), to determine whether the user is
        authenticated or not.
        
        We basically trust our session data, so if the session contains a
        user, we treat them as authenticated. Other systems may have more
        stringent needs, but we should avoid an expensive check here, as this
        method may be called very often - at least once per request.
        
        credentials -> (userid, login)
        
        o 'credentials' will be a mapping, as returned by extractCredentials().
        
        o Return a  tuple consisting of user ID (which may be different 
          from the login name) and login
        
        o If the credentials cannot be authenticated, return None.
        """
        
        # If we didn't extract, ignore
        if credentials.get('src', None) != self.getId():
            return
        
        # We have a session, which was identified by extractCredentials above.
        # Trust that it extracted the correct user id and login name
        
        if (
            'userid' in credentials and
            'username' in credentials
        ):
            return (credentials['userid'], credentials['username'],)
        
        return None
    
    #
    # ICredentialsResetPlugin
    # 
    
    def resetCredentials(self, request, response):
        """This method is called if the user logs out.
        
        Here, we simply destroy their session.
        """
        session = ISession(request, None)
        if session is None:
            return
        
        session.delete()
    
    #
    # IPropertiesPlugin
    # 
    
    def getPropertiesForUser(self, user, request=None):
        """This method is called whenever Plone needs to get properties for
        a user. We return a dictionary with properties that map to those
        Plone expect.
        
         user -> {}
        
        o User will implement IPropertiedUser.
        
        o Plugin should return a dictionary or an object providing
          IPropertySheet.
          
        o Plugin may scribble on the user, if needed (but must still
          return a mapping, even if empty).
          
        o May assign properties based on values in the REQUEST object, if
          present
        """
        
        if request is None:
            request = getRequest()
        
        session = ISession(request, None)
        if session is None:
            return {}
        
        # Is this an cs.auth.Twitter Twitter user?
        if session.get(SessionKeys.user_id, None) == user.getId():            
            return {
                'fullname': session.get(SessionKeys.name, ''),
                'description': session.get(SessionKeys.description, ''),
                'location': session.get(SessionKeys.location, ''),
            }

        else:
            # If this is a Twitter User, it implements ITwitterUser
            if not ITwitterUser.providedBy(user):
                return {}

            # Try to bring user data from the cache 
            # to avoid queries to Twitter API
            
            cacheManager = getUtility(ICacheManager)
            twitter_user_cache = cacheManager.get_cache('cs-twitter-users', expires=86400)
            if twitter_user_cache.has_key(user.getId()):
                cached_user_data = twitter_user_cache.get(user.getId())
                return {
                        'fullname': cached_user_data['fullname'],
                        'description': cached_user_data['description'],
                        'location': cached_user_data['location'],
                }

            else:
                registry = getUtility(IRegistry)
                TWITTER_CONSUMER_KEY = registry.get('cs.auth.twitter.controlpanel.ITwitterLoginSettings.twitter_consumer_key').encode()
                TWITTER_CONSUMER_SECRET = registry.get('cs.auth.twitter.controlpanel.ITwitterLoginSettings.twitter_consumer_secret').encode()
                TWITTER_ACCESS_TOKEN = registry.get('cs.auth.twitter.controlpanel.ITwitterLoginSettings.twitter_access_token').encode()
                TWITTER_ACCESS_TOKEN_SECRET = registry.get('cs.auth.twitter.controlpanel.ITwitterLoginSettings.twitter_access_token_secret').encode()
                
                api = Api(consumer_key=TWITTER_CONSUMER_KEY,
                          consumer_secret=TWITTER_CONSUMER_SECRET, 
                          access_token_key=TWITTER_ACCESS_TOKEN, 
                          access_token_secret=TWITTER_ACCESS_TOKEN_SECRET)
                try:
                    us = api.GetUser(user.getId())
                except:
                    return {}

                if us.id is not None:
                    user_data =  {
                            'fullname': us.name,
                            'description': us.description,
                            'location': us.location,
                    }
                    twitter_user_cache.put(user.getId(), user_data)
                    return user_data

                return {}

    #
    # IRolesPlugin
    # 
    
    def getRolesForPrincipal(self, principal, request=None):
        """Return a list of roles for the given principal (a user or group).
        
        Here, we simply grant the Member role to everyone we have
        authenticated. We could of course have invented a new role as well,
        in which case we'd want to register it in rolemap.xml.
        
        principal -> ( role_1, ... role_N )
        
        o Return a sequence of role names which the principal has.
        
        o May assign roles based on values in the REQUEST object, if present.
        """
        
        if request is None:
            request = getRequest()
        
        session = ISession(request, None)
        if session is None:
            return ()
        
        if session.get(SessionKeys.user_id, None) != principal.getId():
            return ()
        
        return ('Member',)
    
    #
    # IUserEnumerationPlugin
    # 
    
    def enumerateUsers(self 
                      , id=None
                      , login=None
                      , exact_match=False
                      , sort_by=None
                      , max_results=None
                      , **kw
                      ):
        """This function is used to search for users.
        
        We don't implement a search of all of Twitter (!), but it's important
        that we allow Plone to search for the currently logged in user and get
        a result back, so we effectively implement a search against only one
        value.
        
         -> ( user_info_1, ... user_info_N )
        
        o Return mappings for users matching the given criteria.
        
        o 'id' or 'login', in combination with 'exact_match' true, will
          return at most one mapping per supplied ID ('id' and 'login'
          may be sequences).
          
        o If 'exact_match' is False, then 'id' and / or login may be
          treated by the plugin as "contains" searches (more complicated
          searches may be supported by some plugins using other keyword
          arguments).
          
        o If 'sort_by' is passed, the results will be sorted accordingly.
          known valid values are 'id' and 'login' (some plugins may support
          others).
          
        o If 'max_results' is specified, it must be a positive integer,
          limiting the number of returned mappings.  If unspecified, the
          plugin should return mappings for all users satisfying the criteria.
          
        o Minimal keys in the returned mappings:
        
          'id' -- (required) the user ID, which may be different than
                  the login name
                  
          'login' -- (required) the login name
          
          'pluginid' -- (required) the plugin ID (as returned by getId())
          
          'editurl' -- (optional) the URL to a page for updating the
                       mapping's user
                       
        o Plugin *must* ignore unknown criteria.
        
        o Plugin may raise ValueError for invalid criteria.
        
        o Insufficiently-specified criteria may have catastrophic
          scaling issues for some implementations.
        """
        
        request = getRequest()
        session = ISession(request, None)
        if session is None:
            return ()
        
        if exact_match and id == session.get(SessionKeys.user_id, None):
            return ({
                'id': session[SessionKeys.user_id],
                'login': session[SessionKeys.screen_name],
                'pluginid': self.getId(),
            },)
    
        elif id != session.get(SessionKeys.user_id, None):
            try:
                # Tw
                # Twitter user_ids are integers, so we can check if this is a
                # valid id and if not, avoid the Twitter API query overhead 
                user_id = int(id)
            except ValueError:
                return ()

            
            site = getSite()
            mdata = getToolByName(site, 'portal_memberdata') 
            member_data = mdata._members.get(id)
            
            if member_data is not None:
                return ({
                         'id': id,
                         'login': id,
                         'pluginid': self.getId(),
                     },)

        return ()

    # IUserFactoryPlugin interface
    def createUser(self, user_id, name):
        request = getRequest()
        session = ISession(request, None)
        # Create a TwitterUser just if we are loging in with Twitter
        if session.get(SessionKeys.user_id):
            return TwitterUser(user_id, name)

        return None   