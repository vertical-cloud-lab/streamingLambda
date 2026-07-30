# YouTube Streaming Lambda Function (deployed via Chalice)

This repository deploys an AWS Lambda function using [AWS Chalice](https://github.com/aws/chalice) for automatic YouTube livestream creation and management from [monitoring device](https://ac-training-lab.readthedocs.io/en/latest/devices/picam.html).

## Video orientation and resolution

The Lambda creates YouTube live streams with `"resolution": "variable"` and `"frameRate": "variable"` (see `chalicelib/ytb_api_utils.py`), so YouTube accepts whatever dimensions the device sends — including portrait (9:16) video, which YouTube preserves without letterboxing or cropping. Resolution, frame rate, and rotation are therefore configured on the device itself in `my_secrets.py` (`RESOLUTION`, `FRAME_RATE`, `CAMERA_ROTATION`), used by `device.py` in the [ac-training-lab picam setup](https://ac-training-lab.readthedocs.io/en/latest/devices/picam.html). For a physically rotated (portrait) camera, the device captures full-field-of-view landscape frames and rotates them in ffmpeg (`transpose`), which avoids the sensor cropping that occurs if portrait dimensions are requested from libcamera directly.

### Sensor mode and field of view

Even with landscape capture, libcamera may auto-select a center-cropped sensor mode for small output sizes, silently losing field of view. On the imx708 (Camera Module 3), a 1280x720 request picks the 1536x864 sensor mode, which covers only the central ~44% of the sensor area (~2x zoom); the 2x2-binned 2304x1296 mode covers the full sensor. `device.py` supports an optional `SENSOR_MODE` setting in `my_secrets.py` (e.g. `SENSOR_MODE = "2304:1296"`), passed to `rpicam-vid` as `--mode`, to force the full-field-of-view mode. List a camera's modes with `rpicam-vid --list-cameras`.
