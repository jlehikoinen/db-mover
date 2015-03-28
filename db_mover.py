from datetime import datetime
import logging
import os
import re
import time

import redis
from dropbox.client import DropboxClient
from dropbox.rest import ErrorResponse
import config as cfg

# API token
access_token = os.environ['ACCESS_TOKEN']

# DropboxClient instance
db_client = DropboxClient(access_token)

# Redis
redis_url = os.environ['REDISTOGO_URL']
redis_client = redis.from_url(redis_url)

# Dropbox date & time format
# Example: Sun, 25 Jan 2015 18:36:24 +0000
db_date_format = '%a, %d %b %Y %H:%M:%S +0000'

# Include Dropbox /delta media info metadata
include_media_info = True

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
    """Download log file from Dropbox."""

    if item_exists(cfg.db_log):
        logger.debug('Downloading log file')
        out = open(cfg.local_log, 'wb')
        with db_client.get_file(cfg.db_log) as f:
            out.write(f.read())
    else:
        logger.debug('No log file found in Dropbox. Using local template.')


def upload_log_file():
    """Upload log file to Dropbox."""

    logger.debug('Uploading log file')
    f = open(cfg.local_log, 'rb')
    response = db_client.put_file(cfg.db_log, f, overwrite=True)


def item_exists(path):
    """Check if file or folder exists in Dropbox

    Parameters
        path: complete Dropbox file path

    Returns
        False if file is (not permanently) deleted or not found
        True if file exists
    """

    try:
        path_metadata = db_client.metadata(path)
        # logger.debug('File metadata: ' + str(path_metadata))
        # Check if file is 'deleted'
        if 'is_deleted' in path_metadata:
            logger.debug(path + ' is deleted')
            return False
    except ErrorResponse as e:
        if e.status == 404:
            logger.debug('http response code: ' + str(e.status))
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

    Parameters
        target_path: base path defined in config
        year: year from metadata or from file name
        month: month from metadata or from file name
        media_type: empty or photo/video description

    Returns
        complete_path: full target path string (e.g. path/to/target/2015/2015-02)
    """

    complete_path = target_path + '/' + year + '/' + year + \
        '-' + month + media_type

    logger.debug('Creating new folder ' + complete_path)

    try:
        db_client.file_create_folder(complete_path)
    except ErrorResponse as e:
        if e.status == 403:
            logger.debug('Target folder ' + complete_path +
                         ' already exists')

    return complete_path


def move_file(source_path, target_path, file_name):
    """Move file to target folder.
    Rename the file if it already exists in target folder.

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
        db_client.file_move(source_path,
                            os.path.join(target_path, file_name))
    except ErrorResponse as e:
        if e.status == 403:
            file_name = file_name_base + '_' + date_time + extension
            logger.info('File already exists in ' + last_path
                        + ' folder. New name: ' + file_name)
            db_client.file_move(source_path,
                                os.path.join(target_path, file_name))


def parse_time_taken(item, item_info):
    """Parse time_taken attribute from media info metadata.

    Parameters
        item: metadata item
        item_info: photo_info or video_info

    Returns
        year: string, e.g. 2015
        month: string, e.g. 03
    """

    year = ''
    month = ''

    # If time_taken value exists
    if (item[item_info]['time_taken'] is not None):
        logger.debug('Time taken: ' + item[item_info]['time_taken'])

        d = datetime.strptime(item[item_info]['time_taken'], db_date_format)
        # formatted_time = d.strftime(cfg.log_date_format)
        year = d.strftime('%Y')
        month = d.strftime('%m')

    return year, month


def main(uid):
    """Main hook.

    Parameters
        uid: user id from webhook notification request
    """

    logger.debug('STARTING WEBHOOK')
    logger.debug('UID: ' + str(uid))

    # Check if Redis lockfile exists
    lockfile_exists = redis_client.exists('lockfile')
    logger.debug('Lockfile exists: ' + str(lockfile_exists))

    if not lockfile_exists:

        # /delta cursor for the user (None the first time)
        cursor = redis_client.hget('cursors', uid)

        has_more = True

        # Loop de loop
        while has_more:

            # Include cursor, prefix_path and include_media_info in result
            result = db_client.delta(cursor, cfg.source_dir, include_media_info)

            # Iterate over metadata contents
            for path, item in result['entries']:

                # Default values
                is_photo = False
                is_video = False
                year = ''
                month = ''
                target_path = ''

                # Skip deleted files and folders
                if (item is None or item['is_dir']):
                    continue

                # Create a lockfile to Redis and set expiration
                redis_client.setex('lockfile', 'IAMALOCKFILE', cfg.lockfile_exp)

                # Item metadata
                logger.debug('File metadata: ' + str(item))

                # Download log file
                get_log_file()

                # Get source path and file name
                source_path = item.get('path')
                file_name = os.path.basename(source_path)

                # Find out if there's year and month values available
                if 'photo_info' in item:

                    is_photo = True
                    year, month = parse_time_taken(item, 'photo_info')

                elif 'video_info' in item:

                    is_video = True
                    year, month = parse_time_taken(item, 'video_info')

                else:
                    # Try parsing year, month and extension from file name
                    year, month, extension = get_info_from_file_name(source_path)
                    logger.debug('Year and month from file name: '
                                 + year + ' ' + month)
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

            # Update cursor
            cursor = result['cursor']
            redis_client.hset('cursors', uid, cursor)

            # Repeat only if there's more to do
            has_more = result['has_more']

if __name__ == "__main__":
    main()