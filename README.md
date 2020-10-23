RUET Contest Management System
------------------------------------
<<<<<<< HEAD
A Contest Management System for competitive programming community. It will help a community to track all the programmers and their performance. A user can also track his ups and downs using various analytics.

How to install?
-----------------
Bash code for Ubuntu/Debian.

    # clone the repository
    $ git clone https://github.com/joynahid/ruetcms.git
    $ cd ruetcms
    $ pip3 install pipenv
    $ pipenv shell
    $ pipenv sync
    
    $ flask run //run the app
=======
A Contest Management System for competitive programmers. It will help a community to track all the programmers and their performance. A user can also track his ups and downs using various analytics.

Tools
-------
- Flask
- Bootstrap
- Chart.js

How to install?
-----------------
First install python3 virtual environment. And activate it. Then clone this repository in your virtual environment and install all the requirements using pip. The codes below will work for Ubuntu/Debian.

    # clone the repository
    $ git clone https://github.com/joynahid/ruetcms.git
    $ cd /path/to/ruetcms
    $ pip3 install -r requirements.txt

    # to run this app write below code in your terminal
    $ export FLASK_APP = app.py
    $ python3 app.py //run the app
>>>>>>> 66894d29abca90a0e11a4c213d858d344b7ac9af