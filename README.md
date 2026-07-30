# YouTube Streaming Lambda Function (deployed via Chalice)

This repository deploys an AWS Lambda function using [AWS Chalice](https://github.com/aws/chalice) for automatic YouTube livestream creation and management from [monitoring device](https://ac-training-lab.readthedocs.io/en/latest/devices/picam.html).

## Video orientation and resolution

The Lambda creates YouTube live streams with `"resolution": "variable"` and `"frameRate": "variable"` (see `chalicelib/ytb_api_utils.py`), so YouTube accepts whatever dimensions the device sends — including portrait (9:16) video, which YouTube preserves without letterboxing or cropping. Resolution, frame rate, and rotation are therefore configured on the device itself in `my_secrets.py` (`RESOLUTION`, `FRAME_RATE`, `CAMERA_ROTATION`), used by `device.py` in the [ac-training-lab picam setup](https://ac-training-lab.readthedocs.io/en/latest/devices/picam.html). For a physically rotated (portrait) camera, the device captures full-field-of-view landscape frames and rotates them in ffmpeg (`transpose`), which avoids the sensor cropping that occurs if portrait dimensions are requested from libcamera directly.
