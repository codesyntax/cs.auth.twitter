Introduction
============

A PAS plugin to login into a Plone Site using Twitter. Provides the following features:

* Log in to a Plone site through Twitter: when a user requests to log in to the Plone site he will be redirected to Twitter so that he provides the credentials there, then he will be redirected back to the Plone site and will be identified there.

* The user will be a standard Plone user, so Roles or Group membership can be set.

* Minimal user information is kept in Plone such as full name, screen-name Twitter ID and twitter photo of the user. This is kept to avoid permanent requests to Twitter API. This information is refreshed each time the user logs in to the site.


Installation and getting started
-----------------------------------

Add `cs.auth.twitter` to your buildout.cfg's eggs list. It will install all required dependencies.

Install the product in the Plone Control Panel. This will create a "Login with
Twitter" action into the personal tools toolbar in Plone.


Create a new Twitter app at https://dev.twitter.com/apps/new and fill in the
required data in the plugin's control panel form.

Credit
--------

This product contains code written for collective.twitter.accounts
by Franco Pellegrini (@frapell) and Hector Velarde (@hvelarde)


Compatibility
==============

Plone 4.x
