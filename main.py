import json
import os
import datetime
import requests
from dateutil import parser as time_parser

SRC_DIR = "src"
BEARER_TOKEN = ""
SPOTIFY_USER_ID = ""

class Activity:
    def __init__(self, ts, username, platform, ms_played, conn_country,
                 ip_addr_decrypted, user_agent_decrypted, master_metadata_track_name,
                 master_metadata_album_artist_name, master_metadata_album_album_name,
                 spotify_track_uri, episode_name, episode_show_name, spotify_episode_uri,
                 reason_start, reason_end, shuffle, skipped, offline, offline_timestamp,
                 incognito_mode):
        self.ts = time_parser.parse(ts)
        self.username = username
        self.platform = platform
        self.ms_played = ms_played
        self.conn_country = conn_country
        self.ip_addr_decrypted = ip_addr_decrypted
        self.user_agent_decrypted = user_agent_decrypted
        self.master_metadata_track_name = master_metadata_track_name
        self.master_metadata_album_artist_name = master_metadata_album_artist_name
        self.master_metadata_album_album_name = master_metadata_album_album_name
        self.spotify_track_uri = spotify_track_uri
        self.episode_name = episode_name
        self.episode_show_name = episode_show_name
        self.spotify_episode_uri = spotify_episode_uri
        self.reason_start = reason_start
        self.reason_end = reason_end
        self.shuffle = shuffle
        self.skipped = skipped
        self.offline = offline
        self.offline_timestamp = offline_timestamp
        self.incognito_mode = incognito_mode

    def __eq__(self, other) -> bool:
        return self.ts == other.ts

    def __lt__(self, other) -> bool:
        return self.ts < other.ts

    def __gt__(self, other) -> bool:
        return self.ts > other.ts


class Song:
    def __init__(self, spotify_track_uri, master_metadata_track_name,
                 master_metadata_album_artist_name,
                 master_metadata_album_album_name):
        self.spotify_track_uri = spotify_track_uri
        self.master_metadata_track_name = master_metadata_track_name
        self.master_metadata_album_artist_name = master_metadata_album_artist_name
        self.master_metadata_album_album_name = master_metadata_album_album_name


def read_files(song_dict, activity_list, path):
    files = os.listdir(path)
    for file in files:
        if file.find("endsong") == 0:
            read_file(song_dict, activity_list, os.path.join(SRC_DIR, file))


def read_file(song_dict, activity_list, file_path):
    with open(file_path) as json_file:
        parsed_data = json.load(json_file)
    for activity in parsed_data:
        act = Activity(**activity)
        if act.spotify_track_uri is not None:  # filter out podcasts
            song = Song(act.spotify_track_uri, act.master_metadata_track_name,
                        act.master_metadata_album_artist_name,
                        act.master_metadata_album_album_name)
            if song_dict.get(act.spotify_track_uri) is None:
                song_dict[act.spotify_track_uri] = song
            activity_list.append(act)


def main():
    activity_list = []
    song_dict = {}
    read_files(song_dict, activity_list, SRC_DIR)
    activity_list = sorted(activity_list)

    # find first Activity object index after specific date
    start_date = datetime.date(2021, 12, 1)
    start_index = -1
    for i in range(len(activity_list)):
        if start_date <= activity_list[i].ts.date():
            start_index = i
            break

    # new activity list
    activity_list = activity_list[start_index:]

    # calculate each track listening time
    song_scores = {}
    for activity in activity_list:
        if song_scores.get(activity.spotify_track_uri) is None:
            # song_scores[activity.spotify_track_uri] = 1
            song_scores[activity.spotify_track_uri] = activity.ms_played
        else:
            # song_scores[activity.spotify_track_uri] += 1
            song_scores[activity.spotify_track_uri] += activity.ms_played

    # sort dictionary by value(listening time)
    most_listened = dict(
        sorted(song_scores.items(), key=lambda item: item[1], reverse=True))

    # define headers n token
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {}'.format(BEARER_TOKEN)
    }

    response = requests.request(
        "POST",
        "https://api.spotify.com/v1/users/{}/playlists".format(SPOTIFY_USER_ID),
        headers=headers,
        data=json.dumps({
            "name": "Spotify unwrapped",
            "description": "",
            "public": True
        })
    )

    playlist_uri = json.loads(str(response.text))["uri"]
    playlist_uri = playlist_uri[17:]
    print("New playlist uri: {}".format(playlist_uri))

    i = 0
    for k, v in most_listened.items():
        if i >= 100:
            break
        print(i + 1, k, v, song_dict[k].master_metadata_album_artist_name,
            song_dict[k].master_metadata_track_name)
        url_new = "https://api.spotify.com/v1/playlists/{}/tracks?uris={}".format(
            playlist_uri, k)
        response = requests.request("POST", url_new, headers=headers, data={})
        print(response.text)
        i += 1

if __name__ == "__main__":
    main()
