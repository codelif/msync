import sys
from pprint import pprint

from youtube_title_parse import get_artist_title as extract
from yt_dlp import YoutubeDL



def extract_artist_title(i):
    try:
        # Parse the title to extract only the artist and title.
        artist, title = extract(i["fulltitle"])
    except TypeError:
        # Fallback if youtube_title_parse is not able to parse a title.
        artist, title = (i["channel"], i["fulltitle"])

    title = title.replace("/", "-")  # special case
    artist = artist.replace(" - Topic", "")  # special case

    return title, artist


def get_song():
    LINK = "https://www.youtube.com/watch?v=%s"
    with YoutubeDL({"quiet": True}) as dl:
        search = dl.extract_info("ytsearch:%s" % sys.argv[1], download=False)
        
        song_url = search["entries"][0]["webpage_url"]
        song_info = dl.extract_info(song_url, download=False)

        for i in song_info["formats"]:
            if i["format_id"] == "140":
                return (extract_artist_title(song_info), i["url"])


if __name__ == "__main__":
    from mpd import MPDClient

    (title, artist), link = get_song()

    c = MPDClient()
    c.connect("127.0.0.1", 6600)
    mpdid = c.addid(link)
    c.addtagid(mpdid, "title", title)
    c.addtagid(mpdid, "artist", artist)
    if c.status()["state"] != "play":
        c.playid(mpdid)
    c.close()
    c.disconnect()

    print("Added %s - %s to queue." % (artist, title))
