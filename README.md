# BlogBot - Convert Youtube Videos To Blogs

BlogBot is a Python script that create blogs from YouTube videos.


## Installation

Use requirements.txt file to install required packages.

```bash
pip install -r requirements.txt
```

## Usage

Open **bot.py** and add Blogger and Youtube API ID's

```python
BLOG_ID = "<YOUR BLOG ID>"
YOUTUBE_ID = '<YOUR YOUTUBE KEY/ID>'
```

**Blogger ID** can be obtained by going to the dashboard of blogger and check url:

Example Image:

![image](https://user-images.githubusercontent.com/57774379/147849222-817b6c0d-212f-4786-8ca5-a4c76fdf2bd4.png)


**Youtube API Key** follow [this](https://blog.hubspot.com/website/how-to-get-youtube-api-key) tutorial to get api key or follow the [official](https://developers.google.com/youtube/v3/getting-started) tutorial

Along with all this we also need to setup OAuth for Blogger.
Follow [this](https://www.topzenith.com/2020/05/working-with-blogger-api-v3-using-python-for-beginners-via-Oauth-2.0.html) tutorial to setup OAuth.

If everything works well. You should get **'client_secret_<some_weird_numbers>.json'** 

Rename this JSON file to **'credentials.json'** and put it in the same directory as **blogBot.py**.

## Almost Done!

Now we must pass the id of the channel from which we wish to obtain videos.

Click [here](https://commentpicker.com/youtube-channel-id.php) and follow the instructions on page to obtain channel id.

When you get id, open **bot.py** and add or replace the information present in **channels**.

```python
# You can add new channels to the list as well
channels = [
    {
        "channel_name": "Abhijit Chavda",
        "channel_tag": "abhijitchavda",
        "channel_id": "UC2bBsPXFWZWiBmkRiNlz8vg",
    },
    {
        "channel_name": "<Name of Channel>",
        "channel_tag": "<Some tag to remember or mark>",
        "channel_id": "<Channel_ID>",
    }
]

```

## Contributing
Pull requests are welcome.

## Known Issues

* Some videos may throw error when fetching transcripts.
* When publishing videos on blogger, 'tags' or 'label' error may occure.

P.S: I have not tested this script on a fresh env yet, some parts can be unstable.

## License
[MIT](https://choosealicense.com/licenses/mit/)
