# Onboarding

This is suppose to be a brief guide on some of the applications needed when getting started with Medusa development as well as some other pointers that may help. The purpose of Medusa is to create a plug and play app that can integrate with any of the tools we currently use. Because of this we try to make Medusa as modular as possible so that we can quickly and simply add in the best features available.

## 1. Need To Download & Install The Following Programs

In order to work on the application you will need to download the following programs.

### PuTTY

PuTTY is needed to SSH into the application. SSH is just a secure way of connecting to a remote instance stored on an exteral computer (hosted by AWS).

You can download PuTTY from [here](https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html). You will also need the key generator utility as well so either download the single package with all the utilities or make sure you get the key generator utility as well.

Create a new session by typing in the IP address and and adding the security key as per the instructions below. Don't forget to save this new session so that it is easier to open next time. If the Instance is new you will need to setup the private and public keys yourself in AWS (amazon web server).

You will need to grab the keys that will give PuTTY access to the development environment. The keys can be found on the google drive under Medusa -> Engineering -> Security. In order to add the key to putty you will need to convert from a PEM file to a ppk file using PuTTY generator, follow the steps outlined [here](https://tecadmin.net/convert-pem-to-ppk-private-key/) on how to do this. Once the new ppk key has been saved you can add it to the corresponding PuTTY session from SSH -> Auth in the catergory bar to the left.

### Atom (or any other text editor that allows you to work with github)

Atom is a great text editor that is easy to integrate with the git repository so you can make changes and see the results quickly. As it is the main text editor it is recommended to get atom as other developers can help with any issues you may have. You can get the latest version of atom [here](https://atom.io/). Next you will need to create a new project folder through File -> Add Project Folder. This will be the location on your own PC where the project will be stored.

Once you have installed atom and set up a project file you should download the remote sync add-on so that you can quickly upload and download changes from the git repository of the EC2 instance. Go to File -> settings and click on the packages tab. In the search bar type "remote-sync" and click install. Next you will need to configure the remote connection between this folder and the git repository by right clicking the main project folder, go to remote-sync and click *"configure"*. Enter the details (similar to PuTTY setup) and ensure *"uploadOnSave"* is ticked so that all your changes are automatically uploaded to the repo. You should now be able to download the current repository by right-clicking the main folder, going to remote-sync and clicking *"Download folder"*. The file will slowly populate your main project folder (This download should be performed every time you download changes from the main github repo.). You can add files to ignore when uploading in the *".remote-sync.json"* folder to stop unneccesary clutter both uploading and downloading.

### Python (if you have a new instance that does not already have it installed)

Currently the app is being developed in Python3, so make sure it is installed on your EC2 instance by typing `python --version` if it comes back with `python 3.x.x` then you have the correct version otherwise follow [these instructions](http://docs.python-guide.org/en/latest/starting/install3/linux/) to install the latest.

We will also need a virtual environment when working with Medusa to install virtual environment use the following command `sudo apt-get install python-virtualenv`. Once installed change directories to the main app folder (`cd /var/www/medusa`) and create the virtual directory using `virtualenv env`, this will create a new directory/folder called env which will contain all your environment packages. to make sure all the latest packages/dependencies are installed activate the virtual environment (see below on how to activate and deactivate the virtual environment) and type `pip install -r requirements.txt`. For more information on the virtual environment head [here](http://flask.pocoo.org/docs/0.12/installation/#virtualenv).

## 2. Need Access Or Accounts For The Following

Having an account for the following services will help improve team coordination and in some cases is necessary for development.

### Github

[Github](https://github.com/) is main repository for all developments of the app with master being the production version of the app and sprints being the development versions of the app. Print branches should be used for development and testing purposes, no new features should be added to the master before testing and review. New sprint branches should be created fortnightly after a sprint review however this is not always possible so the lifetime of a sprint may end up longer. With the release of Medusa 0.2.0 a new support component of Medusa became available whose purpose is to fix any major bug issues and release them to production therefore any bug fixes can be pushed straight to the master branch after verifying the bug has been fixed. The only time this isn't true is for db migrations to fix issues. In this case the production database server will also need to be updated therefore if a bug fix requires a db migration then it needs to be pushed to a sprint branch.

### Slack

Is used for communication but can also be synced to the github repository to get notifications on the latest changes and uploads. While it is not crucial to have it makes the team development process easier. You need to be added to a slack team therefore contact the slack administrator in order to get an account.

### Trello

Trello is a card based board system that the team uses to assign, create and review tasks related to medusa. You will need to create a [Trello account](https://trello.com/) and get added to the board by the Trello admin. Once added you will have access to two different boards. The first board is **Medusa Epics** which gives a broad picture of where Medusa is heading and the second board is **Medusa** which is used for specific bite size tasks. The main board for developers is **Medusa** which is seperated into several smaller baords with fairly self explanitory names.

### Google Drive

You will need a [google account](https://www.google.com/drive/) so you can access several key pieces of information such as SSH keys and diagrams. Once you have an account give one of the medusa admins your account so they can send you an invite. It is worth while going through the latest presentation and documents in the drive to grasp an understanding of what medusa is and the goals heading forward.

### Amazon Web Server

[Amazon web server](https://aws.amazon.com/) (AWS) is the main page for behind the scenes action on the EC2 instances (development environments that we connect to via putty), databases for storing data and other web critical facilities. For access to AWS you will need to get the AWS admin to add you to account. Once you have access you will see a number of different services available. Medusa uses the following services: EC2, RDS, S3, IAM. The main ones for new developers to become familiar with are EC2 which is used for managing server instances and RDS which manages the databases. Always remember to shut off any development instances that you are not using as they cost money per hour of usage (for development databases just ensure no one else is using it at the time).

If you have a fresh instance remember to follow the [server hardening](server_hardening.md) instructions to reduce risks from attacks.

## 3. App & the current setup

The application has been developed in Python using the flask packages for web application (if you are unfamiliar with flask it is a good idea to read up on some of the basics found [here](http://flask.pocoo.org/)). Flask is a great tool that is simple to use for web development as it gives the developer a great variety of tools and flexibility while dealing with the more difficult aspects of web development. It comes with a number of extensions which you will come across in Medusa but for now just trying to understand the basics is the important part. The current Filing system needs some cleaning up however the following will outline where each piece of the app lives.

### Templates

Templates are the html pages that render on the user web browser when the person tries to access the application. A large portion of the templates can be found under `app/templates` and some of the templates have been further seperated into indivdual folders within the templates section to make them easier to find. If a template cannot be found in this folder then it will be located under the specific site package. These packages can be found by SSHing into the EC2 instance and going to `/var/www/medusa/env/lib/python3.5/site-packages/SPECIFICPACKAGERELATEDTOFEATURE`. In some cases these site package templates can be "overwritten" by creating a new temaplate in the app template folder and giving it the same name as the site package template. Templates found in the site package folders should not be modified unless absolutely necessary. Moving forward we may use blue prints which creates a modular folder including templates, models and controllers in the same folder. This will make it easier add and remove new features going forward.

### Database Models

Models are used to tell the database how to store the data it recieves. This may seem confusing at first but reading up on the main features of models in [flask sqlalchemy](http://flask.pocoo.org/docs/0.12/patterns/sqlalchemy/) and looking at some of the models in the app can give you a better understanding of their purpose. The models can be found in several different places within the app depending on when the feature was developed. The current preferred file system attempts to put models and contollers in their own folder related to a particuler feature (i.e. the site data agent folder contains the models and controllers related to the site data agent along with some other things). However prior to this models where placed into the `app/models` folder, therefore when looking for models first check for an individual file. If there is no individual folder containing models then it is probably in the models folder.

### Controllers

Controllers are used to control the flow of data to and from the web pages as well as handling validation, define the URLs to use, some security and other logic behind the web pages. Unfortunately as there are so many controller they have ended up in various different places. As mentioned earlier the current format is to keep everything as modular as possible. However prior to this a majority of the controllers ended up within the `app/controller.py` file. The bottom half of the main controller file contains ITP related controller while ticketing controllers ended up in the `app/ticket/controllers.py` folder. This may just take some time getting use to and looking through files until the format is changed. Apart from these developer created controllers there are also package controllers which get used often in the background. These controllers once again live in the `/var/www/medusa/env/lib/python3.5/site-packages/SPECIFICPACKAGERELATEDTOFEATURE` and should not be changed in any way unless absolutely necessary.

### Styling, images and javascript

The static folder `app/static` contains all the external CSS, Javascript and Images for the application. Keeping these things seperate from the pages makes them reusable and easy to adapt as styles change. In addition Medusa follows the [material deisgn light](styling.md)  style guide to keep the website looking slick and uniform.

### Migrations

The migrations folder is key to the version control for the database. Each new update to the models needs to be migrated to the database for the app to continue working. The "versions" of the database are found in the migrations folder which should not be manually altered in anyway. In order to update use the following commands from the main app folder:
* `python manage.py db migrate`
* `python manage.py db upgrade`
    
These two commands will alter the database models and upgrade the tables as required, this process can brake the application so be careful when updating the database. For further help please refer to the [documentation](https://flask-migrate.readthedocs.io/en/latest/) on database migrations.

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

The virtual environment should be started before completing any development tasks.

Activate virtual environment from /var/www/medusa
`source env/bin/activate`

End virtual environment
`deactivate`

the virtual environment will also hold all your application dependencies which are the packages the application needs to have installed in order to run successfully. If a new package needs to be installed into the app is needs to be added to the *"requirements.txt"* to ensure all instances have the latest and most up to date dependencies. To do this either enter the dependency with the current version manually into the requirements.txt otherwise you can do it using the [pip freeze](https://pip.pypa.io/en/stable/reference/pip_freeze/) method however this may add sub dependencies to your *"requirements.txt"* which may not be a great thing

### To Run The Application In Flask:

Set up the config variables for the app
`export MEDUSA_DEVELOPMENT_SETTINGS=/var/lib/medusa/medusa-development.cfg`

run from /var/www/medusa
`python wsgi.py`

Sometimes the previous session won't close down properly and it will tell you that a session is already in progress. To find out what the session number is type
`ps -fA | grep python`

Look for the line that mentions something about meudsa running, not the data importer and type
`kill SESSIONNUMBER`

After big changes to the app the Medusa app should be restarted using
`sudo systemctl stop medusa`
`sudo systemctl start medusa`

If any changes are made to Nginx it can be reset similarly using
`sudo systemctl stop nginx`
`sudo systemctl start nginx`
keep in mind though that you should stop medusa before stopping nginx and then start nginx before starting medusa up again.

To view the log information for the app use the following commands
`tail -f /var/log/uwsgi/medusa.log`
`tail -f /var/log/nginx/nginx.log`
A seperate PuTTY window should be used to track logs during development and testing.

### Working with tables in MySQL
#TODO: Access 

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

#TODO: Adding SSH keys to your development server




