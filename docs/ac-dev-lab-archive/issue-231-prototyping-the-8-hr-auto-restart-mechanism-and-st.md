# Issue #231: Prototyping the 8-hr auto-restart mechanism and stream restoration

- **URL:** https://github.com/AccelerationConsortium/ac-dev-lab/issues/231
- **Author:** @sgbaird
- **State:** open
- **Created:** 2025-04-28T16:21:36Z  **Closed:** None
- **Comments archived:** 45 issue comments

---

## Original description

Related:
- https://github.com/AccelerationConsortium/ac-training-lab/issues/202 (focused on getting the API set up and pulling stream URL automatically)
- https://github.com/AccelerationConsortium/ac-training-lab/issues/212
- https://github.com/AccelerationConsortium/ac-training-lab/issues/223


Based on discussion with @Neil-YL:

How should the following tasks be handled (e.g., same manager, different managers):
1. Close the current stream and start a new one every 8 hours
2. Log the recent status of each stream into a CSV every 10-15mins
3. Report the latest download link to a database

Or is it better to separate these into different scripts or services?

Maybe the monitor (task 2) as a separate service.  Maybe the auto-restart and download links as a schedule-based service (e.g., scheduled task with Prefect) to trigger the workflow: first retrieve the download link for the latest completed video (not the currently active stream), then close the current broadcast and create a new one.

Another idea is to have a monitor create new stream when `device_name` is not in active stream list, and an 8-hr schedule to end all active streams

> 8-hr schedule to end all active streams
This one could also restart the stream, to minimize downtime (i.e., loop through each stream one at a time --> [end stream, restart stream]), but maybe this would cause issues if the monitor and this both try to restart the same stream.

It could be one code/service to both end/restart and monitor, when executing ending and restart, try to move out of the loop of the checking and when the restart completed back to the monitor loop.

---

