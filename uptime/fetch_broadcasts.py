"""Save every broadcast on the channel (broadcasts.json) and its video details (videos.json).

Needs a Google OAuth token pickle with the youtube scope, e.g. from GOOGLE_OAUTH_TOKEN_PICKLE_B64.
"""
import base64
import json
import os
import pickle

from google.auth.transport.requests import Request
from googleapiclient.discovery import build


def main():
    creds = pickle.loads(base64.b64decode(os.environ["GOOGLE_OAUTH_TOKEN_PICKLE_B64"]))
    if not creds.valid:
        creds.refresh(Request())
    yt = build("youtube", "v3", credentials=creds)
    items, tok = [], None
    while True:
        r = yt.liveBroadcasts().list(part="id,snippet,status,contentDetails", broadcastStatus="all",
                                     broadcastType="all", maxResults=50, pageToken=tok).execute()
        items += r["items"]
        tok = r.get("nextPageToken")
        if not tok:
            break
    json.dump(items, open("broadcasts.json", "w"), indent=1)
    ids = [x["id"] for x in items]
    videos = {}
    for i in range(0, len(ids), 50):
        r = yt.videos().list(part="contentDetails,liveStreamingDetails,status", id=",".join(ids[i:i + 50])).execute()
        videos.update({v["id"]: v for v in r["items"]})
    json.dump(videos, open("videos.json", "w"), indent=1)
    print(len(items), "broadcasts")


if __name__ == "__main__":
    main()
