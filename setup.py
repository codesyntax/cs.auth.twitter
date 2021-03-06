from setuptools import setup, find_packages
import os

version = '1.2.dev0'

setup(name='cs.auth.twitter',
      version=version,
      description="Twitter based login for Plone",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from
      # http://pypi.python.org/pypi?:action=list_classifiers
      classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
        ],
      keywords='pas plugin plone authentication twitter',
      author='Mikel Larreategi',
      author_email='mlarreategi@codesyntax.com',
      url='https://github.com/codesyntax/cs.auth.twitter/',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['cs', 'cs.auth'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'oauth2',
      ],
      entry_points="""
      # -*- Entry points: -*-

      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
