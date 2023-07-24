import pandas as pd
import json
import sys
from datetime import datetime
from dateutil import parser as dateparser
import ast
import os

def main():
    if len(sys.argv) < 6 or len(sys.argv) > 9:
        print("Usage: mattermost_import.py 'teamName' 'channelName' 'listOfUserIDs' 'mode' 'optional:rootDir' 'optional:dockerRootDir' 'optional:csvFilePath' 'optional:roomName'")
        return

    team_name = sys.argv[1]
    channel_name = sys.argv[2]
    user_ids = ast.literal_eval(sys.argv[3])  # Convert string of list to actual list
    mode = sys.argv[4].lower()  # Mode can be 'exclude' or 'include'
    root_dir = sys.argv[5] if len(sys.argv) >= 6 else None  # Root directory for attachments
    docker_dir = sys.argv[6] if len(sys.argv) >= 7 else None  # Docker root directory for attachments
    csv_file = sys.argv[7] if len(sys.argv) >= 8 else 'data.csv'  # CSV file path
    roomId = sys.argv[8] if len(sys.argv) == 9 else None  # Room Id (rid)

    if mode != 'exclude' and mode != 'include':
        print("Invalid mode. Mode can be 'exclude' or 'include'.")
        return

    df = pd.read_csv(csv_file)

    with open('posts.json', 'w') as json_file:
        # Write the version line
        json_file.write('{"type": "version", "version": 1}\n')

        for _, row in df.iterrows():
            if pd.isnull(row['u.username']) or pd.isnull(row['u.name']) or pd.isnull(row['u._id']):
                continue

            user_id_matches = row['u._id'] in user_ids

            if roomId:
                if row['rid'] != roomId:
                    continue
            else:
                if (mode == 'exclude' and user_id_matches) or (mode == 'include' and not user_id_matches):
                    continue

                if not all(uid in row['rid'] for uid in user_ids):
                    continue

            timestamp = dateparser.parse(row['ts']).timestamp() * 1000  # Convert timestamp to epoch in milliseconds

            # Replace 'NaN' with empty string
            message = '' if pd.isnull(row['msg']) else row['msg']

            post = {
                'type': 'post',
                'post': {
                    'team': team_name,
                    'channel': channel_name,
                    'user': row['u.username'].lower(),  # Ensure username is lowercase
                    'message': message,
                    'create_at': int(timestamp),
                    'attachments': []
                }
            }

            if root_dir and not pd.isnull(row['file._id']):
                # Add a trailing slash to the root directory if it's not there
                if root_dir[-1] != '/':
                    root_dir += '/'
                if docker_dir[-1] != '/':
                    docker_dir += '/'                    

                file_path = root_dir + row['file._id']

                # Only include if the file exists
                if os.path.isfile(file_path):
                    # Rename the file in place to its original name
                    new_file_path = root_dir + row['file.name']
                    os.rename(file_path, new_file_path)
                    
                    attachment_path = (docker_dir if docker_dir else root_dir) + row['file.name']
                    attachment = {
                        'path': attachment_path,
                        'id': row['file._id']
                    }

                    # Append the attachment to the 'attachments' list of the 'post'
                    post['post']['attachments'].append(attachment)

            json_file.write(json.dumps(post) + '\n')

if __name__ == "__main__":
    main()
