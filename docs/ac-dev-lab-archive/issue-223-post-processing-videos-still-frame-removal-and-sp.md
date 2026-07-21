# Issue #223: Post-processing videos (still frame removal and speedup)

- **URL:** https://github.com/AccelerationConsortium/ac-dev-lab/issues/223
- **Author:** @sgbaird
- **State:** open
- **Created:** 2025-04-08T22:30:02Z  **Closed:** None
- **Comments archived:** 39 issue comments

---

## Original description

This can be standalone from #212, but is of course related. The idea would be to remove segments of the video where there is little to no change (which could be difficult when there are blinking lights for example) and run a speedup of e.g., 16x, to later be uploaded to a separate playlist (we can worry about automatic video uploads later, though not sure if that requires just an API key or needs token.pickle).

https://claude.ai/share/217878d2-d194-4441-8c91-9af937ba787b

---

## Comments (complete, in chronological order)

### Comment 1 — @sgbaird at 2025-05-01T21:55:43Z

Per our conversation, I think the decision was to include something in the title (maybe original video id? Or could be timestamp) that we can keep the same between the original and the processed videos, and add some kind of note in the title like: `[processed, 16x]`. @Neil-YL

This can be used with the YouTube API, grabbing lists of the video names from from original and processed. From the YouTube API quota perspective, if multiple pages are returned, each page will count towards the quota.

Per @jonathan-woo 's suggestion, hosting this on a paid-tier HuggingFace space with a the lowest tier GPU (could also try the free, preemptable A100) and the minimum sleep time of 5 minutes of inactivity seems pretty reasonable and low-cost.

@Jonathan-Woo which algorithms/codebases were you looking at? I had found some in the transcript above (a few links were dead of course), might be worth a quick look.

---

### Comment 2 — @sgbaird at 2025-05-01T22:04:03Z

@Jonathan-Woo here's the example video you can use: https://www.youtube.com/live/Tbru5BiokmU?si=Sbmfu5dggSYLpnsp

---

### Comment 3 — @Jonathan-Woo at 2025-05-01T23:05:57Z

Yep, I looked at the transcript, thanks for that. I'm looking into motion and auto-editor right now. Both can provide timestamps. I think I'll test both and examine their performance. Leaning more towards motion as it seems to be more popular.

---

### Comment 4 — @sgbaird at 2025-05-06T18:55:02Z

Related: https://docs.frigate.video/ (I guess @yakavetsiv is incorporating or at least has plans to). Thanks @kelvinchow23 for the ping about it


EDIT: using with esp32 cameras, PoE, and local network

