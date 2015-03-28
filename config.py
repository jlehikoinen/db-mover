"""
TODO:
- 1 or more files in buffer, run /delta has_more again?
- Logging should be separated from the main hook
"""

# Source folder location
source_dir = '/Camera Uploads'

# Use one or two target folders
one_target_dir = True

# One common target folder location
target_dir_common = '/My Media Archive'

# or

# Two separate target folder locations
target_dir1 = '/My Photos'
target_dir2 = '/My Videos'

# Unsorted files location
unsorted_dir = '/Unsorted Media Files'

# File types
pics_types = ['.jpg', '.JPG']
vids_types = ['.mov', '.MOV']

# Photo and video subfolder descriptions
# These are used if one_target_dir is False
pics_desc = '-photos'
vids_desc = '-videos'

# Dropbox log file location
db_log = '/My Logs/db-webhook.txt'

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
