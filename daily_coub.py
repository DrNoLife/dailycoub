from nbformat import write
from numpy import add
import tweepy
import json
import subprocess
import os
import random
import time

FOLDERS_USED_BEFORE = 'Q:/Repositories/dailycoub/folders_used.txt'
PATH_TO_SETTINGS = "Q:/Repositories/dailycoub/bot_settings.json"
PATH_TO_COUB_ARCHIVE = "Q:/Videos/Coub/all my likes/Anime"
PATH_TO_LAST_UPLOAD_FILE = "Q:/Repositories/dailycoub/last_upload_time.txt"
FOLDER_FOR_ERROR_LOG = "C:/Users/lazyt/Desktop"

# I need to make sure I call this in all try catch statements, so the error gets yeeted to my desktop.
def write_error_log(error):

    error_log_path = f"{FOLDER_FOR_ERROR_LOG}/DAILY_COUB_ERROR_LOG.txt"

    if not os.path.exists(error_log_path):
        with open(error_log_path, mode='w', encoding="utf8"): pass

    with open(error_log_path, 'a', encoding="utf8") as f:
        f.write(error)

def get_bot_settings():
    with open(PATH_TO_SETTINGS, 'r') as settings:
        return json.loads(settings.read())

def reencode_video(video_path, use_speeeeedy_preset = False):
    if video_path != None:
        print('Encoding video.')
        #ffmpeg_command = f"ffmpeg -i \"{video_path}\" -c:v libx264 -crf 20 -preset slow -vf format=yuv420p -loglevel quiet -c:a aac -movflags +faststart output.mp4"

        if use_speeeeedy_preset:
            ffmpeg_command = f"ffmpeg -i \"{video_path}\" -c:v libx264 -crf 20 -preset ultrafast -vf format=yuv420p -loglevel quiet -c:a aac -movflags +faststart output.mp4"
        else:
            ffmpeg_command = f"ffmpeg -i \"{video_path}\" -c:v libx264 -crf 20 -preset slow -vf format=yuv420p -loglevel quiet -t 30 -c:a aac -movflags +faststart output.mp4"
        
        subprocess.run(ffmpeg_command)
        print("Finished encoding.")
    else:
        error = "Failed to re-encode video."
        write_error_log(error)
        raise(error)

def clear_the_folder():
    try:
        if os.path.exists('output.mp4'):
            os.remove('output.mp4')
    except:
        error = 'Failed to delete output.mp4'
        write_error_log(error)
        raise(error)

def check_for_duplicate_upload(folder_path):

    # The text file containing our list.
    textfile = FOLDERS_USED_BEFORE

    # Create textfile if it doesn't exist.
    if not os.path.exists(textfile):
        open(textfile, 'w+', encoding="utf-8").close()

    # Open local file, containing list of folders we've used before.
    with open(textfile, 'r', encoding="utf-8") as f:
        lines = f.readlines()

        # Check all entries - if the folder path is in, we return a False, so we can find a new one.
        for line in lines:
            if folder_path == line.rstrip():
                return False

    return True
 
def get_random_folder():
    try:
        path_to_main_folder = PATH_TO_COUB_ARCHIVE
        all_sub_folders = os.listdir(path_to_main_folder)

        # Get the a random folder from the list of possible folders.
        wanted_folder = all_sub_folders[random.randint(0, len(all_sub_folders) - 1)]

        fullpath = f"{path_to_main_folder}/{wanted_folder}"

        # Check for duplicate.
        if not check_for_duplicate_upload(fullpath):
            fullpath = get_random_folder()
            
        return fullpath
            
    except Exception as e:
        error = f'Failed to get a random folder.\n{str(e)}'
        write_error_log(error)

def get_coub(folder_path):
    try:
        coubs = []

        for file in os.listdir(folder_path):
            if file.endswith(".mp4"):
                coubs.append(file)

        return coubs
    except Exception as e:
        error = f"Failed to get coub from folder.\n{str(e)}"
        write_error_log(error)
        raise(error)
  
