"""
Own configs for Heroku
"""

# Source folder location
source_dir = '/Camera Uploads'

# Use one or two target folders
one_target_dir = False

# One common target folder location
target_dir_common = '/My Media Archive'

# or

# Two separate target folder locations
target_dir1 = '/Kuvat ja videot/Kuvat'
target_dir2 = '/Kuvat ja videot/Videot'




# Temp
source_dir = '/Kuvat ja videot/Slo-mos'
target_dir1 = '/Apps/DB Mover/test1'
target_dir2 = '/Apps/DB Mover/test2'




# Unsorted files location
unsorted_dir = '/Apps/DB Mover/Unsorted Media Files'

# File types
pics_types = ['.jpg', '.JPG']
vids_types = ['.mov', '.MOV']

# Photo and video subfolder descriptions
# These are used if one_target_dir is False
pics_desc = '-kuvat'
vids_desc = '-videot'

# Dropbox log file location
db_log = '/Apps/DB Mover/Logs/db-webhook.txt'

# Logging
log_date_format = '%d.%m.%Y %H.%M.%S'
file_date_format = '%Y%m%d-%H%M%S'
local_log = 'log_template.txt'

# Lockfile expiration in seconds
lockfile_exp = 20

# Year & month regex
regex_year = r'^20\d\d$'
regex_month = r'^(0?[1-9]|1[012])$'

#####
