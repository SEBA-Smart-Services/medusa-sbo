# User Quickstart

TODO: document user quickstart


## 1. Need To Download & Install The Following Programs
In order to work on the application you will need to download the following programs or get an account.
### PuTTY
PuTTY is needed to SSH into the application.

You can download PuTTY from [here](https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html).
You will also need the key generator utility as well so either download the single package with all the utilities or make sure you get the key generator utility as well.

You will need to grab the keys that will give PuTTY access to the development environment. The keys can be found on the google drive under Medusa -> Engineering -> Security

Need to generate a key to remote access the application

### Python
Currently the app is being developed in Python3, 

Download virtual environment as well 

### Atom (or any other text editor that allows you to work with github)
Atom is a great text editor that is easy to integrate with the git repository so you can make changes and see the results quickly.

Need remote Sync to access git.

## 2. Need Access Or Accounts For The Following

### Google Drive
You will need a google account so you can access several key pieces of information. Once you have an account give one of the medusa admins your account so they can send you an invite.

### Amazon Web Server

## 3. Current File System
Currently the Filing system needs some cleaning up however the following will outline where each thing lives.

### Rendering Templates
All Jinja templates can be found under app/templates

### Database Models
All models are 

### Static Folder
The static folder (app/static) contains all the external CSS, Javascript and Images for the application. Keeping these things seperate from the pages makes them reusable and easy to adapt as styles change.

### Controllers
Probably the most confusing part of the application is the controllers. While a majority of the controllers are contained within the app/controller.py script, there are some controllers that exist seperate to these.

### Migrations
The migrations folder is key to the version control for the database.

## 4. Useful Things To Know

### Basic Terminal Functions
These functions will help you move around the terminal and make changes to files if you need to.

Looking at current directory
`ls`

Change directory
`cd`

Using vim to manipulate file:
* `vim <filename>` to enter file
* You will start in a executable mode where you can perform functions on the file
  * Press i to start making changes (It will say --Insert-- in the bottom left hand corner)
  * To save press **ESC** to re-enter executable mode, then type **:w** and press **Enter**
  * To exit the file from executable mode type **:q** and then hit **Enter**
    * Can save and exit at the save time by typing **:wq** then pressing **Enter**
  * Avoid pressing **ctrl + s** as this freezes the screen
    * If you do this press **ctrl + q** to unfreeze the screen

### Virtual Environment
Activate virtual environment from /var/www/medusa
`source env/bin/activate`

End virtual environment
`deactivate`

### To Run The Application In Flask:
Tell Flask where to start the app from
`export FLASK_APP=wsgi.py`

run from /var/www/medusa
`flask run --host=0.0.0.0`

Sometimes the previous session won't close down properly and it will tell you that a session is already in progress. To find out what the session is type
`ps -fA | grep python`

Look for the line that has 

### Working with tables in MySQL
Access 

### Working With Git
Check the differences between current and earlier versions
`git status`

See what branch you are working on
`git branch`

Change branches
`git checkout <branchname>`

Pull down the latest uploads from the Git hub repository
`git pull origin <Branch you want to pull from>`

Prepare your latest changes to be pushed to Git hub repository (use . for all files or type in the ones you want to add)
`git add .`

Commit your changes
`git commmit -m <write a short message about your changes>`

Push all commited changes to the repositroy
`git push origin <branch to push changes to>`





