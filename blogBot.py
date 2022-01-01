import os
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import requests
from requests.structures import CaseInsensitiveDict
import random
import nltk
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
import language_tool_python
from datetime import datetime, timedelta
import re

class BloggerPy():
    def __init__(self,blogID):
        """
        Initializes the BlogBot class.

        Parameters:
            blogID (str): The ID of the blog to be used.

        """
        print("BlogBot is running")

        try:
            self.blogID = blogID

            # Authenticate Blogger
            SCOPES = ['https://www.googleapis.com/auth/blogger']
            
            # The file token.pickle stores the user's access and refresh tokens, and is
            # created automatically when the authorization flow completes for the first
            # time.
            creds = None
            if os.path.exists('blogger_token.pickle'):
                with open('blogger_token.pickle', 'rb') as token:
                    creds = pickle.load(token)
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        'credentials.json', SCOPES)
                    creds = flow.run_local_server(port=0)
                
                # Save the credentials for the next run
                with open('blogger_token.pickle', 'wb') as token:
                    pickle.dump(creds, token)
            self.blogService = build('blogger', 'v3', credentials=creds)
        
        except Exception as e:
            print(e)

    def getBlogTitles(self, maxResults=10):
        """
        Gets the titles of the blogs in the account.

        Parameters:
            maxResults (int): The maximum number of results to return.

        Returns:
            titles (list): A list of the titles and ids of the blogs in the account.
        """
        blogTitles = []
        try:
            getPosts = self.blogService.posts()
            posts = getPosts.list(blogId=self.blogID, maxResults=maxResults).execute()
            allPosts = posts['items']
            for post in allPosts:
                blogTitles.append({'title': post['title'], 'id': post['id']})
            return blogTitles
        except Exception as e:
            print(e)
        
    
    def postToBlog(self, title, content, isDraft=True ,tags=None):
        """
        Posts a blog to the account.

        Parameters:
            title (str): The title of the blog.
            content (str): The content of the blog.
            isDraft (bool): Whether the blog is a draft or not.
            tags (list): A list of tags to be added to the blog.

        Returns:
            post (dict): The blog post.
        """

        try:
            post = {}
            post = self.blogService.posts().insert(blogId=self.blogID, body={
                    'title': title,
                    'content': content,
                    'labels': tags
                }, isDraft=isDraft, fetchImages=True).execute()
            return post
        except Exception as e:
            if "labels must be at most 200 characters." in str(e):
                return "Error: The tags are too long."
            else:
                return "Error: " + str(e)

