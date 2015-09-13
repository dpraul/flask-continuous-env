# Continuous Integration and Deployment with Flask & Travis CI
Build environment for Flask development with Grunt for frontend development.  
Testing and integration handled by Travis CI. 
Zero-downtime deployment stack with Nginx and Gunicorn, configured easily with Fabric locally or from Travis CI. 
Build flow based off of [Batista Harahap's configuration](http://www.bango29.com/continuous-web-development/)

## Setup
1. Install the following:
    - [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) (you probably have this already)
    - [Python](https://www.python.org/) & [pip](https://pip.pypa.io/en/latest/installing.html)
    - [node.js](https://nodejs.org/en/)
2. Run `npm install -g bower -g less` to install bower & lessc
3. Run `bower install` to install browser packages from bower.json into /static/bower_components/
4. Install virtualenv using `pip install virtualenv` (Note: see [flask virtualenv install docs](http://flask.pocoo.org/docs/0.10/installation/) for more info)
5. Setup virtualenv:
    1. Run `virtualenv env`
    2. On Windows: `env\scripts\activate`; On Linux: `. env/bin/activate`
6. Install python packages with `pip install -r requirements.txt` (NOTE: Make sure you have activated the python virtualenv prior.)
7. Copy `flask_site/config/config_sample.yml` to `flask_site/config/config.yml` and **DO NOT ADD IT TO GIT** (do not delete `config_sample.yml`, it is used for testing)
8. Change `secret_key` in `config.yml`

## Develop
- New Flask routes are added to `routes.yml` with associated controllers in the `controllers` sub-package
- Install JS and CSS plugin resources with [bower](http://bower.io/):
    - Use `bower search PACKAGE` to find a package.
    - Use `bower install PACKAGE --save` to install and remember package in `bower.json` (i.e. `bower install animate.css --save`)
    - Add resources to bundles in `bundles.yml` so they are compiled by [Flask-Assets](http://flask-assets.readthedocs.org/en/latest/)
- If you install a new python package with pip, run: `pip freeze > requirements.txt`
- See [Testing Flask Applications](http://flask.pocoo.org/docs/0.10/testing/) for useful info on how to make tests comprehensive.
- If you make any changes to `flask_site/config/config.yml`, the file must be manually uploaded to `/home/$USER/blue-green/config/config.yml`

## Run
Run `python start.py` to start Flask locally at 127.0.0.1:5000.  
Run `python start.py production` to test the production configuration.

## Test
Run `nosetests --with-xunit --with-xcoverage --cover-package=flask_site --cover-erase tests`

## Deploy
Fabric is used to easily setup and push code to deployment servers. Deployment configuration is based off of the [0-downtime blue-green deployment](http://dan.bravender.net/2014/8/24/Simple_0-Downtime_Blue_Green_Deployments.html) style.  
Tested on Debian wheezy, but with minor alterations to `fabfile.py` it should work with other distros.

### Variables
Several variables are referenced in this section. Following is their descriptions:

- `$DEPLOY_HOSTS` - the hosts you will deploy to (comma separated - I've only tested with one host)
- `$DEPLOY_PASS` - the ssh password you will set for your deployment user (default: `admin`) - **NOT THE ROOT PASSWORD**
- `$LIVE_SERVER_URL` - the URL people will use to access your server (i.e. example.com)
- `$NEXT_SERVER_URL` - the URL you can use to test changes before going live (i.e. dev.example.com)

### Setting up
This only has to be done once. If you'd like to use a different user besides `admin`, change env.user in `fabfile.py`

#### From your remote machine as root:
1. `apt-get update`
2. `apt-get install -y sudo` (this is only necessary if it's not already installed) 
3. `adduser admin`, and set the password to something feisty.
4. `adduser admin sudo`

#### From your local machine:
1. `pip install fabric gitric`
2. `fab -H $DEPLOY_HOSTS -p $DEPLOY_PASS --set LIVE_SERVER_URL=$LIVE_SERVER_URL,NEXT_SERVER_URL=$NEXT_SERVER_URL prod setup_machine`

### Deploy automatically using Travis CI
See `.travis.yml` if you're interested in exactly what's going on.  
If you'd like to automatically deploy but manually switch from the new version to live, remove `cutover` from `.travis.yml` and 
skip step 1 of the "Deploy Manually" section.

1. Navigate to [Travis CI](https://travis-ci.org/) and enable this repository to be built (login with your Github credentials).
2. In settings, add the following environment variables (make sure they are all set to not display in log):     
    - `DEPLOY_HOSTS`
    - `DEPLOY_PASS`
3. Commit or push some changes to `master` branch.


### Deploy Manually
1. `fab -H $DEPLOY_HOSTS -p $DEPLOY_PASS prod deploy`, enter `$DEPLOY_PASS` again when prompted
    - Alternatively, you can:
        - add your local public key to `~/.ssh/authorized_keys` on your production servers, or 
        - use `--set SSH_PUB_KEY_FILE=$YOUR_PUB_KEY_LOCATION` to automatically add and remove the key during deployment. 
2. (optional) test from `$NEXT_SERVER_URL`
3. `fab -H $DEPLOY_HOSTS -p $DEPLOY_PASS prod cutover`

If you don't intend to test the server before going live, you can run the commands at the same time:   
`fab -H $DEPLOY_HOSTS -p $DEPLOY_PASS prod deploy cutover`

## Notes
- To skip Travis builds, include [ci skip] in the commit message.
- For a nice git branching model: http://nvie.com/posts/a-successful-git-branching-model/
- Because of Flask-Assets, the first user to visit your newly-deployed site will take a long time to load (while resources compile). 
Circumvent this by visiting `$NEXT_SERVER_URL` before running `fab cutover`
