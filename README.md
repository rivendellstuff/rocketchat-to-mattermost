# rocketChat-To-MatterMost
 convert posts from rocketChattoMattermost (so far)
 - attachments are supported if "filesystem type"
 - docker version supported
 - [Github Repo](https://github.com/rivendellstuff/rocketchat)

# description
- RocketChat stores data in MongoDB
- Mattermost stores data in SQL
- RocketChat stores messages by combining the entityIds of the participants as a single large string in "rid" (not sure how it specifies which ID to put first)
- Mattermost stores all messages as "posts" in a "channel" between participants
- Use Compass (or however) to export your rocketchat_message collection from MongoDB
- Use this script to reformat the data to JSONL output
- Use Mattermost import to import the messages
- Should handle multiple chatters but only tested with 2 users in a conversation with each other

# requirements
- Python3
- pandas ( pip install pandas )

# usage
- not specifying attachmentRootDir will ignore all attachments
- not specifying dockerAttachmentRootDir will use attachmentRootDir as the source of truth for attachment locations
- fullPathToCsvFile not specified will look for "data.csv" in same folder by default
- mode(include|exclude) takes a literal string of "include" or "exclude". It's whether or not to include JUST the u._id specified in the CLI argument or to use all rows EXCEPT ones where those u._id match (i.e. all messages to one mattermost room except)
- generally use "include" if migrating users private conversations

```
mattermost_import.py "teamName" "channelName" "[listOfUserIDsSeparateByCommas]" "mode(include|exclude) of userIds prior" "optional:attachmentRootDir" "optional:dockerAttachmentRootDir" "optional:fullPathToCsvFile"
```

## attachments
- assumes all attachments are in FileSytem (not database)
- uses file.name from export to get attachment names
- uses attachmentRootDir to get attachment root dir (where all attachments are)
- will verify the file is valid (or its skipped) using this path attachmentRootDir 
- IF using DOCKER, specify the docker mounted path to the same location. The validation happens using the attachmentRootDir but the import needs to happen from the Docker accessible path (if running THIS script on the Mattermost container then can treat it as a non-docker and just use attachmentRootDir)
- if valid, renames the **original file in place** to its real name (dont run this on your original attachments folder, use a copy!)
> eg: 
```
    file._id = 64bb9a1d81807b81b5ff84ef
    attachmentRootDir = /volume1/chat/rocketchat_uploads/
    file.name = Clipboard - July 22, 2023 1:50 AM.png
    attachment = "/volume1/chat/rocketchat_uploads/Clipboard - July 22, 2023 1:50 AM.png"
```
> attachment is what will get migrated into mattermost. Image processing if images will happen naturally

## directions
### notes
- users in Mattermost should already exist
- the conversation you're importing between the users needs to have a "room name" already made in Mattermost i.e.: ```simply start a conversation in Mattermost between the users you're about to import (if not done already) ```
- get the "channel name" from Mattermost. (I used pgAdmin and just looked at the posts between the two users to see the channel id and looked up the channel in the channel's table to get the channel name (not the display name))
- similar to the prev step, also get the "team name" (not the displayname) - I only have one team
- you do NOT need to manually edit the RC exported csv in anyway!! The entire file can be used multiple times with this script by specifying different users conversations

### verify u._id
- do the below instructions for EACH conversation you'd like to migrate - use the u._id fields in the CSV to determine the accurate conversations
- if you put just **one** u._id then that one user's ALL conversations with everyone in RocketChat will end up as conversations with the single wrong person as it will put all messages to and from that user into the specified Mattermost channel (see line 10 of this readme)
- ensure the items you use from the u._id of the RC export are the u._ids of the exact users involved in the conversation you're importing in this run
- this script will skip any rows where the RocketChat "RID" field doesn't  contain all of the u._uid entered (in cases where there are more than 2 ppl in a conversation it may be a "room" which hasnt been tested yet so keep that in mind when looking at which u._id you want to use or if its just a single room to room migration)

### prep data for import
1. Use Compass (or however) to export your rocketchat_message collection from MongoDB into CSV format (all fields EXCEPT one of the reactions (will give an error if you try to export anyway))
2. CSV should have the following fields (tho not all are required)
``` 
_id	_updatedAt	attachments	channels	editedAt	editedBy._id	editedBy.username	file._id	file.name	file.type	groupable	mentions	msg	reactions	reactions.:thumbsup:.usernames	rid t	ts	u._id	u.name	u.username	urls
```
3. Open the CSV and find the two users whose conversation you want to import
4. Note both users: u._id
5. If also migrating attachments: you will want to make a COPY of your rocketchat attachments folder. This will be permanent copy for legacy attachments in mattermost so put it somehwere that makes sense and is accessible to this script (and the docker image if running Mattermost in Docker) e.g: ```cp -rf /volume1/chat/rocketchat_uploads /volume1/chat/mattermost_uploads/legacy```
6. Create your posts.json file: (note: "/uploads/legacy" is optional for attchments as I'm using Mattermost in Docker I need to provide the docker OS the link to the same place from its perspective) where:
>> Dwqweq12322311312h is the u._id of username 'john' (from RC exported CSV)

>> b3swq2334eefs3z is the u._id of username 'jane' (from RC exported CSV)

>> this will get the only the entire conversation from the CSV between John and Jane

```
python3 mattermost_import.py "mattermostteamnamealllowercasewithnospaces" "gw3t6wqweqweqfiqwqeqeqeqweqwar__gxyweeewqeqeqepgnqweqeqwe" "['Dwqweq12322311312h', 'b3swq2334eefs3z']" "include" "/mnt/server/chat/mattermost-uploads/legacy" "/uploads/legacy" "data.csv"
```
```
for comparison:

python3 mattermost_import.py "teamname" "channelname" "[listOfUserIDsSeparateByCommasOrOneRoomIdMaybe]" "mode(include|exclude) of userIds prior" "optional:attachmentRootDir" "optional:dockerAttachmentRootDir" "optional:fullPathToCsvFile"
```

7. After processing (approx 5-10 mins for 5000 attachments totalling 15gig on AMD Ryzen7) you'll end up with a file called: ```posts.json```
> eg: 

```
{"type": "version", "version": 1}
{"type": "post", "post": {"team": "mattermostteamnamealllowercasewithnospaces", "channel": "gw3t6wqweqweqfiqwqeqeqeqweqwar__gxyweeewqeqeqepgnqweqeqwe", "user": "jane", "message": "", "create_at": 1613959241344, "attachments": []}}
{"type": "post", "post": {"team": "mattermostteamnamealllowercasewithnospaces", "channel": "gw3t6wqweqweqfiqwqeqeqeqweqwar__gxyweeewqeqeqepgnqweqeqwe", "user": "jane", "message": "yes, the mainentance part just stuck somehow", "create_at": 1613959228371, "attachments": []}}
{"type": "post", "post": {"team": "mattermostteamnamealllowercasewithnospaces", "channel": "gw3t6wqweqweqfiqwqeqeqeqweqwar__gxyweeewqeqeqepgnqweqeqwe", "user": "john", "message": "maybe do that and ill just order something small for now", "create_at": 1689891765932, "attachments": []}}
{"type": "post", "post": {"team": "mattermostteamnamealllowercasewithnospaces", "channel": "gw3t6wqweqweqfiqwqeqeqeqweqwar__gxyweeewqeqeqepgnqweqeqwe", "user": "john", "message": "", "create_at": 1690016286016, "attachments": [{"path": "/uploads/legacy/Clipboard - July 22, 2023 1:50 AM.png", "id": "64bb9a1d81807b81b5ff84ef"}]}}
```

### import into Mattermost
1. Use Mattermost Import CLI to import the posts: ```mattermost import bulk posts.json --validate```
2. If there are no errors in that output: ```mattermost import bulk posts.json --apply``` 
3. For 67000 messages (inc attachments mentioned above) this took about 15 mins running directly on the docker container
4. Once this is complete the conversation should have been imported
#### notes
- I ran the mattermost import on the docker container directly via portainer
- I copied my rocketchat attachments to a "legacy" folder in mattermost-uploads folder eg from docker-compose: ``` (/mnt/server/chat/mattermost-uploads:/uploads) ```
- I ran THIS script on the Docker host
- I copied the posts.json over to ```/mnt/server/chat/mattermost-uploads/config/migration which is mapped to my Docker container ```
- I had Bleve enabled initially and the import appeared to hang on line 1 forever. I disabled Bleve and it worked fine after that (not sure why), have not tried enabling it since as I'm still setting up the rest of Mattermost
- During the import you will see many debug messages about "failing to get image orientation" etc... as long as the import doesn't halt, there shouldnt be any issues
- Consider this VERY much NOT widely tested and use at your own risk
- I migrated 2.5 years worth of data and attachments for 15 users in about an hour total using the above method