class YoutubePy():
    def __init__(self,key):
        self.ytService = build('youtube', 'v3', developerKey=key)

    def getChannelVideoList(self,channelID,prevDateRange=7):
        """
        Gets the video list of a channel from specified previous days.

        Parameters:
            channelID (str): The channel ID.
            prevDateRange (int): The number of days to get the videos from.

        Returns:
            videoList (list): A list of the videos in the channel.

        """

        date = datetime.now() - timedelta(prevDateRange)
        videos = []
        nextPageToken = None
        while True:
            channelVideos = self.ytService.search().list(
            part="id",
            channelId=channelID,
            publishedAfter=date.strftime('%Y-%m-%dT%H:%M:%SZ'),
            pageToken=nextPageToken,
            ).execute()
            for video in channelVideos['items']:
                # print(video)
                videos.append({'id': video['id']['videoId']})
                nextPageToken = channelVideos.get('nextPageToken')
            
            nextPageToken = channelVideos.get('nextPageToken')
        
            if not nextPageToken:
                break
        return videos
    
    def listTranscripts(self, videoId):
        """
        Lists the transcripts of a video.

        Parameters:
            videoId (str): The video ID.

        Returns:
            transcripts (list): A list of the transcripts of the video.

        """

        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(videoId)
        except Exception:
            print("No transcript found")

        available_lang = []
        for tran in transcript_list:
            if 'en' in tran.language_code and tran.is_generated == True:
                available_lang.append(tran.language_code)
            else:
                return "No English Transcript"
        return available_lang

    def getVideoTranscript(self,videoId):
        """
        Gets the transcript of a youtube video.

        Parameters:
            videoId (str): The id of the video.

        Returns:
            transcript (str): The transcript of the video.
        """
        
        try:
            story = ''''''

            # retrieve the available transcripts
            transcript_list = YouTubeTranscriptApi.list_transcripts(videoId)

            available_langs = self.listTranscripts(videoId)
            

            if available_langs != [] and available_langs != "No English Transcript":
                availableTranscripts = str(transcript_list.find_transcript(available_langs))
                if "auto-generated" in availableTranscripts:
                    transcript_list = transcript_list.find_generated_transcript(available_langs)
                elif "auto-generated" not in availableTranscripts:
                    transcript_list = transcript_list.find_manually_created_transcript(available_langs)
                else:
                    transcript_list = "No transcript found"
                    return transcript_list
            else:
                transcript_list = "No transcript found"
                return transcript_list

            # if available_langs != []:
            #     transcript_list = transcript_list.find_manually_created_transcript(available_langs)
            # elif 'auto-generated' in availableTranscripts:
            #     transcript_list = transcript_list.find_generated_transcript(available_langs)
            # else:
            #     transcript = transcript_list
            
            transcript = transcript_list.fetch()
            for i  in transcript:
                story += i['text']
                story += ' '

            return story
        except Exception as e:
            # print(e)
            if "Subtitles are disabled for this video" in str(e):
                return "Subtitles are disabled for this video"
            else:
                return 'No transcript found'


    def convertDuration(self, duration):
        """
        Converts a Youtube duration format to a mins.

        Parameters:
            duration (str): The duration to be converted.

        Returns:
            duration (int): The converted duration.
        """

        try:
            regex = r"(PT)([0-9]|[1-9][0-9])(M)"
            matches = re.search(regex, duration)
            if matches:
                duration = matches.group(2)
                duration = int(duration)
            return duration
        except Exception as e:
            print(e)


    def getYoutubeVideo(self,videoID):
        """
        Gets the video of a youtube video.

        Parameters:
            videoID (str): The id of the video.

        Returns:
            video (dict): Title, thumbnail and tags of the video.

        """

        try:
            videoMetaData = {}
            videoData = self.ytService.videos().list(part='snippet,contentDetails', id=videoID).execute()

            
            videoDuration = videoData['items'][0]['contentDetails']['duration']
            if videoDuration != "P0D" and "H" not in videoDuration:
                videoDuration = self.convertDuration(videoDuration)
            elif videoDuration == "P0D" or "H" in videoDuration:
                videoDuration = 20

            if videoDuration > 10:
                videoMetaData['status'] = "Rejected"
                videoMetaData['reason'] = "Duration is greater than 10 mins"
                videoMetaData['thumbnail'] = ''
                videoMetaData['tags'] = []
                videoMetaData['videoID'] = videoID
                return videoMetaData

            videoSnippet = videoData["items"][0]['snippet']

            videoMetaData['title'] = videoSnippet['title']

            availableThumbnail = videoSnippet['thumbnails'].keys()
        
            if 'maxres' in availableThumbnail:
                thumbnail = videoSnippet['thumbnails']['maxres']['url']
            
            elif 'standard' in availableThumbnail:
                thumbnail = videoSnippet['thumbnails']['standard']['url']
            
            elif 'high' in availableThumbnail:
                thumbnail = videoSnippet['thumbnails']['high']['url']
            
            elif 'medium' in availableThumbnail:
                thumbnail = videoSnippet['thumbnails']['medium']['url']
            
            else:
                thumbnail = videoSnippet['thumbnails']['default']['url']

            videoMetaData['status'] = "Accepted"
            videoMetaData['thumbnail'] = thumbnail

            if 'tags' in videoSnippet.keys():
                videoMetaData['tags'] = videoSnippet['tags'] 
            else:
                videoMetaData['tags'] = ['blogBot']
            videoMetaData['videoID'] = videoID

            return videoMetaData
        except Exception as e:
            print(e)
            # pass

    def getYoutubePlaylist(self, playlistId):
        """
        Gets the videos of a youtube playlist.

        Parameters:
            playlistId (str): The id of the playlist.
        
        Returns:
            videos (list): A list of the title, thumbnail and tags of the videos in playlist.

        """

        try:
            nextPageToken = None
            videoList = []

            while True:
                # Retrieve youtube video results
                pl_request = self.ytService.playlistItems().list(
                    part='snippet',
                    playlistId=playlistId,
                    maxResults=99,
                    pageToken=nextPageToken
                )
                pl_response = pl_request.execute()

                # Iterate through all response and get video description
                for item in pl_response['items']:

                    try:
                        YouTubeTranscriptApi.get_transcript(item['snippet']['resourceId']['videoId'])
                        availableThumbnail = item['snippet']['thumbnails'].keys()
            
                        if 'maxres' in availableThumbnail:
                            thumbnail = item['snippet']['thumbnails']['maxres']['url']
                        
                        elif 'standard' in availableThumbnail:
                            thumbnail = item['snippet']['thumbnails']['standard']['url']
                        
                        elif 'high' in availableThumbnail:
                            thumbnail = item['snippet']['thumbnails']['high']['url']
                        
                        elif 'medium' in availableThumbnail:
                            thumbnail = item['snippet']['thumbnails']['medium']['url']
                        
                        else:
                            thumbnail = item['snippet']['thumbnails']['default']['url']

                        videoObject = {
                            'title': item['snippet']['title'],
                            'thumbnail': thumbnail,
                            'videoID': item['snippet']['resourceId']['videoId']
                        }
                        videoList.append(videoObject)
                    except:
                        continue

                nextPageToken = pl_response.get('nextPageToken')
        
                if not nextPageToken:
                    break
                
            return videoList
        except Exception as e:
            print(e)

class GrammerPy():
    def basicGrammerFilter(self, text):
        """
        Filters out basic grammer from text.

        Parameters:
            text (str): The text to be filtered.
        
        Returns:
            text (str): The filtered text.

        """

        self.gtool = language_tool_python.LanguageTool('en-US')

        try:
            transcription = self.gtool.correct(text)
        except UnicodeEncodeError:
            transcription = self.gtool.correct(text.encode('utf-8'))
        
        return transcription

    def formatContentIntoParagraph(self, text, formatHTML=True):
        """
        Breaks text into paragraphs.

        Parameters:
            text (str): The text to be broken into paragraphs.
            formatHTML (bool): Paragraphs are wraped into simple <div> tags.
        
        Returns:
            text (str): The text broken into paragraphs.

        """

        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')

        url = "http://bark.phon.ioc.ee/punctuator"
        headers = CaseInsensitiveDict()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        data = f"text={text}"

        try:
            resp = requests.post(url, headers=headers, data=data)
        except UnicodeEncodeError:
            resp = requests.post(url, headers=headers, data=data.encode('utf-8'))
        cleanText = resp.text

        try:
            sentenceList = nltk.tokenize.sent_tokenize(cleanText)
            paragraph = """"""
            sentenceLength = 0
            for sentence in sentenceList:
                sentenceLength += 1
                paragraph += sentence + ' '
                if sentenceLength > random.randint(4,6):
                    if formatHTML:
                        paragraph = '<div>' + paragraph + '</div>' + '<br>'
                    else:
                        paragraph = paragraph
                    sentenceLength = 0
            return paragraph
        except Exception as e:
            print(e)