def add_coub_to_duplicate_list(folder_path):
    with open(FOLDERS_USED_BEFORE, 'a', encoding="utf-8") as f:
        f.write(folder_path + "\n")

# This encodes, and tweets the coub the short version of the coub.
def tweet_short_coub(coub_path, coub_folder):
    try:
        # Encode media - this also gets the video into the projects folder.
        reencode_video(coub_path)

        print("Tweeting the short version.")

        # Get meta data regarding this coub.
        with open(f'{coub_folder}/summary.txt', 'r', encoding="utf8") as f:
            lines = f.readlines()
            title = lines[0].split('\t')[1]

        # Upload the media to Twitter.
        upload_result = api.media_upload('output.mp4')
        response = api.update_status(status = title, media_ids=[upload_result.media_id_string])

        print("Done.")

        # Deletes the output.mp4 
        clear_the_folder()

        # Get the id of the tweet
        json_object = json.loads(json.dumps(response._json))

        return json_object['id']
    except Exception as e:
        error = f"Failed to tweet the video.\n{str(e)}"
        write_error_log(error)

# THIS DOES NOT WORK. Because Twitter wants "large" files to be handles async, but Tweepy does not support this.
# I might rewrite this in C#.
def tweet_long_version(tweet_id, coub_path, coub_folder):

    # Encode the long version.
    reencode_video(coub_path, use_speeeeedy_preset=True)

    # Get meta data regarding this coub.
    with open(f'{coub_folder}/summary.txt', 'r', encoding="utf8") as f:
        lines = f.readlines()
        title = lines[0]

    print("Tweeting the long version.")

    # Upload the long version as a reply.
    upload_result = api.media_upload('output.mp4')

    print(f"\n\n\n{upload_result}")

    response = api.update_status(status = title, media_ids=[upload_result.media_id_string], in_reply_to_status_id = tweet_id)

    print("Done.")

    # Clear the folder.
    clear_the_folder()

# Used to making sure we only upload one coub a day.
def more_than_24_hours_ago_since_last_upload():

    # Check if the file exists.
    if not os.path.exists(PATH_TO_LAST_UPLOAD_FILE):
        with open(PATH_TO_LAST_UPLOAD_FILE, mode='w', encoding="utf8"): pass

    with open(PATH_TO_LAST_UPLOAD_FILE, 'r', encoding="utf-8") as f:
        last_upload_time = f.read()

    if last_upload_time == None or last_upload_time == '':
        return True

    # Check if last upload, plus a 20 hours worth of seconds, is less or equal to current time.
    if float(last_upload_time) + 72000 <= time.time():
        return True
    else:
        return False

def update_last_upload_timestamp():
    current_time = time.localtime()

    # Check if the file exists.
    if not os.path.exists(PATH_TO_LAST_UPLOAD_FILE):
        with open(PATH_TO_LAST_UPLOAD_FILE, mode='w', encoding="utf8"): pass

    with open(PATH_TO_LAST_UPLOAD_FILE, 'w', encoding="utf-8") as f:
        f.write(str(time.time()))

settings = get_bot_settings()

# Tweepy setup
auth = tweepy.OAuthHandler(settings['API_Key'], settings['API_Key_Secret'])
auth.set_access_token(settings['Access_Token'], settings['Access_Token_Secret'])
api = tweepy.API(auth)

try:

    # Check if enough time has passed for a new upload.
    if more_than_24_hours_ago_since_last_upload():
        coub_folder = get_random_folder()
        coubs = get_coub(coub_folder)

        # Upload the short version.
        tweet_id = tweet_short_coub(coub_path = f"{coub_folder}/{coubs[0]}", coub_folder = coub_folder)

        # Reply to short version, with long version.
        #tweet_long_version(tweet_id = tweet_id, coub_path = f"{coub_folder}/{coubs[1]}", coub_folder = coub_folder)

        # Handle cleaning touches.
        update_last_upload_timestamp()
        add_coub_to_duplicate_list(coub_folder)
    else:
        print("Not enough time.")
    

except Exception as e:
    error = str(e)
    write_error_log(error)
    print(error)