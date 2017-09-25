# User Management

User management is an important part of the application, keeping information secure while making the app as user friendly as possible is an important consideration. To aid in this task the app integrates a number of prepackaged projects from flask including Flask User and Flask Security. These packages simplify the development process and improve security using mature code.

## Setup

User management has been split been controllers taken from packages and templates which have been taken from these packages and updated to suit the needs of the app.

### Controllers

As mentioned at the start we have used a number of packages to simplify the task of user management. Flask User and Security bother offer a variety of premade functions that handle user sessions, logins, password hashing and other features. Because of this most of the login and user controllers have been left to these packages which can be found in `/var/www/medusa/env/lib/python3.5/site-packages/flask_security` and `/var/www/medusa/env/lib/python3.5/site-packages/flask_user` (These folders should not be manipulated unless absolutely necessary, paths are provided for ease of access and understanding).

### Templates

The great thing about Flask User and Security is that html templates found with the same name in the *template* folder will override the default Flask User and Security html templates. Therefore we have pulled all the relavent user management pages into a 2 folders *flask_user* and *security* and manipulated them to fit into the medusa theme (added MDL styling and place pages into base.html layout).

### Models

The User model can be found under `app/models/users.py`

## Other

### Flask Mail

Flask mail has been used to send out links and passwords to users.
