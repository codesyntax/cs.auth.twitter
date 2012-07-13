Introduction
============

A PAS plugin to login into a Plone Site using Twitter.


Installation and getting started
-----------------------------------

Add 'cs.auth.twitter' to your buildout.cfg's eggs list.

You have to add a configuration similar to this to your buildout.cfg::

 zope-conf-additional = 
    <product-config beaker>
        session type     file 
        session.data_dir ${buildout:directory}/var/sessions/data
        session.lock_dir ${buildout:directory}/var/sessions/lock 
        session.key      beaker.session
        session.secret   this-is-my-secret-${buildout:directory}
    </product-config>

This is needed because we are using collective.beaker to handle Twitter login
session information.

Install the product in the Plone Control Panel

Create a new Twitter app at https://dev.twitter.com/apps/new and fill in the 
required data in the plugin's control panel form.

Credit
--------

This product contains code written for collective.twitter.accounts
by Franco Pellegrini (@frapell) and Hector Velarde (@hvelarde)
