# Version control

Version control is achieved using Git.

- Each sprint checks out a new branch. The sprint number increments upward by 1 integer.
- At the completion of the sprint, after all features, bug fixes etc have been thoroughly tested, merge the sprint into master.
- Once merged into master, on each Medusa instance:
  1. Stop the Medusa service with `sudo service medusa stop`.
  2. Pull the latest master to the server with `git pull`.
  3. Restart the Medusa service with `sudo service medusa start`.
  4. Test each production server thoroughly.
  
