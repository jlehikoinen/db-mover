from datetime import datetime
import logging
import os
import re
import sys
import time

import redis
import dropbox
import config as cfg

"""
Notes

- Possibly existing cursor and 'files_list_folder_continue' method are
  ignored temporarily

"""

# API token
access_token = os.environ['ACCESS_TOKEN']

# Dropbox instance
db_client = dropbox.Dropbox(access_token)

# Redis
redis_url = os.environ['REDISTOGO_URL']
redis_client = redis.from_url(redis_url)

# Dropbox date & time format
# Example: 2017-06-07 14:25:03
db_date_format = '%Y-%m-%d %H:%M:%S'

# Logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(cfg.local_log)
handler.setLevel(logging.INFO)
simple_format = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s',
                                  cfg.log_date_format)
handler.setFormatter(simple_format)
logger.addHandler(handler)


# Helper functions
def get_log_file():
    """Download log file from Dropbox.
    Uses Dropbox's 'files_download_to_file' method
    """

    if item_exists(cfg.db_log):
        logger.debug('Downloading log file')
        db_client.files_download_to_file(cfg.local_log, cfg.db_log)
    else:
        logger.debug('No log file found in Dropbox. Using local template.')


def upload_log_file():
    """Upload log file to Dropbox.
    Uses Dropbox's 'files_upload'
    """

    logger.debug('Uploading log file')
    mode = dropbox.files.WriteMode.overwrite
    with open(cfg.local_log, 'rb') as f:
        response = db_client.files_upload(f.read(), cfg.db_log, mode)


def item_exists(path):
    """Check if file or folder exists in Dropbox.
    Uses Dropbox's 'files_get_metadata' method

    Parameters
        path: complete Dropbox file path

    Returns
        False if file is (not permanently) deleted or not found
        True if file exists
    """

    try:
        path_md = db_client.files_get_metadata(path, include_deleted=True)
        # logger.debug('File metadata: ' + str(path_md))

        # Check if file is 'deleted'
        if (isinstance(path_md, dropbox.files.DeletedMetadata)):
            logger.debug(path + ' is deleted')
            return False
    except dropbox.exceptions.ApiError as e:
        logger.debug('*** Dropbox API error: ', e)
        return False

    return True


def get_info_from_file_name(path):
    """Parse year, month and file extension from file name.
    Carousel naming convention: 2015-02-12 00.05.58.jpg.

    Parameters
        path: full Dropbox path

    Returns
        year: string, e.g. 2015
        month: string, e.g. 03
        extension: string, e.g. jpg
    """

    year = ''
    month = ''

    file_name_dummy, extension = os.path.splitext(path)
    file_name = os.path.basename(path)

    if not year:
        # Try parsing year and month from file name
        year = file_name[:4]
        month = file_name[5:7]

    # Check that year has valid value
    if not re.match(cfg.regex_year, year):
        year = ''

    # Check that month has valid value
    if not re.match(cfg.regex_month, month):
        month = ''

    return year, month, extension


def create_dir_tree(target_path, year, month, media_type=''):
    """Create directory tree if it doesn't exist.
    Uses Dropbox's 'files_create_folder' method

    Parameters
        target_path: base path defined in config
        year: year from metadata or from file name
        month: month from metadata or from file name
        media_type: empty or photo/video description

    Returns
        complete_path: full target path string (e.g. path/to/target/2015/2015-02)
    """

    complete_path = '%s/%s/%s-%s%s' % (target_path, year, year, month, media_type)

    # if not item_exists(complete_path):

    logger.debug('Creating new folder ' + complete_path)
    try:
        db_client.files_create_folder(complete_path)
    except dropbox.exceptions.ApiError as e:
        logger.debug('*** Dropbox API error', e)
        logger.debug('Target folder ' + complete_path + ' probably already exists?')

    return complete_path


