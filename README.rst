=========
BakpdlBot
=========


.. image:: https://img.shields.io/pypi/v/bakpdlbot.svg
        :target: https://pypi.python.org/pypi/bakpdlbot

.. image:: https://img.shields.io/travis/mickboekhoff/bakpdlbot.svg
        :target: https://travis-ci.com/mickboekhoff/bakpdlbot

.. image:: https://readthedocs.org/projects/bakpdlbot/badge/?version=latest
        :target: https://bakpdlbot.readthedocs.io/en/latest/?version=latest
        :alt: Documentation Status




Bot to help manage the Discord server for Backpedal cc.


* Free software:
* Documentation: https://bakpdlbot.readthedocs.io.


Features
--------

* TODO

Google Credentials
------------------

Setup a project with API access as described in https://developers.google.com/docs/api/quickstart/python. Store your credentials (client_secret_*) as bakpdlbot/googledocs/credentials.json 

Run the following command:

    google-oauthlib-tool --client-secrets bakpdlbot/googledocs/credentials.json --credentials bakpdlbot/googledocs/token.json --save --scope https://www.googleapis.com/auth/spreadsheets.readonly

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
