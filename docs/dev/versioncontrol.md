# Version control

Version control is achieved using Git.

- Each sprint checks out a new branch. The sprint number increments upward by 1 integer.
- At the completion of the sprint, after all features, bug fixes etc have been thoroughly tested, merge the sprint into master.
- Once merged into master, on each Medusa instance:
  1. Stop the Medusa service with `sudo service medusa stop`.
  2. Pull the latest master to the server with `git pull`.
  3. Restart the Medusa service with `sudo service medusa start`.
  4. Test each production server thoroughly.
  
## Pushing to production
```
git checkout master
git pull origin master
git merge sprint_X
```

First, fix any merge conflicts, then:

```
git tag -a v[version#] -m "version [version#]"
git push origin master
```

For each production server:
1. Disconnect from load balancer.
2. Poweroff the server.
3. Take a backup image.
4. Power on the server.
5. Stop the medusa servie and any other related services.
6. Modify any auxiliary config and service files.
7. Install any additional new software outside of the virtualenv.
8. Prepare the new version of the application:
```
cd /var/www/medusa
source env/bin/activate
git pull origin master
pip install -i requirements.txt
```
9. (first server only) Perform any database migrations:
```
python manage.py db migrate
python manage.py db upgrade
```
10. Make sure the app loads the production settings, currently in `/var/www/medusa/app/__init__.py`:
```
# set config
app.config.from_envvar('MEDUSA_PRODUCTION_SETTINGS')
```

10. Start the medusa service and any other related services, test and inspect the logs.
11. Once satisfied, rejoin the load balncer and repeat for subsequent production servers.
