from datetime import datetime
from blogBot import YoutubePy, GrammerPy,BloggerPy
import sqlite3
import ast

BLOG_ID = "<YOUR BLOG ID>"
YOUTUBE_ID = '<YOUR YOUTUBE ID>'
con = sqlite3.connect('blogbot.db')

# You can add new channels to the list as well
channels = [
    {
        "channel_name": "Abhijit Chavda",
        "channel_tag": "abhijitchavda",
        "channel_id": "UC2bBsPXFWZWiBmkRiNlz8vg",
    }
]

yt = YoutubePy(YOUTUBE_ID)
gm = GrammerPy()
bg = BloggerPy(BLOG_ID)

def prepareVideoIds(daysOldVideo=2):

    # Create DB if not exists
    con.execute('''CREATE TABLE IF NOT EXISTS blogs (blog_id text, video_id text,status text, title text, published_at text, channel_name text, channel_tag text, channel_id text, thumbnail text, reason text);''')

    # Get all the video ids from the channels
    for channel in channels:
        print("\n")
        print("||===========================================================>")
        print(f"|| Getting videos from channel {channel['channel_name']}")
        print("||===========================================================>\n")
        channel_videos = yt.getChannelVideoList(channel['channel_id'],prevDateRange=daysOldVideo)
        for video in channel_videos:
            video_id = video['id']
            channel_name = channel['channel_name']
            channel_tag = channel['channel_tag']
            channel_id = channel['channel_id']

            # Get video meta data from youtube
            videoMeta = yt.getYoutubeVideo(video_id)
            if videoMeta['status'] == 'Accepted':
                video_title = videoMeta['title']
                video_tags = videoMeta['tags'] + [channel_tag]
                thumbnail = videoMeta['thumbnail']
            else:
                print(f"===> Desired video not found.\n===> Possible reasons: \n \t1. No video uploaded in past {daysOldVideo} days. \n \t2. Video duration is more than 10mins.\n")
                continue

            checkIfExists = con.execute(f"SELECT video_id FROM blogs WHERE video_id = '{video_id}'").fetchone()
            if checkIfExists != None:
                print(f"===> Video '{video_id}' already exists in the DB")
                continue

            con.execute("INSERT INTO blogs (blog_id, video_id, status, title, published_at, channel_name, channel_tag, channel_id,thumbnail,reason) VALUES (?,?,?,?,?,?,?,?,?,?)", ('', video_id, 'pending', video_title, datetime.now(), channel_name, str(video_tags), channel_id, thumbnail,''))
            con.commit()
            print(f"===> Video '{video_id}' added to the DB")


def createTheme(title, content, thumbnail, videoID):
    blogThumbnail = f'''<div class="separator" style="clear: both; text-align: center;"><a href="{thumbnail}" imageanchor="1" style="margin-left: 1em; margin-right: 1em;"><img border="0" data-original-height="450" data-original-width="800" height="450" src="{thumbnail}" width="800" /></a></div><br /><p><br /></p>'''

    iframe = f'''<div class="embed-responsive embed-responsive-16by9"><p align="center"><iframe class="embed-responsive-item" width="380vw" height="400vh" src="https://www.youtube.com/embed/{videoID}" title="{title}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe></p></div>'''

    disclaimer = '''<br><blockquote style="background-color:#FFC11A;"><i>A bot has generated this blog entry based on the linked YouTube video. There are no intentions to steal the information or research from the original owner. This blog post is exclusively for "Educational Purposes Only," and I have no intention of earning, selling, or monetizing it. The main objective of this site is to share knowledge to as many people as possible. I strongly advise people to watch the original video for a better understanding.</i></blockquote><br>'''

    mainContent = blogThumbnail + '<br>' + iframe + '<br>' + disclaimer + '<br>' + content

    return mainContent


def createBlog():
    pendingVideos = con.execute('''SELECT * FROM blogs WHERE status = "pending";''').fetchall()
    for video in pendingVideos:
        print("\n")
        print("||===========================================================>")
        print(f"|| Creating blog from video for {video[5]}")
        print("||===========================================================>\n")

        # Get video meta data from youtube
        video_id = video[1]
        tags = ast.literal_eval(video[6])

        # TODO: Keep tags to a minimum of 5 and add channel tag at last
        channel_tag = tags[-1]
        thumbnail = video[8]
        title = video[3]

        # Get Transcription
        print(f"===> Getting transcription from youtube")
        transcript = yt.getVideoTranscript(video_id)
        if transcript == 'No transcript found':
            con.execute(f"UPDATE blogs SET status = 'rejected', reason = 'No transcript found' WHERE video_id = '{video_id}'")
            print(f"===> Failed: No transcript found for video '{video_id}'")
            print(f"===> Status and Reason updated in the DB")
            continue
        elif transcript == "Subtitles are disabled for this video":
            con.execute(f"UPDATE blogs SET status = 'rejected', reason = 'Subtitles are disabled for this video' WHERE video_id = '{video_id}'")
            print(f"===> Failed: Subtitles are disabled for this video '{video_id}'")
            print(f"===> Status and Reason updated in the DB")
            continue
            
        # Get Grammer
        print(f"===> Correcting grammar")
        filteredTranscript = gm.basicGrammerFilter(transcript)
        formatedTranscript = gm.formatContentIntoParagraph(filteredTranscript)

        # Create Blog
        print(f"===> Creating blog")
        blogContent = createTheme(title, formatedTranscript, thumbnail, video_id)

        print(f"===> Publishing blog")
        result = bg.postToBlog(title, blogContent,isDraft=False, tags=tags)

        if result == "Error: The tags are too long.":
            newTags = tags[:5]
            newTags = newTags.append(channel_tag[0])
            result = bg.postToBlog(title, blogContent,isDraft=False, tags=newTags)
            if "Error" not in result:
                print(f"===> Success: Blog published")
                con.execute(f"UPDATE blogs SET status = 'published', blog_id = '{result['id']}' WHERE video_id = '{video_id}'")
                con.commit()
            else:
                print(f"===> Failed: {result}")
                print(f"===> Status and Reason updated in the DB")
                con.execute(f"UPDATE blogs SET status = 'rejected', reason = '{result}' WHERE video_id = '{video_id}'")
                con.commit()
        elif "Error" in result:
            print(f"===> Failed: {result}")
            print(f"===> Status and Reason updated in the DB")
            con.execute(f"UPDATE blogs SET status = 'rejected', reason = '{result}' WHERE video_id = '{video_id}'")
            con.commit()
        else:
            print(f"===> Success: Blog published")
            con.execute(f"UPDATE blogs SET status = 'published', blog_id = '{result['id']}' WHERE video_id = '{video_id}'")
            con.commit()


if __name__ == "__main__":
    # Change the 'daysOldVideo' parameter to the number of days you want to check for new videos
    prepareVideoIds(daysOldVideo=2)
    createBlog()


