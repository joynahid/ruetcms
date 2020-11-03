RUET Contest Management System
------------------------------
A Contest Management System for competitive programming community. It will help a community to track all the programmers and their performances. A user can also track his ups and downs using various analytics.

Hosted on Heroku: https://ruetcms.heroku.com

Points worth Knowing
--------------------
- Coded in Python (Backend), JQuery, HTML, CSS
- Vjudge Scraper (Crawl all the contest information by contest ID)
- Blog System (Markdown and Latex Support)
- Various Analytics
- Powered by Flask

Clone & Install
---------------
Bash code for Ubuntu/ Debian.

    $ git clone https://github.com/joynahid/ruetcms.git
    $ cd ruetcms
    $ pip3 install pipenv
    $ pipenv shell
    $ pipenv sync
    $ flask run