![PXL_20250522_160523717.jpg](https://github.com/user-attachments/assets/702a4783-7486-4c6e-803d-9c6f3085aee4)

![PXL_20250522_160501152.jpg](https://github.com/user-attachments/assets/cceb8c94-eda6-435e-823f-e52cae887ce6)

Ilya running everything on a local server, Zima Cube (frigate, MQTT broker, Prefect local)

![PXL_20250522_164421589.jpg](https://github.com/user-attachments/assets/1baae55b-4846-4abf-8530-9d1482ff4143)




---

### Comment 5 — @Jonathan-Woo at 2025-05-07T18:26:17Z

I've been using [auto-editor](https://github.com/WyattBlue/auto-editor) so far and the results are pretty good on the video linked above. The following command cut these sections out:

https://github.com/user-attachments/assets/0da82384-e7f7-4554-aaa8-1256991032c7

The tricky part is to tune:
1. margin: amount of stale video added to edited sections to smooth out edit
2. threshold: % of "motion" required to not be stale

There is also support for yt-dlp directly so we can pass the stream link directly. Also, there is support for hardware encoding.

```
auto-editor https://www.youtube.com/live/Tbru5BiokmU\?si\=WtsDaMc0DSHxFbKH --edit motion:threshold=0.2 --video-speed 99999 --silent-speed 1 -c:v h264_videotoolbox --download-format bv --margin 10sec
```

One issue is that, since we don't have a wall clock, it's difficult to tell when video is being sped up. So, I'm working on adding an indicator for when video is being sped up. Then, it will be easier to tune the settings.

---

### Comment 6 — @sgbaird at 2025-05-09T22:45:08Z

Really cool to see this! Had thought about adding an overlay directly via the pi zero 2w but not sure if it will handle that extra processing well, and might complicate other things (for one, we lose the raw footage). Ultimately leaned away from it since YouTube already has timestamps.

White text with slightly transparent black background has often worked well from a contrast and aesthetics point of view.

Any luck with adding the indicator?

Also would be great if you could share the sections that were kept, if not too much work.


---

### Comment 7 — @sgbaird at 2025-05-12T16:58:48Z

@Jonathan-Woo bump

---

### Comment 8 — @Jonathan-Woo at 2025-05-12T18:01:14Z

> Really cool to see this! Had thought about adding an overlay directly via the pi zero 2w but not sure if it will handle that extra processing well, and might complicate other things (for one, we lose the raw footage). Ultimately leaned away from it since YouTube already has timestamps.
> 
> White text with slightly transparent black background has often worked well from a contrast and aesthetics point of view.
> 
> Any luck with adding the indicator?
> 
> Also would be great if you could share the sections that were kept, if not too much work.

Still working on adding the indicator. I'm using ffmpeg to add an overlay similar to https://video.stackexchange.com/questions/12105/add-an-image-overlay-in-front-of-video-using-ffmpeg. 

Overall, this my plan:
1. auto-editor to get [v1](https://auto-editor.com/docs/v1) file to get timestamps for when to add overlay.
2. ffmpeg to add overlay
3. auto-editor to accelerate stale sections

This is the kept video:

https://github.com/user-attachments/assets/cba3e7eb-780f-488b-8eb8-9e61ccde58c8

---

### Comment 9 — @sgbaird at 2025-05-12T18:26:25Z

Awesome, thanks! It seems like it did a pretty good job with separating the stale vs. non-stale

> auto-editor to accelerate stale sections

Quick aside: Originally, I was imagining deleting the stale sections entirely and speeding up the non-stale sections

---

### Comment 10 — @Jonathan-Woo at 2025-05-12T18:32:32Z

Sure that's totally possible. We would just have to update the `--silent-speed` argument.

---

### Comment 11 — @Jonathan-Woo at 2025-05-14T18:31:10Z

Overlay has been added.

https://github.com/user-attachments/assets/998b1555-a738-4143-847d-ad0dbbfff0e3

I'm concerned about removing stale sections entirely because I'm concerned that this editor may have false positives.

I will share the final sped up version soon. In the meantime we should think about what to remove/speed up.

---

### Comment 12 — @sgbaird at 2025-05-14T21:25:34Z

Nice! Good point about false positives. I'm worried a bit about devices that have a lot of stale time (e.g., 8 hrs of stale video @ 16x = 30 min), which might get cumbersome for promo vids and robotic training. Though, it could cause problems if people are doing post-mortem analysis (i.e., watching the sped-up video) and miss something that would otherwise catch their eye.

I could be missing something else too. I should probably document and consolidate the various intended uses somewhere (these have made it on a whiteboard occasionally).

Aside: is the intention to put the speedup factor in the overlay? (e.g., `16x`).

---

### Comment 13 — @Jonathan-Woo at 2025-05-15T01:47:11Z

This is the edited version with the overlay indicating 16x. It still flickers a bit so the sensitivity governed by the motion will likely need to be tuned more.

Other parts of the pipeline left is the communication with youtube in terms of downloading, uploading, organizing into playlists, etc. Let's sync tomorrow?

https://github.com/user-attachments/assets/06cb2b35-ec54-48c8-ae60-cf6dd2f6cc4d

---

### Comment 14 — @sgbaird at 2025-05-15T21:00:36Z

> communication with youtube in terms of downloading, uploading, organizing into playlists, etc.

Based on our conversation, [try adding timestamp directly on Zero 2W](https://github.com/AccelerationConsortium/ac-training-lab/issues/213) (looks like picamera2 has a built-in option that will hopefully not add too much processing overhead). We also agreed that when 16x appears for the stale video, we naturally expect to see something moving quickly, so it's not quite as clear for a 1-second display of 16x that 16 seconds have gone by. A running timestamp will probably make this more straightforward.

Easy way to get rid of section is to set speedup to huge value (999x) so it essentially just disappears. Might be worth a quick check to verify it doesn't cause an error to have massive speedup like this that wipes out all frames for that section.

Moving on to the hugging face portion, scheduling to avoid constant GPU consumption is probably the main challenge. Based on a quick search:
- https://www.google.com/search?q=schedule+for+hugging+face+space
- https://huggingface.co/docs/huggingface_hub/main/en/guides/manage-spaces
- https://github.com/kghamilton89/spaces-scheduler

High-level purposes review:
1. Real-time, remote hardware development (not relevant to speedup)
2. Flashy/cool demos, promo videos (ideal is to cut stale video almost entirely, with max a few seconds at a time without motion)
3. Post-mortem / failure analysis (i.e., when you don't know the timestamp of an event, but want to get a general sense of the process or see if something unexpected happens)
4. Training datasets for roboticists (video + timestamps + metadata such as temperature/humidity/hardware logs. Cropping the video afterwards to remove a UTC timestamp overlay portion is probably not a huge issue. As long as timestamps for metadata like temperature are stored elsewhere, we don't need to worry about storing that on YouTube side).

@Jonathan-Woo - some [documentation by Yanghuang related to OAuth 2.0](https://github.com/AccelerationConsortium/ac-training-lab/issues/202#issuecomment-2770625621), though I think you can probably use the pickle file I shared directly with you. As you mentioned, you can probably deserialize the pickle file, store it as text as a Hugging Face Space, and then reserialize it. I could be missing something.

The plan is to start with a free CPU-version on HuggingFace and lmk when I should convert it to a paid GPU-tier.

---

### Comment 15 — @sgbaird at 2025-05-27T12:13:28Z

@Jonathan-Woo do you think HF is the right platform for doing this? There's not really a need for a GUI (more of a service). Though there might still be an appeal from a cost perspective (not sure how HF compares).

---

### Comment 16 — @Jonathan-Woo at 2025-05-27T14:55:45Z

Yes I think HF is a good platform for this. 

1. We wouldn't have to take on and support another service.
2. It supports task scheduling and can switch to different hardware as required which makes it easy for us to scale.
3. I think we would still want to visualize the processing progress and this would be a very convenient way to access it.

---

### Comment 17 — @sgbaird at 2025-05-27T16:23:15Z

All points make sense to me, and I'm aligned on that. Thanks for detailing!

---

### Comment 18 — @Jonathan-Woo at 2025-06-07T17:05:40Z

Almost finished MWE here: https://huggingface.co/spaces/AccelerationConsortium/Video-Processing?logs=container

Current issue is that the tool we use for downloading youtube videos, `yt-dlp`, requires cookies for authentication. When testing locally, it's not an issue as we can forward the cookies from our browser. But for the HF space, we can't access the browser, navigate to youtube, and login to get the cookie. So, I believe the options are:

1. Download your cookies and upload them to the space before use.
2. Use `yt-dlp` locally to download the videos and then upload them for processing.

---

### Comment 19 — @sgbaird at 2025-06-07T21:16:52Z

Could you link the documentation for the cookies, if available?

---

### Comment 20 — @sgbaird at 2025-06-07T21:19:02Z

Also, does the following have the same requirement for cookies as `yt-dlp`? (Linked from #212) - https://github.com/ytdl-org/youtube-dl

---

### Comment 21 — @Jonathan-Woo at 2025-06-07T21:27:59Z

> Could you link the documentation for the cookies, if available?

Under the "How do I pass cookies to yt-dlp?" section: https://github.com/yt-dlp/yt-dlp/wiki/FAQ


---

### Comment 22 — @Jonathan-Woo at 2025-06-07T21:30:42Z

> Also, does the following have the same requirement for cookies as `yt-dlp`? (Linked from [#212](https://github.com/AccelerationConsortium/ac-training-lab/issues/212)) - https://github.com/ytdl-org/youtube-dl

I believe so. `youtube-dl` is no longer maintained and `yt-dlp` should contain all the features of `youtube-dl` as it merged with it.

---

### Comment 23 — @sgbaird at 2025-06-07T21:48:27Z

Aside:

Noticed they have a Python wrapper - https://github.com/yt-dlp/yt-dlp#embedding-yt-dlp

and that it's pip-installable (noticed you're using that)

https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-download-only-new-videos-from-a-playlist seems helpful for our use case (at least relevant)

Could you rename requirements.txt to requirements-frozen.txt or similar and make a minimal requirements.txt? (Not sure what's required other than yt-dlp in your code)

For the cookies, since there's a method for having a txt file, I suppose we could have this as an environment secret?

Any idea on how frequently the cookies would need to be refreshed? It seems these cookies are tied to a specific account. Might make a separate one for this.

Do you know if this will work for private videos as well? (Unlisted I imagine shouldn't make a difference from public, but private videos require authentication)

---

### Comment 24 — @Jonathan-Woo at 2025-06-07T22:05:50Z

I've removed unnecessary packages from the requirements. 

It seems like the cookies last a few hours at best: https://github.com/yt-dlp/yt-dlp/issues/8227

Regarding private videos, I'm not sure. My understanding of `yt-dlp` is that it retrieves videos similarly to how the youtube webpage does so if you're able to view it on youtube, `yt-dlp` should work. Though again, I haven't tried it.

---

### Comment 25 — @sgbaird at 2025-06-07T23:47:25Z

Aside: even though we're downloading content that we have the rights to, we'll need to be mindful and probably use a dedicated account -  https://github.com/yt-dlp/yt-dlp/wiki/Extractors#exporting-youtube-cookies

Also some other info above

---

### Comment 26 — @sgbaird at 2025-06-08T00:51:42Z

Another option we could consider is using [playwright](https://playwright.dev/python/) (I've been using the MCP server for it at times, saw it listed on one of GitHub's tutorials as an example MCP) and having it login and go directly to the download button on the YouTube UI for the various videos.

I'm not sure if playwright could handle that, but maybe worth a shot (either for automatically retrieving cookies or for navigating to YouTube's built-in download link for self-owned videos).

---

### Comment 27 — @sgbaird at 2025-06-11T04:30:21Z

@Jonathan-Woo do you have some of the processed videos that you can share? Let me know if you need specific links that are going to have more interesting content.

---

### Comment 28 — @sgbaird at 2025-06-20T18:20:28Z

cc @zweaung1014 

---

### Comment 29 — @sgbaird at 2025-06-26T15:37:56Z

@zweaung1014 I sent you an invite to Hugging Face, once you've accepted the invite I'll give you access to https://huggingface.co/spaces/AccelerationConsortium/Video-Processing. Probably, we'll make it public (ensuring that there aren't any secrets in the history). From there, could you work on replacing the yt-dlp downloading with your playwright implementation?

---

### Comment 30 — @zweaung1014 at 2025-06-26T21:35:37Z

@sgbaird Turns out, my playwright implementation might also be running into cookie issues. The download sometimes works and sometimes doesn't. It's pretty inconsistent. When i manually download from an incognito browser, it doesn't download. But when I do it from a normal one, it downloads. Since the playwright script opens its own session, it also behaves like an incognito browser. Hence the cookie problem. 

I put it in my repo: https://github.com/zweaung1014/yt_download_2FA.git
`verify_pyotp.py` is what runs the script
The secret code is stored as a "Repository Secret"; not in the code.

---

### Comment 31 — @zweaung1014 at 2025-06-26T21:48:00Z

The way the script works is, it goes to the link first, and takes the video title. Then, it signs in with 2FA and goes to the YouTube Studio page. On this page, it finds the video title it stored earlier, and clicks it. 

I was having a problem at first because I was telling it to click the checkbox, go to "More Actions", and click "Download". But this throws frequent errors due to timing. Clicking the video title first is a much more consistent process.

The last step is to click the Options menu and click "Download".

---

### Comment 32 — @sgbaird at 2025-06-26T22:54:10Z

Could you use Python to change the string URL to the correct one, rather than clicking to get there?

---

### Comment 33 — @sgbaird at 2025-06-26T23:04:15Z

It was seeming to work ok in the copilot actions. Not sure if there was something different or it was implying it did but not actually 

---

### Comment 34 — @sgbaird at 2025-06-26T23:08:30Z

Maybe we put this back in the playwright PR discussion

---

### Comment 35 — @zweaung1014 at 2025-06-26T23:31:15Z

> Could you use Python to change the string URL to the correct one, rather than clicking to get there?

Good point! Let me do that.

---

### Comment 36 — @sgbaird at 2025-07-02T21:00:35Z

(scheduled) any updates? (I know you were working a lot on solid dosing, etc. so no worries if not)

Get Outlook for Android<https://aka.ms/AAb9ysg>
________________________________
From: Larry Aung ***@***.***>
Sent: Thursday, June 26, 2025 7:31:36 PM
To: AccelerationConsortium/ac-training-lab ***@***.***>
Cc: Sterling Baird ***@***.***>; Mention ***@***.***>
Subject: Re: [AccelerationConsortium/ac-training-lab] MWE for post-processing videos (still frame removal and speedup) on HF space (Issue #223)

[https://avatars.githubusercontent.com/u/135032017?s=20&v=4]zweaung1014 left a comment (AccelerationConsortium/ac-training-lab#223)<https://github.com/AccelerationConsortium/ac-training-lab/issues/223#issuecomment-3010622984>

Could you use Python to change the string URL to the correct one, rather than clicking to get there?

Good point! Let me do that.

—
Reply to this email directly, view it on GitHub<https://github.com/AccelerationConsortium/ac-training-lab/issues/223#issuecomment-3010622984>, or unsubscribe<https://github.com/notifications/unsubscribe-auth/AK25ABIGUPFKJV5M3Z3QIEL3FR7FRAVCNFSM6AAAAAB2XONWPCVHI2DSMVQWIX3LMV43OSLTON2WKQ3PNVWWK3TUHMZTAMJQGYZDEOJYGQ>.
You are receiving this because you were mentioned.Message ID: ***@***.***>


---

### Comment 37 — @sgbaird at 2025-07-12T03:53:36Z

Like we talked about, Larry - thanks for prioritizing the SDL2 workflows. @Jonathan-Woo is available again to work on this, so he'll pick up from where you left off (thanks for your patience with the relay race).

EDIT: Here's where we left off https://github.com/AccelerationConsortium/ac-training-lab/pull/343#issuecomment-3040740167

Also, @Jonathan-Woo I think you mentioned there were some ways we may be able to speed up the process? (It would be good to get a sense of the time required to process a single video in general, too). I think you mentioned avoiding encoding the segments that would be removed anyway

---

### Comment 38 — @Jonathan-Woo at 2025-07-16T20:39:17Z

Yes, so here's how things currently work. 

1. `auto-editor` is used to detect stale video sections
2. `ffmpeg` applies overlay
3. `auto-editor` is applied to speed-up sections

Currently, step 2 naively re-encodes the entire video after adding the overlay which can be accelerated by using stream copy to avoid encoding unedited sections. I'm working on this.

---

### Comment 39 — @sgbaird at 2025-08-21T17:24:18Z

Porting most development and code over to https://github.com/AccelerationConsortium/youtube-livestream-processor, new issues to be raised there.

We may also end up clearing out https://github.com/AccelerationConsortium/ac-training-lab/tree/main/src/ac_training_lab/video_editing since it's redundant now.

---
