# User Management

User management is an important part of the application, keeping information secure while making the app as user friendly as possible is an important consideration. To aid in this task the app integrates a number of prepackaged projects from flask including Flask User and Flask Security. These packages simplify the development process and improve security using mature code.

## Design choices

* It was decided that users could only be created by an admin in Flask admin (see below). This allows the admin team to manage the number of accounts and the roles easily.
* Users can not be deleted, this was to stop any model deletion errors that may occur from referencing a deleted user which would crash the page.
* If a user has the role 'admin' then they should have access to all sites so when creating controllers a seperate admin check may be needed. In addition admin should not populate the users sites with all sites as their admin privilege may be removed and they would still have access to all the sites.

## Setup

User management has been split been controllers taken from packages and templates which have been taken from these packages and updated to suit the needs of the app.

### Controllers

As mentioned at the start we have used a number of packages to simplify the task of user management. Flask User and Security bother offer a variety of premade functions that handle user sessions, logins, password hashing and other features. Because of this most of the login and user controllers have been left to these packages which can be found in `/var/www/medusa/env/lib/python3.5/site-packages/flask_security` and `/var/www/medusa/env/lib/python3.5/site-packages/flask_user` (These folders should not be manipulated unless absolutely necessary, paths are provided for ease of access and understanding).

### Templates

The great thing about Flask User and Security is that html templates found with the same name in the *template* folder will override the default Flask User and Security html templates. Therefore we have pulled all the relavent user management pages into a 2 folders *flask_user* and *security* and manipulated them to fit into the medusa theme (added MDL styling and place pages into base.html layout).

### Models

The User model can be found under `app/models/users.py`. As users are an integral part of the application any changes to this file should be carefully considered in case it breaks the app.

## Other

### Flask Admin

The front end user creation is all done through the admin tab which uses a package called Flask Admin. This package makes managing assets and model creation very simple however where possible the developer should still develop their own seperate management pages. Flask Admin also provides a number of functions and definitions to simplify the viewing and creatioin of asset objects. One thing to mention here is the use of Flask Admins *after_model_change* function which activates on object creation and changes. For the user section there is a bit of code which is designed to generate a random user password for first time use which is sent out using flask mail (below). For more details and uses on flask admin check out the [documentation](https://flask-admin.readthedocs.io/en/latest/).

### Flask Mail

Flask mail is a great application for sending automated mail out based on actions completed on the app. It has been used to send out links and passwords to users on creation of their account. Further information behind this application can be found [here](https://pythonhosted.org/Flask-Mail/)