def move_file(source_path, target_path, file_name):
    """Move file to target folder.
    Rename the file (=add timestamp) if it already exists in target folder.
    Uses Dropbox's 'files_move' method

    Parameters
        source_path: source folder defined in config
        target_path: target path formed from year and month metadata
        file_name: file name with extension
    """

    last_path = os.path.basename(os.path.normpath(target_path))
    date_time = datetime.now().strftime(cfg.file_date_format)
    file_name_base, extension = os.path.splitext(file_name)

    logger.info('Moving ' + file_name + ' to ' + last_path)

    try:
        db_client.files_move(source_path,
                             os.path.join(target_path, file_name))
    except dropbox.exceptions.ApiError as e:
        logger.debug('*** Dropbox API error', e)
        file_name = file_name_base + '_' + date_time + extension
        logger.info('File already exists in ' + last_path +
                    ' folder. New name: ' + file_name)
        db_client.files_move(source_path, os.path.join(target_path, file_name))


def parse_time_taken(item):
    """Parse time_taken attribute from media info metadata.

    Parameters
        item: metadata item

    Returns
        year: string, e.g. 2015
        month: string, e.g. 03
    """

    year = ''
    month = ''

    # If time_taken value exists
    time_taken_value = str(item.media_info.get_metadata().time_taken)
    if (time_taken_value is not None):
        logger.debug('Time taken: ' + time_taken_value)

        d = datetime.strptime(time_taken_value, db_date_format)
        year = d.strftime('%Y')
        month = d.strftime('%m')

    return year, month


def main():
    """Main hook."""

    logger.debug('STARTING WEBHOOK')

    # Check if Redis lockfile exists
    lockfile_exists = redis_client.exists('lockfile')
    logger.debug('Lockfile exists: ' + str(lockfile_exists))

    if lockfile_exists:
        sys.exit(1)

    try:
        result = db_client.files_list_folder(cfg.source_dir, include_media_info=True)
    except dropbox.exceptions.ApiError as e:
        logger.debug('*** Dropbox API error', e)
        sys.exit(1)

    if len(result.entries) > 0:
        # Create a lockfile to Redis and set expiration
        redis_client.setex('lockfile', 'IAMALOCKFILE', cfg.lockfile_exp)
        # Download log file
        get_log_file()
    else:
        logger.debug('No new files in: %s. Exiting.' % cfg.source_dir)
        sys.exit(1)

    # Iterate over metadata contents
    for item in result.entries:

        # Default values
        is_photo = False
        is_video = False
        year = ''
        month = ''
        target_path = ''

        # Skip deleted files and folders
        if (isinstance(item, dropbox.files.DeletedMetadata) or
            isinstance(item, dropbox.files.FolderMetadata)):
            continue

        # Item metadata
        logger.debug('File metadata: ' + str(item))

        # Get source path and file name
        source_path = item.path_lower
        file_name = os.path.basename(source_path)
        _, extension = os.path.splitext(source_path)

        # Find out if there's media info available
        if (item.media_info is not None and not
            item.media_info.is_pending()):
            year, month = parse_time_taken(item)
        else:
            # Try parsing year, month and extension from file name
            year, month, extension = get_info_from_file_name(source_path)
            logger.debug('Year and month from file name: ' +
                         year + ' ' + month)
            logger.debug('File extension: ' + extension)

        # Validate file extension
        if extension in cfg.pics_types:
            is_photo = True
        elif extension in cfg.vids_types:
            is_video = True

        # Build target folder path
        if year and month:
            # Handle 1 vs 2 target folders option
            if cfg.one_target_dir:
                if is_photo or is_video:
                    target_path = create_dir_tree(cfg.target_dir_common,
                                                  year, month)
            else:
                if is_photo:
                    target_path = create_dir_tree(cfg.target_dir1,
                                                  year,
                                                  month,
                                                  media_type=cfg.pics_desc)
                elif is_video:
                    target_path = create_dir_tree(cfg.target_dir2,
                                                  year,
                                                  month,
                                                  media_type=cfg.vids_desc)
                else:
                    logger.debug('Invalid file type')

        # Move file(s)
        if target_path:
            move_file(source_path, target_path, file_name)
        else:
            # Unsorted folder will be created automatically
            # if it doesn't exist
            move_file(source_path, cfg.unsorted_dir, file_name)

    # Upload log
    upload_log_file()

if __name__ == "__main__":
    main()
