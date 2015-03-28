Photo Management using Dropbox Core API and Heroku
==================================================

This is the 3rd iteration of my photo and video management solution. The first version can be found [here](https://github.com/jlehikoinen/media-management-helper). I wanted to have the solution to be independent of running anything at home on a Mac mini and run this completely in the cloud. This was also good opportunity to learn how Heroku works and how to interact with Dropbox Core API. See the complete photo management solution [here](http://www.trrt.me/#!./md/photo_management.md).

This version is using [Dropbox Core API  webhooks](https://www.dropbox.com/developers/webhooks/docs) and Python web app running in Heroku. The web app part is heavily based on the [Markdown Webhook](https://github.com/dropbox/mdwebhook) example.

This solution uses [Redis To Go](https://addons.heroku.com/redistogo) Heroku add-on. The Redis To Go entry-level plan "Nano" is free, but you need to add valid credit card information to Heroku Billing section.

The main script `db_mover.py` creates a key-value pair to Redis when new files are uploaded to Dropbox Camera Uploads folder. The key-value pair expires automatically in 20 seconds and it should be enough for the script to finish running. This prevents race condition when webhook reacts to the changes in Dropbox during the script execution.

**Note! I'd suggest creating a separate Dropbox account for testing the functionality of this tool.**

**Requirements:**

* [Dropbox](https://www.dropbox.com/) account
* [Carousel](https://itunes.apple.com/us/app/carousel-by-dropbox/id825931374?mt=8) app
* [Heroku](https://www.heroku.com/) account
* [Heroku Toolbelt](https://toolbelt.heroku.com) installed
* Credit card for registering [Heroku add-ons](https://addons.heroku.com)

**Heroku add-ons:**

* [Redis To Go](https://addons.heroku.com/redistogo)
* [Papertrail](https://addons.heroku.com/papertrail) (optional)
* [New Relic APM](https://addons.heroku.com/newrelic) (optional)

Main steps
----------

* Create a new Dropbox app
* Deploy to Heroku
* Configure Dropbox webhook
* Test

Create a new Dropbox app
------------------------

Go to [Dropbox App Console](https://www.dropbox.com/developers/apps) and Create app.

Settings:
* Dropbox API app
* Files and datastores
* No - My app needs access to files already on Dropbox
* All file types - My app needs access to a user's full Dropbox. Only supported via the Core API.

![Dropbox Core API](https://dl.dropboxusercontent.com/u/3972607/GitHub/Dropbox-CoreAPI-app.png)

Other settings (optional):

`OAuth 2 > Allow implicit grant: Disallow`

Generate access token

`OAuth 2 > Generated access token > Generate`

Write down the App secret and the Generated access token.

Test Dropbox Core API with cURL using the access token:

`$ curl https://api.dropbox.com/1/account/info -H "Authorization: Bearer <access token>"`

Example output:

```
{"referral_link": "https://db.tt/2wbthj", "display_name": "John Doe", "uid": 1234567, "locale": "en", "email_verified": true, "team": null, "quota_info": {"datastores": 0, "shared": 3558555318, "quota": 1121523335168, "normal": 126771121734}, "is_paired": false, "country": "FI", "name_details": {"familiar_name": "John", "surname": "Doe", "given_name": "John"}, "email": "john@doe.net"}
```

Deploy with "Deploy to Heroku" button
-------------------------------------

The easiest way to deploy this app to Heroku is to use the button below. If you want to do the deployment part more manually, jump to the next section.

[![Deploy](https://www.herokucdn.com/deploy/button.png)](https://heroku.com/deploy)

After the app has finished building, create a new Heroku projects folder (optional):

`$ mkdir ~/heroku-projects`

`$ cd ~/heroku-projects`

Login to your Heroku account:

`$ heroku login`

Clone the app from Heroku:

`$ heroku clone -a <app name>`

`$ cd <app name>`

Open `config.py` with a text editor and make your own adjustments.

Deploy your changes:

`$ git add .`

`$ git commit -am "my configs"`

`$ git push heroku master`

If everything went ok, jump to the [Configure Dropbox webhook](https://github.com/jlehikoinen/db-mover#configure-dropbox-webhook) section of this page.

Deploy manually
---------------

### Create a local Heroku project

Create a new Heroku projects folder (optional):

`$ mkdir ~/heroku-projects`

`$ cd ~/heroku-projects`

Clone the project from GitHub:

`$ git clone https://github.com/jlehikoinen/db-mover.git`

`$ cd db-mover`

Open `config.py` with a text editor and make your own adjustments.

1. Source folder location
2. One or two target folders
3. Target folder location(s)
4. 'Unsorted' folder location
5. File types (arrays)
6. Subfolder descriptions
7. Dropbox log file location
8. Date & time formats (optional)
9. Lockfile expiration (optional)
10. Year & month regex (optional)

Create a Flask secret key:

`$ python`

`>>> import os`

`>>> os.urandom(24)`

Write down the random key.

Example:

```
'1p\xf9\xb4Yq(*ac\x1fx\xb4x\x13\xde}P\x9a\x94/U\xa8\x1e'
```

Initialize a fresh Git repository:

`$ git init`

Add all files:

`$ git add .`

Make your first commit:

`$ git commit -am "my configs"`

### Create and configure the Heroku app

Login to your Heroku account:

`$ heroku login`

Create a new Heroku app:

`$ heroku create <app name>`

Example output:

```
Creating db-1234... done, stack is cedar-14
https://db-1234.herokuapp.com/ | https://git.heroku.com/db-1234.git
Git remote heroku added
```

Write down app URL: `https://<app name>.herokuapp.com`

Add Redis To Go add-on:

`$ heroku addons:add redistogo`

Redis To Go URL is added automatically to Heroku config.

Add Dropbox app secret:

`$ heroku config:add APP_SECRET='<app secret>'`

Add Dropbox access token:

`$ heroku config:add ACCESS_TOKEN='<access token>'`

Add Flask secret key:

`$ heroku config:add FLASK_SECRET_KEY='<your_random_key>'`

Add time zone (optional):

`$ heroku config:add TZ='Europe/Helsinki'`

This will change the Dyno time zone so the Dropbox log file will get correct time stamps, but the Heroku log stream remains unaffected.

List of time zones: [Wikipedia](http://en.wikipedia.org/wiki/List_of_tz_database_time_zones)

With [Papertrail](https://addons.heroku.com/papertrail) add-on you can configure the time zone correctly.

Verify your Heroku app configuration:

`$ heroku config`

```
ACCESS_TOKEN:          3qSsGe1tdzEAAAABCDAAIc1QPkmma57JxhjJY5KgtaolnuCLeZz0Gt_kOB4qu_13
APP_SECRET:            q34reftdsu7mi3i
FLASK_SECRET_KEY:      1p\xf9\xb4Yq(*ac\x1fx\xb4x\x13\xde}P\x9a\x94/U\xa8\x1e
REDISTOGO_URL:         redis://redistogo:6d1c43a131267754052cfe833220r6d8@angelfish.redistogo.com:11161/
TZ:                    Europe/Helsinki
```

### Deploy to Heroku

When everything is in place, push the app to Heroku. Heroku will install all the depencies automatically during the deployment.

Push the code to Heroku:

`$ git push heroku master`

Verify that the app is running:

`$ heroku ps`

Example output:

```
=== web (1X): `gunicorn app:app`
web.1: up 2015/03/27 08:12:07 (~ 1h ago)
```

If your app is not running, run:

`$ heroku ps:scale web=1`

Open app in browser:

`$ heroku open`

Check Heroku logs that everything is fine so far:

`$ heroku logs`

You should already see few events in the log after the initial deployment and configuration changes.

Configure Dropbox webhook
-------------------------

Go back to [Dropbox App Console](https://www.dropbox.com/developers/apps) > App name

Add Heroku app URI to Webhook URIs:

`https://<app name>.herokuapp.com/webhook`

Webhooks Status should change to "Enabled" after clicking the "Add" button.

Test
----

Tail the Heroku log stream to see what's happening in real time. You should already see few events in the log after the initial deployment and Dropbox webhook requests.

`$ heroku logs --tail`

If you want to follow only app specific entries:

`$ heroku logs --tail --source app`

Take a couple of photos and upload them to Dropbox. See the log for debug information.

Go to Dropbox and see the photos in new location: e.g. `My Media Archive/2015/2015-03`

Check the Dropbox log file: `My Logs/db-webhook.txt`

_Sometimes the web app reacts "slowly" and doesn't move the file to target folder instantly. This is because of the Redis lockfile and Dropbox webhook /delta behavior. To work around this, edit some file in Dropbox or take another photo and upload it. This should be fixed in the future.._

After the testing, scale down the Heroku dyno (optional):

`$ heroku ps:scale web=0`

Monitoring
----------

Manage your app on [Heroku Dashboard](https://dashboard.heroku.com) > App name.

Monitor Redis To Go usage from [Heroku Dashboard](https://dashboard.heroku.com) > App name > Add-ons > Redis To Go or by entering following command:

`$ heroku addons:open redistogo`

If you want to have more control over logging and monitoring, install these Heroku add-ons:

* [Papertrail](https://addons.heroku.com/papertrail)
* [New Relic APM](https://addons.heroku.com/newrelic)
