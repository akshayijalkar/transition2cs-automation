# Transition2CS · Wan 2.2 → YouTube Shorts

**Target:** one public Short each day at 18:00 Asia/Kolkata, using strictly free-tier resources.

## Status: NOT LIVE
The scheduled workflow is intentionally blocked until a tested Wan 2.2 ZeroGPU Space, OAuth refresh token, and repository secrets are configured. A cloud GPU with enough VRAM is not necessarily fast enough for a 5-minute/day free quota. The system must never use paid hardware.

## Required GitHub repository secrets
- `HF_TOKEN`: Hugging Face personal access token with minimum required permissions.
- `HF_SPACE`: full Gradio Space name, e.g. `yourname/transition2cs-wan22`. **Must implement the /generate endpoint taking a single text prompt and returning a downloadable video file.**
- `GOOGLE_CLIENT_ID`: YouTube OAuth desktop/web app client ID.
- `GOOGLE_CLIENT_SECRET`: corresponding OAuth secret.
- `GOOGLE_REFRESH_TOKEN`: long-lived refresh token authorized for https://www.googleapis.com/auth/youtube.upload on the correct YouTube channel.
- `AUTOMATION_ENABLED`: set to `true` only after manually verifying the Space, output and channel.

## Safeguards
- GitHub Actions uses an explicit timeout and no paid runners.
- Job exits without uploading if any secret is missing.
- Video output is checked before uploading.
- Public uploads require explicit `AUTOMATION_ENABLED=true`.
- Each day is given a unique topic; GitHub concurrency reduces overlaps. Duplicate uploads should be independently verified if a failed upload retry might have succeeded.
- YouTube account must be identified as Transition2CS during manual OAuth setup; the email address alone cannot select a channel.

## Setup
1. Sign in at https://huggingface.co/new-space and check ZeroGPU eligibility. Free accounts need a verified email and account age >30 days.
2. Deploy and **test** a Gradio Wan 2.2 Space with `/generate` accepting a single prompt and returning a video file. This repo does NOT contain a confirmed running Wan 2.2 Space; do not enable the workflow before testing.
3. In https://console.cloud.google.com/ enable YouTube Data API v3, configure OAuth, and authorize `youtube.upload` for Transition2CS. Keep OAuth consent app in appropriate production status to avoid temporary 7-day testing refresh-token expiry. Depending on Google policies/API verification, publication restrictions may apply.
4. Set all GitHub secrets above, then invoke workflow_dispatch once for a private test by temporarily changing `YOUTUBE_PRIVACY` to `private`. Inspect the result.
5. After confirming the channel and free video generation, set privacy back to public, then set `AUTOMATION_ENABLED=true`.

**Schedule:** 12:30 UTC is 18:00 IST, daily. GitHub scheduled workflow runs can be delayed or missed under load.
**Cost:** No payment is authorized; if free-tier resources are insufficient, generation fails/skips.