There also needs to be a service that auto-downloads the videos and post-processes them (high bandwidth, so probably don't want to mix with the scripts that ensure uptime). This might be long-running processes on the order of 1+ hrs for each video, where GPUs would significantly accelerate the process. If there are only a few streams, a single service might be able to handle this. If there are 50+ streams, then there would need to be multiple machines doing the processing. This might justify some kind of trigger-based and on-demand mechanism.. (instead of having a few dedicated machines doing the processing). This might still require a schedule and monitor to see if new videos are available in a playlist (or if new entries are available in MongoDB).

https://prefect-community.slack.com/archives/C04DZJC94DC/p1745859761114599?thread_ts=1745858182.153999&cid=C04DZJC94DC

<details>

Sterling Baird
  42 minutes ago
[@Marvin](https://prefect-community.slack.com/team/ULVA73B9P)
 how do you handle on-demand spinup of resources based on monitoring some kind of condition? (e.g., new entry added to a MongoDB database)

Marvin
APP  [41 minutes ago](https://prefect-community.slack.com/archives/C04DZJC94DC/p1745859761114599?thread_ts=1745858182.153999&cid=C04DZJC94DC)
To handle on-demand resource spinup based on a condition like a new entry in a MongoDB database using Prefect, you can follow these general steps:
1. Monitoring and Triggering: Use Prefect's event-driven triggers to monitor conditions. For instance, you can create a custom trigger that listens for specific events such as changes in your MongoDB database. Prefect allows you to define custom events and triggers that can start flows based on these events. More details can be found in the [Prefect custom triggers documentation](https://docs-3.prefect.io/v3/automate/events/custom-triggers).
2. Infrastructure Provisioning: Prefect can automatically provision the necessary infrastructure for running your flows. This is done using Prefect's CLI with the --provision-infra flag, which allows for serverless resource provisioning. This requires proper authentication and setup with your cloud provider, such as AWS. You can find more information in the [Prefect infrastructure examples documentation](https://docs-3.prefect.io/v3/deploy/infrastructure-examples/serverless).
3. Flow Definition: Define your flow using Prefect's flow decorator, which is part of the core API. Prefect supports imperative programming styles, which should suit your preference.
For more specific implementations, you may need to integrate with Prefect's Python API to define tasks that interact with MongoDB and trigger flows based on the results.
If you have more specific requirements or need further clarification, feel free to ask!

</details>

---

## Comments (complete, in chronological order)

### Comment 1 — @Neil-YL at 2025-04-29T19:17:59Z

While testing the "End device stream and start a new one" function, I noticed that even with "Autostart" enabled, which should automatically start the stream when YouTube receives data from the RTMP stream key, the stream doesn't begin immediately with "Excellent connection".

<img width="1053" alt="Image" src="https://github.com/user-attachments/assets/2a0269f1-f04e-4bad-a00f-d04341bf3065" />

To clarify: When YouTube API creates a new "Broadcast", it initially appears as "Scheduled", which can then be started either manually or via Autostart.  

This could result in losing footage and may also bring many troubles for the monitor set up (but we can simply add "Scheduled" as an active broadcast in the restart condition)

<img width="972" alt="Image" src="https://github.com/user-attachments/assets/7fbd8565-f3e5-42f7-bc42-96d96a12e4bc" />
(In this test, the OT-2 stream started in about 5 minutes, but the A1 Mini stream took more than 20 minutes to start after the manager triggered the "End device stream and start a new one")  




---

### Comment 2 — @Neil-YL at 2025-04-30T14:03:48Z

Sum up for the test yesterday:

I set a 5 hours restart yesterday at around 16:35.

So it will trigger end and restart at 21:35, 2:35, 7:35, we should have 3 video for each device, and a live now. 
1. 16:35-21:35
2. 21:35-2:35
3. 2:35-7:35
4. 7:35-now

Now we only has the footage for:

- OT2: 1. 4hrs 56mins; 2. 32mins; 3. no footage; 4. no live;
- A1mini: 1. 4rs56mins; 2. no footage; 3: 1hr52mins; 4. on live;
- Pi4-test: 1. no footage; 2. 32mins; 3. no footage; 4. no live;
 
The 32 mins records are very likely be triggered by the 2am reboot on the zero2w, but not sure why A1mini doesn't have a similar 32mins video.

<img width="976" alt="Image" src="https://github.com/user-attachments/assets/7216a5e7-9006-4604-ab90-af1fb1692780" />

Update:

When checking the status of the un-started broadcast, it shows as "ready" but never covert to "active" 
YouTube API provides a status transition request, it only applies to broadcasts that are already in the "active" state: 

> Note that to transition a broadcast to either the testing or live state, the [status.streamStatus](https://developers.google.com/youtube/v3/live/docs/liveStreams#status.streamStatus) must be active for the stream that the broadcast is bound to.

Very similar to our situation: https://stackoverflow.com/a/79204910

---

### Comment 3 — @sgbaird at 2025-04-30T18:28:07Z

Thanks for collecting the data and the update! If the "already sending data" piece is the main issue and isn't one that can easily be overcome with YouTube's API and restrictions, then we may need to brainstorm a bit more. We could use an AWS Lambda function perhaps that handles the setup and teardown of the streams and call the lambda function from the device directly. The `token.pickle` file could live on the AWS Lambda instance, and this way the device script can stop sending data, tear down the stream, set it back up, and then start sending data again. Thoughts?

---

### Comment 4 — @sgbaird at 2025-05-01T12:00:10Z

As a side note, I think it may be worth changing the stream latency to "low-latency", and possibly adding a delay (unless adding a delay doesn't help). There seems to be missing segments (e.g., when the OT-2 was removed from the office for the event), as noted in a separate issue (I think the OT-2 equipment monitoring issue or the original Zero 2W issue).
[cid:d31037e8-050a-4f89-aa50-c024665cd509]


---

### Comment 5 — @Neil-YL at 2025-05-01T13:47:40Z

> As a side note, I think it may be worth changing the stream latency to "low-latency", and possibly adding a delay (unless adding a delay doesn't help). There seems to be missing segments (e.g., when the OT-2 was removed from the office for the event), as noted in a separate issue (I think the OT-2 equipment monitoring issue or the original Zero 2W issue).
> [cid:d31037e8-050a-4f89-aa50-c024665cd509]

I think it is because it happened to have a no data issue during the removal period. I will change the latency to low in next start.

---

### Comment 6 — @Neil-YL at 2025-05-01T14:22:19Z

<img width="1110" alt="Image" src="https://github.com/user-attachments/assets/68b757c2-04ef-4418-b888-21232a021801" />

<img width="1172" alt="Image" src="https://github.com/user-attachments/assets/94a70c12-a3ea-48c2-b6fc-73a0806500a1" />

Add enableMonitorStream: false to the broadcast creating codes as suggested in one stackoverflow, seems not help in improving the uptime:

14:00 - 19:00: lose around 30mins
19:00 - 24:00: lose around 1hrs 8/15mins
0:00 - 5:00: lose around 1hrs 40mins and 2 hrs
5:00 - now: never start until I reboot zero2w


I will think about the cross devices end and restart.
Basic scheme:
Manager: End device.py on zero2w --> End YTB broadcast --> Restart YTB broadcast --> Restart device.py on zero2w
(It also could be:  End YTB broadcast --> Restart YTB broadcast --> End device.py on zero2w --> Restart device.py on zero2w?)
Monitor: Find which device broadcast is down  --> End device.py on zero2w -->  Restart YTB broadcast --> Restart device.py on zero2w

---

### Comment 7 — @Neil-YL at 2025-05-01T21:10:52Z

> Thanks for collecting the data and the update! If the "already sending data" piece is the main issue and isn't one that can easily be overcome with YouTube's API and restrictions, then we may need to brainstorm a bit more. We could use an AWS Lambda function perhaps that handles the setup and teardown of the streams and call the lambda function from the device directly. The `token.pickle` file could live on the AWS Lambda instance, and this way the device script can stop sending data, tear down the stream, set it back up, and then start sending data again. Thoughts?


[Scheduled reboot via crontab]  
      ↓  
[Zero2W reboots]  
      ↓  
[systemd auto-starts device.py]  
      ↓  
[device.py, before starting P1/P2 stream]  
    → Calls Lambda to:  
        - End current YouTube broadcast  
        - Start a new one
        - Return successful message 
      ↓  
[device.py starts stream and enters existing while loop]  
  

I think by doing so, we can limit the changes to our systemd setup and the `device.py` while loop, helping maintain overall stability.  


---

### Comment 8 — @sgbaird at 2025-05-01T21:27:20Z

This sounds great! I thing this leverages the scheduling strengths of cron pretty well, and like you said avoids complicating device top high which already took a while to get it to be robust.

---

### Comment 9 — @sgbaird at 2025-05-01T21:58:39Z

> Per our conversation, I think the decision was to include something in the title (maybe original video id? Or could be timestamp) that we can keep the same between the original and the processed videos, and add some kind of note in the title like: [processed, 16x]. @Neil-YL

Source: https://github.com/AccelerationConsortium/ac-training-lab/issues/223#issuecomment-2845867241

---

### Comment 10 — @sgbaird at 2025-05-01T22:27:59Z

@Neil-YL instructions https://github.com/ACC-HelloWorld/5-data-logging#aws-lambda-function

---

### Comment 11 — @Neil-YL at 2025-05-05T17:39:44Z

I finished the setup on AWS Lambda. I will start working on the device.py and the crontab restart.

Here is a test on starting a new broadcast for A1mini
<img width="749" alt="Image" src="https://github.com/user-attachments/assets/d07d9bc9-25ea-44f8-b0be-c54591edae8b" />

---

### Comment 12 — @Neil-YL at 2025-05-06T16:44:01Z

OK I think I have finished the deployment and I put it on the Bambu A1mini stream zero2w for test. I set a reboot at 05:00, 13:00 and 21:00 with crontab. 
Now the playlist has 27 video so it would be 30 tomorrow. 
<img width="256" alt="Image" src="https://github.com/user-attachments/assets/995775dc-4808-4bcb-9a1a-ed53432186d3" />

If everything works as expected I will create a PR later.



---

### Comment 13 — @sgbaird at 2025-05-07T01:01:56Z

Awesome! Funnily, just as I was reading this, I got a yt notification (9:01 pm)

---

### Comment 14 — @Neil-YL at 2025-05-07T13:41:38Z

<img width="390" alt="Image" src="https://github.com/user-attachments/assets/28a91a81-0813-4ac6-97b0-7d057c775106" />
Looks good! 


---

### Comment 15 — @sgbaird at 2025-05-07T13:54:57Z

This is amazing! 45 s downtime is not bad at all either 🚀 thank you!

I'll try to figure out how we can get the lambda function centralized. Do you mind pasting a snippet of the lambda function code here?

The 8 hour restart mechanism looks solid!

---

### Comment 16 — @Neil-YL at 2025-05-07T14:34:17Z


> I'll try to figure out how we can get the lambda function centralized. Do you mind pasting a snippet of the lambda function code here?


https://colab.research.google.com/drive/1ApwqbTkNmUfOAlsTlrTavd4yR_tprOPT?usp=sharing

Colab to generate the deployment.zip for Lambda.
(The logger in the Lambda function may not be necessary. I only used it for debugging)

---

### Comment 17 — @sgbaird at 2025-05-08T12:00:13Z

Also, just to confirm - is this UTC time? We probably talked about this already

Get Outlook for Android<https://aka.ms/AAb9ysg>
________________________________
From: Yanghuang Liu ***@***.***>
Sent: Wednesday, May 7, 2025 10:34:39 AM
To: AccelerationConsortium/ac-training-lab ***@***.***>
Cc: Sterling Baird ***@***.***>; Author ***@***.***>
Subject: Re: [AccelerationConsortium/ac-training-lab] Prototyping the 8-hr auto-restart mechanism and stream restoration (Issue #231)

[https://avatars.githubusercontent.com/u/179746567?s=20&v=4]Neil-YL left a comment (AccelerationConsortium/ac-training-lab#231)<https://github.com/AccelerationConsortium/ac-training-lab/issues/231#issuecomment-2858833436>

I'll try to figure out how we can get the lambda function centralized. Do you mind pasting a snippet of the lambda function code here?

https://colab.research.google.com/drive/1ApwqbTkNmUfOAlsTlrTavd4yR_tprOPT?usp=sharing

Colab to generate the deployment.zip for Lambda.

—
Reply to this email directly, view it on GitHub<https://github.com/AccelerationConsortium/ac-training-lab/issues/231#issuecomment-2858833436>, or unsubscribe<https://github.com/notifications/unsubscribe-auth/AK25ABPKXI25I3EQJV4CDRT25IKX7AVCNFSM6AAAAAB4A2Z2H6VHI2DSMVQWIX3LMV43OSLTON2WKQ3PNVWWK3TUHMZDQNJYHAZTGNBTGY>.
You are receiving this because you authored the thread.Message ID: ***@***.***>


---

### Comment 18 — @sgbaird at 2025-05-08T12:00:13Z

Looks like something odd happened with a couple last night.

Get Outlook for Android<https://aka.ms/AAb9ysg>
________________________________
From: Yanghuang Liu ***@***.***>
Sent: Wednesday, May 7, 2025 10:34:39 AM
To: AccelerationConsortium/ac-training-lab ***@***.***>
Cc: Sterling Baird ***@***.***>; Author ***@***.***>
Subject: Re: [AccelerationConsortium/ac-training-lab] Prototyping the 8-hr auto-restart mechanism and stream restoration (Issue #231)

[https://avatars.githubusercontent.com/u/179746567?s=20&v=4]Neil-YL left a comment (AccelerationConsortium/ac-training-lab#231)<https://github.com/AccelerationConsortium/ac-training-lab/issues/231#issuecomment-2858833436>

I'll try to figure out how we can get the lambda function centralized. Do you mind pasting a snippet of the lambda function code here?

https://colab.research.google.com/drive/1ApwqbTkNmUfOAlsTlrTavd4yR_tprOPT?usp=sharing

Colab to generate the deployment.zip for Lambda.

—
Reply to this email directly, view it on GitHub<https://github.com/AccelerationConsortium/ac-training-lab/issues/231#issuecomment-2858833436>, or unsubscribe<https://github.com/notifications/unsubscribe-auth/AK25ABPKXI25I3EQJV4CDRT25IKX7AVCNFSM6AAAAAB4A2Z2H6VHI2DSMVQWIX3LMV43OSLTON2WKQ3PNVWWK3TUHMZDQNJYHAZTGNBTGY>.
You are receiving this because you authored the thread.Message ID: ***@***.***>


---

### Comment 19 — @Neil-YL at 2025-05-08T13:42:52Z

> Also, just to confirm - is this UTC time? We probably talked about this already

Yes.

> Looks like something odd happened with a couple last night.

I was working on the PR yesterday, and the streaming Zero2W was very laggy, so I stopped the service and paused the stream for a while. I restarted it around 2 PM, so the footage is incomplete for these two clips.  (5am to 1pm and 1pm to 9pm).



---

### Comment 20 — @sgbaird at 2025-05-08T13:46:07Z

Ah, got it. Thanks!

---

### Comment 21 — @Neil-YL at 2025-05-08T13:56:20Z

> Ah, got it. Thanks!

Can I merge this one https://github.com/AccelerationConsortium/ac-training-lab/pull/241 so that I can deploy the code on other devices.

---

### Comment 22 — @sgbaird at 2025-05-08T20:34:42Z

Difficult to share Lambda function directly on AWS, so instead long-term we may switch to having the lambda function on GitHub and automatically deploy to cloud via [AWS Chalice](https://aws.github.io/chalice) for example, per comment in:

https://stackoverflow.com/questions/58441717/how-to-share-lambda-function-with-another-user-in-organization

---

### Comment 23 — @Neil-YL at 2025-05-09T13:33:34Z

<img width="1105" alt="Image" src="https://github.com/user-attachments/assets/a113a4c5-4a9e-43aa-9cda-d6a7e00da517" />

---

### Comment 24 — @sgbaird at 2025-05-09T13:37:48Z

Amazing!

---

### Comment 25 — @sgbaird at 2025-05-09T13:41:23Z

Another thought about naming schemes: we could have the hostnames and video titles be non-workflow-specific (e.g., SDL5 camera-7t3j) and have the playlists be workflow/hardware in the playlist titles. This could make it more flexible as labs evolve and needs change.

---

### Comment 26 — @Neil-YL at 2025-05-09T13:59:22Z

> Another thought about naming schemes: we could have the hostnames and video titles be non-workflow-specific (e.g., SDL5 camera-7t3j) and have the playlists be workflow/hardware in the playlist titles. This could make it more flexible as labs evolve and needs change.

I would prefer to have same/similar name for the broadcast/video and playlist since the` start stream and add to playlist` function is using the same parameter to match the streamkey, create broadcast title and add to playlist. Or we have to add another mapping between the two (within the YouTube API utils script). 

Using a non-workflow-specific host name seems very reasonable to me though.

--------
More thoughts:

It would be more reasonable if the create funtion is(Camera_name, playlist_name) so we could swap camera between monitored device/workflow. After all I would have to update those zero2w running old device.py without the visibility. 

---

### Comment 27 — @sgbaird at 2025-05-09T14:20:02Z

Those points make sense to me!

---

### Comment 28 — @sgbaird at 2025-05-09T15:35:01Z

- Try to change stream key to one-time stream key (otherwise, can just create new ones each time and eventually get rid of old ones)

EDIT: change "isReusable" to False (not sure if it will delete it or just inactivate it after the first use)
```python
        if not matched_stream:
            print(f"No matching stream found for '{device_name}', creating a new one...")
            stream_response = YOUTUBE.liveStreams().insert(
                part="snippet,cdn,contentDetails",
                body={
                    "snippet": {"title": f"{device_name} stream key"},
                    "cdn": {
                        "frameRate": "variable",
                        "resolution": "variable",
                        "ingestionType": "rtmp"
                    },
                    "contentDetails": {
                        "isReusable": True
                    }
                }
            ).execute()
            matched_stream = stream_response
            stream_id = matched_stream["id"]
```

- Separate device name into camera name + workflow name
- Remove stream key from device secrets, return stream key from lambda
- Lambda should receive both camera name and workflow name
- Camera hostname without workflow / hardware name (e.g., no "ot2")

Aside:

Maybe worth noting there is the ability to ["update"](https://developers.google.com/youtube/v3/live/code_samples) the title and description of a stream, though single use stream keys would be a bit more secure since lambda would be returning the stream key (and leaking a single stream key causes issues with all future videos with that stream, and could be problematic especially for private streams).
![Image](https://github.com/user-attachments/assets/8ecb63d0-90a5-430f-8c5a-efc80ccc6c47)

---

### Comment 29 — @Neil-YL at 2025-05-12T01:36:13Z

Now all three livestream devices are on new script with the workflow_name and cam_name, using returned one-time stream key from YouTube API for streaming.

Also changed hostname on Zero2w. 

<img width="1206" alt="Image" src="https://github.com/user-attachments/assets/366ee53f-4ba1-465e-80a7-39ad8563e279" />

---

### Comment 30 — @sgbaird at 2025-05-21T15:49:02Z

Looks like [all streams are down](https://studio.youtube.com/channel/UCHBzCfYpGwoqygH9YNh9A6g/videos/live?filter=%5B%5D&sort=%7B%22columnType%22%3A%22date%22%2C%22sortOrder%22%3A%22DESCENDING%22%7D). Maybe something to do with the lambda function?

There are many repeats of ones that are scheduled, which could also mean the device restart mechanism is having some issues (e.g., lambda function returns error after successfully scheduling a stream, then device script restarts due to error, triggering lambda function again, but only up to X number of times due to systemd restart limit?).

Wondering if related to credentials/authorization and possible expired token.

![Image](https://github.com/user-attachments/assets/0f7bac64-390f-4435-a910-eb1bbe74c6cc)

Maybe worth moving to using 

> Difficult to share Lambda function directly on AWS, so instead long-term we may switch to having the lambda function on GitHub and automatically deploy to cloud via [AWS Chalice](https://aws.github.io/chalice) for example, per comment in:
> 
> https://stackoverflow.com/questions/58441717/how-to-share-lambda-function-with-another-user-in-organization

The difficulty of sharing the lambda function is a bit annoying. Maybe worth creating a separate set of credentials that owns the lambda function and that both of us share (not sure what best practice here is). In addition, could be good to move to Chalice so the script is hosted on gh.. thoughts?

---

### Comment 31 — @Neil-YL at 2025-05-21T17:11:02Z

Checked the log on the device service:

> 
> Sending to Lambda: {'action': 'end', 'cam_name': 'cam-fb7p', 'workflow_name': 'OT2-LCM-TrainingLab', 'privacy_status': 'private'}
> Status code: 200
> Response text: OT2-LCM-TrainingLab ended successfully
> Lambda 'end' succeeded: OT2-LCM-TrainingLab ended successfully
> Sending to Lambda: {'action': 'create', 'cam_name': 'cam-fb7p', 'workflow_name': 'OT2-LCM-TrainingLab', 'privacy_status': 'public'}
> Status code: 500
> Response text: Error during 'create' for device 'OT2-LCM-TrainingLab': <HttpError 500 when requesting https://youtube.googleapis.com/youtube/v3/playlistItems?part=snippet&alt=json returned "Internal error encountered.". Details: "[{'message': 'Internal error encountered.', 'domain': 'global', 'reason': 'backendError'}]">
> Traceback (most recent call last):
>   File "/home/ac/ac-training-lab/src/ac_training_lab/picam/device.py", line 109, in call_lambda
>     response.raise_for_status()
>   File "/usr/lib/python3/dist-packages/requests/models.py", line 1021, in raise_for_status
>     raise HTTPError(http_error_msg, response=self)
> requests.exceptions.HTTPError: 500 Server Error:l
> During handling of the above exception, another exception occurred:
> Traceback (most recent call last):
>   File "/home/ac/ac-training-lab/src/ac_training_lab/picam/device.py", line 134, in <module>
>     raw_body = call_lambda(
>                ^^^^^^^^^^^^
>   File "/home/ac/ac-training-lab/src/ac_training_lab/picam/device.py", line 124, in call_lambda
>     raise RuntimeError(f"HTTP error occurred: {e} - Response: {response.text}")
> RuntimeError: HTTP error occurred: 500 Server Error: Internal Server Error for url: / - Response: Error during 'create' for device 'OT2-LCM-TrainingLab': <HttpError 500 when requesting https://youtube.googleapis.com/youtube/v3/playlistItems?part=snippet&alt=json returned "Internal error encountered.". Details: "[{'message': 'Internal error encountered.', 'domain': 'global', 'reason': 'backendError'}]"> 


Unsure why it did create a stream but when inserting new stream to the playlist it returned an error to the device.py so it cannot get the stream key from the create function.

I will look into that.

---

### Comment 32 — @Neil-YL at 2025-05-21T17:16:52Z

Checked the log on the device service:

> 
> > Sending to Lambda: {'action': 'end', 'cam_name': 'cam-fb7p', 'workflow_name': 'OT2-LCM-TrainingLab', 'privacy_status': 'private'}
> > Status code: 200
> > Response text: OT2-LCM-TrainingLab ended successfully
> > Lambda 'end' succeeded: OT2-LCM-TrainingLab ended successfully
> > Sending to Lambda: {'action': 'create', 'cam_name': 'cam-fb7p', 'workflow_name': 'OT2-LCM-TrainingLab', 'privacy_status': 'public'}
> > Status code: 500
> > Response text: Error during 'create' for device 'OT2-LCM-TrainingLab': <HttpError 500 when requesting https://youtube.googleapis.com/youtube/v3/playlistItems?part=snippet&alt=json returned "Internal error encountered.". Details: "[{'message': 'Internal error encountered.', 'domain': 'global', 'reason': 'backendError'}]">
> > Traceback (most recent call last):
> > File "/home/ac/ac-training-lab/src/ac_training_lab/picam/device.py", line 109, in call_lambda
> > response.raise_for_status()
> > File "/usr/lib/python3/dist-packages/requests/models.py", line 1021, in raise_for_status
> > raise HTTPError(http_error_msg, response=self)
> > requests.exceptions.HTTPError: 500 Server Error: Internal Server Error for url: 
> > During handling of the above exception, another exception occurred:
> > Traceback (most recent call last):
> > File "/home/ac/ac-training-lab/src/ac_training_lab/picam/device.py", line 134, in 
> > raw_body = call_lambda(
> > ^^^^^^^^^^^^
> > File "/home/ac/ac-training-lab/src/ac_training_lab/picam/device.py", line 124, in call_lambda
> > raise RuntimeError(f"HTTP error occurred: {e} - Response: {response.text}")
> > RuntimeError: HTTP error occurred: 500 Server Error: Internal Server Error for url: 
 - Response: Error during 'create' for device 'OT2-LCM-TrainingLab': <HttpError 500 when requesting https://youtube.googleapis.com/youtube/v3/playlistItems?part=snippet&alt=json returned "Internal error encountered.". Details: "[{'message': 'Internal error encountered.', 'domain': 'global', 'reason': 'backendError'}]">
> 
> Unsure why it did create a stream but when inserting new stream to the playlist it returned an error to the device.py so it cannot get the stream key from the create function.
> 
> I will look into that.

Seems too frequent request of the API due to the service on the device?
https://github.com/googleapis/google-api-python-client/issues/2013#issuecomment-1363336814

-------- update------
Stopped all the systemd service on the streaming device.

Temporarily add a "try" for the inserting new video to the playlist, now the device can still receive the stream-key while the inserting error occurs. 

I will try to address the inserting error.



---

### Comment 33 — @Neil-YL at 2025-05-21T17:44:57Z

Weird that even though it returned 500 error to the device.py, it still added the new stream to the right playlist

<img width="1049" alt="Image" src="https://github.com/user-attachments/assets/7cd545f2-ccbb-4342-afc7-6b1222898cee" />

---

### Comment 34 — @Neil-YL at 2025-05-21T17:48:29Z

I will reboot all other devices to restart the stream.

---

### Comment 35 — @sgbaird at 2025-05-22T03:00:37Z

(aside: looks like the lambda function URL is in the logs you posted - maybe worth refreshing the URL or adding some mild authentication)

Get Outlook for Android<https://aka.ms/AAb9ysg>
________________________________
From: Yanghuang Liu ***@***.***>
Sent: Wednesday, May 21, 2025 1:17:14 PM
To: AccelerationConsortium/ac-training-lab ***@***.***>
Cc: Sterling Baird ***@***.***>; Author ***@***.***>
Subject: Re: [AccelerationConsortium/ac-training-lab] Prototyping the 8-hr auto-restart mechanism and stream restoration (Issue #231)

[https://avatars.githubusercontent.com/u/179746567?s=20&v=4]Neil-YL left a comment (AccelerationConsortium/ac-training-lab#231)<https://github.com/AccelerationConsortium/ac-training-lab/issues/231#issuecomment-2898689993>

Checked the log on the device service:

Sending to Lambda: {'action': 'end', 'cam_name': 'cam-fb7p', 'workflow_name': 'OT2-LCM-TrainingLab', 'privacy_status': 'private'}
Status code: 200
Response text: OT2-LCM-TrainingLab ended successfully
Lambda 'end' succeeded: OT2-LCM-TrainingLab ended successfully
Sending to Lambda: {'action': 'create', 'cam_name': 'cam-fb7p', 'workflow_name': 'OT2-LCM-TrainingLab', 'privacy_status': 'public'}
Status code: 500
Response text: Error during 'create' for device 'OT2-LCM-TrainingLab': <HttpError 500 when requesting https://youtube.googleapis.com/youtube/v3/playlistItems?part=snippet&alt=json returned "Internal error encountered.". Details: "[{'message': 'Internal error encountered.', 'domain': 'global', 'reason': 'backendError'}]">
Traceback (most recent call last):
File "/home/ac/ac-training-lab/src/ac_training_lab/picam/device.py", line 109, in call_lambda
response.raise_for_status()
File "/usr/lib/python3/dist-packages/requests/models.py", line 1021, in raise_for_status
raise HTTPError(http_error_msg, response=self)
requests.exceptions.HTTPError: 500 Server Error: Internal Server Error for url: https://u7xxb347xucah6slu7fjs5ei3q0kjnar.lambda-url.us-east-2.on.aws/
During handling of the above exception, another exception occurred:
Traceback (most recent call last):
File "/home/ac/ac-training-lab/src/ac_training_lab/picam/device.py", line 134, in
raw_body = call_lambda(
^^^^^^^^^^^^
File "/home/ac/ac-training-lab/src/ac_training_lab/picam/device.py", line 124, in call_lambda
raise RuntimeError(f"HTTP error occurred: {e} - Response: {response.text}")
RuntimeError: HTTP error occurred: 500 Server Error: Internal Server Error for url: https://u7xxb347xucah6slu7fjs5ei3q0kjnar.lambda-url.us-east-2.on.aws/ - Response: Error during 'create' for device 'OT2-LCM-TrainingLab': <HttpError 500 when requesting https://youtube.googleapis.com/youtube/v3/playlistItems?part=snippet&alt=json returned "Internal error encountered.". Details: "[{'message': 'Internal error encountered.', 'domain': 'global', 'reason': 'backendError'}]">

Unsure why it did create a stream but when listing the playlist it returned an error to the device.py so it cannot get the stream key from the create function.

I will look into that.

Seems too frequent request of the API due to the service on the device?
googleapis/google-api-python-client#2013 (comment)<https://github.com/googleapis/google-api-python-client/issues/2013#issuecomment-1363336814>

—
Reply to this email directly, view it on GitHub<https://github.com/AccelerationConsortium/ac-training-lab/issues/231#issuecomment-2898689993>, or unsubscribe<https://github.com/notifications/unsubscribe-auth/AK25ABOM4GJQ4WMIQQXHQDT27SYJVAVCNFSM6AAAAAB4A2Z2H6VHI2DSMVQWIX3LMV43OSLTON2WKQ3PNVWWK3TUHMZDQOJYGY4DSOJZGM>.
You are receiving this because you authored the thread.Message ID: ***@***.***>


---

### Comment 36 — @Neil-YL at 2025-05-22T15:15:11Z

> (aside: looks like the lambda function URL is in the logs you posted - maybe worth refreshing the URL or adding some mild authentication)
> 
> Get Outlook for Android<https://aka.ms/AAb9ysg>
> […](#)

👌 

---

### Comment 37 — @Neil-YL at 2025-05-27T00:32:26Z

> Difficult to share Lambda function directly on AWS, so instead long-term we may switch to having the lambda function on GitHub and automatically deploy to cloud via [AWS Chalice](https://aws.github.io/chalice) for example, per comment in:
> 
> https://stackoverflow.com/questions/58441717/how-to-share-lambda-function-with-another-user-in-organization

If I understand correctly:

- Create a new repo for the Lambda function in GH
- Edit Lambda scripts in this repo
- Set up AWS account credentials on GH secrets
- Commit to trigger GH action using Chalice to deploy new scripts on Lambda(?)

The only thing I need help would be the AWS credentials? I think I need an IAM user credentials within the AC organization?

BTW:
https://stackoverflow.com/questions/58441717/how-to-share-lambda-function-with-another-user-in-organization#comment103249681_58441810
> It's atypical to create an account per developer, in my experience (if by developer, you mean a single person). It's common to see prod, dev, and test accounts (possibly one set dedicated to a product, if it's large enough, but often shared). Have added to original answer.

---

### Comment 38 — @sgbaird at 2025-05-27T02:20:30Z

I'm ok with either option - pursue Chalice now (the steps you described are what I was thinking of too), or create a shared account like what was mentioned in that issue. I'll double check on AWS credentials. Not sure if I gave you admin permissions.

---

### Comment 39 — @Neil-YL at 2025-05-27T05:48:02Z

I thought the IAM user credentials is something other than our personal accounts, like an IAM user for the Lambda deployment with Chalice.

---

### Comment 40 — @sgbaird at 2025-05-27T12:38:44Z

@Neil-YL - started the process. Looks like [`AWSLambda_FullAccess` might be the necessary policy to attach](https://docs.aws.amazon.com/lambda/latest/dg/access-control-identity-based.html).

This is where I went for creating an IAM user: https://us-east-1.console.aws.amazon.com/iam/home?region=us-east-2#/users based on instructions in https://docs.aws.amazon.com/IAM/latest/UserGuide/id_users_create.html.

Going with access key so it doesn't expire.

![Image](https://github.com/user-attachments/assets/0feaa3de-a86c-442d-8166-26a30a5244e8)

Shared the credentials with you privately.

---

### Comment 41 — @Neil-YL at 2025-05-27T14:45:11Z

Not sure if the IAM user also needs the permit to visit S3 (for the pickle token) or there is a better practice. I will look into this while preparing the other setup for the shared managed Lambda.

---

### Comment 42 — @sgbaird at 2025-05-28T16:06:17Z

Seems more complicated than I realized. Created [a new issue](https://github.com/AccelerationConsortium/ac-training-lab/issues/271) specific to Chalice. 

---

### Comment 43 — @sgbaird at 2025-05-31T15:34:53Z

The 8 hour restart seems to be working quite well. Frequently, the stream only has a minute of downtime for the 8 hour chunks.

---

### Comment 44 — @sgbaird at 2025-07-17T21:38:04Z

@Neil-YL sorry to bother.. I'm having trouble finding out where the 8-hr restart mechanism is. The crontab from https://ac-training-lab.readthedocs.io/en/latest/devices/picam.html#automatic-startup shows only at 2 am. When I look around in https://github.com/AccelerationConsortium/streamingLambda and https://github.com/AccelerationConsortium/ac-training-lab/blob/main/src/ac_training_lab/picam/device.py, I'm not seeing the logic implemented there either (maybe I missed it?).

---

### Comment 45 — @Neil-YL at 2025-07-19T04:13:37Z

`sudo crontab` 

and add:

`0 5,13,21 * * * /sbin/shutdown -r now`

---
