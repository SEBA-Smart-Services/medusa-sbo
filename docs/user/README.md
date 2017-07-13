# User Quickstart

TODO: document user quickstart


## 1. Need To Download & Install The Following Programs
In order to work on the application you will need to download the following programs or get an account. Sometimes you will need an admin from the service to add you to the group to access the information there. 

### PuTTY
Need to generate a key to remote access the application

### Python

### Atom (or any other text editor that allows you to work with github)


## 2. Need Access Or Accounts For The Following


## 3. Current File System


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





