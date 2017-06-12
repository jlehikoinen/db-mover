from datetime import datetime
import os
import re
import time

import dropbox
import config as cfg

# API token
access_token = os.environ['ACCESS_TOKEN']

db_date_format = '%Y-%m-%d %H:%M:%S'

# Dropbox instance
db_client = dropbox.Dropbox(access_token)

# cfg.source_dir = '/Apps/DB Mover/Unsorted Media Files'
# cfg.source_dir = '/Camera Uploads'

#####

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
        # logger.debug('Time taken: ' + time_taken_value)

        d = datetime.strptime(time_taken_value, db_date_format)
        year = d.strftime('%Y')
        month = d.strftime('%m')

    return year, month


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
    # if not re.match(cfg.regex_year, year):
    #    year = ''

    # Check that month has valid value
    if not re.match(cfg.regex_month, month):
        month = ''

    return year, month, extension

#####

# Default values
is_photo = False
is_video = False
year = ''
month = ''
target_path = ''

has_more = True

# Loop de loop
while has_more:

    # Include cursor, prefix_path and include_media_info in result
    # result = db_client.delta(cursor, cfg.source_dir, include_media_info)
    result = db_client.files_list_folder(cfg.source_dir, include_media_info=True)

    # if result.has_more == True:

    # Iterate over metadata contents
    for item in result.entries:

        # Skip deleted files and folders
        if (isinstance(item, dropbox.files.DeletedMetadata) or
            isinstance(item, dropbox.files.FolderMetadata)):
            continue

        # print item

        # Item metadata
        # logger.debug('File metadata: ' + str(item))

        # Download log file
        # get_log_file()

        # Get source path and file name
        source_path = item.path_lower
        file_name = os.path.basename(source_path)
        _, extension = os.path.splitext(source_path)
        print file_name

        # Find out if there's media info available
        if (item.media_info is not None and
        not item.media_info.is_pending()):
            print item.media_info.get_metadata().time_taken
            year, month = parse_time_taken(item)
            print year, month
        else:
            # Try parsing year, month and extension from file name
            year, month, extension = get_info_from_file_name(source_path)
            logger.debug('Year and month from file name: '
                         + year + ' ' + month)
            logger.debug('File extension: ' + extension)

        # Validate file extension
        if extension in cfg.pics_types:
            is_photo = True
            print "photo"
        elif extension in cfg.vids_types:
            is_video = True
            print "video"

        """
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
        """

        # Upload log
        # upload_log_file()

    # Update cursor
    # cursor = result['cursor']

    # Repeat only if there's more to do
    has_more = result.has_more
