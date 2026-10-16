# Transition2CS — free-only Wan 2.2 cloud-to-YouTube workflow

## Status and safeguards

**Not deployed, not authorized, not publishing.** This is an integration scaffold, not a guarantee that Wan2.2 can complete on free ZeroGPU. GitHub Actions invokes an existing or separately-deployed compatible Hugging Face Gradio Space. `UPLOAD_ENABLED` must explicitly equal `true` or the job does nothing. The uploader checks the **actual authenticated channel ID** before upload. Upload visibility is **public**, and AI-generated material is disclosed.

### 1. Hugging Face (free-only)

1. Create/log in at https://huggingface.co. Confirm ZeroGPU eligibility at https://huggingface.co/docs/hub/spaces-zerogpu . An eligible free account can create up to two ZeroGPU Spaces; new accounts may have to wait until age 30 days.
2. Create a private Gradio Space named `transition2cs-wan22`, ZeroGPU hardware ONLY. **Do not select a paid GPU.**
3. Obtain/implement a Wan2.2 TI2V-5B Gradio implementation that successfully runs on the shared ZeroGPU time quota (currently 5 min/day). Source model: https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B . This is the unresolved step: the official Wan2.2 inference scripts are not a working ZeroGPU Gradio app out-of-the-box. Initializing/checkpoint download and runtime limits can prevent success. Do not assume a third-party public Space API is stable or permissible for unattended daily usage.
4. The Space must expose a Gradio API endpoint `/generate` with parameter `prompt` returning an mp4 file. Set repository variable `HF_SPACE_ID` to `<hf-username>/transition2cs-wan22` and save a read-access Hugging Face token as secret `HF_TOKEN`.
5. **Test one run manually before enabling uploads.** If free quotas cannot generate an MP4, daily Wan generation is not feasible at ₹0 on this service.

### 2. Google YouTube OAuth (one-time sign-in needed)

1. Sign in at https://console.cloud.google.com/ as **pybrush01@gmail.com**. Create a cloud project, enable **YouTube Data API v3**. Do NOT enable billable resources or a paid billing account.
2. Create OAuth consent configuration and a **Desktop app** OAuth client. Grant YouTube upload and readonly scopes. Make sure any OAuth-app verification/testing constraints and refresh-token lifetime are addressed: an External Testing-mode refresh token often expires after 7 days.
3. Perform an interactive local/browser OAuth authorization using a trusted OAuth tool. Consent on the correct **Transition2CS** YouTube identity. Do not put passwords, client secrets or refresh tokens into chat or GitHub files. A durable refresh token must be obtained with `access_type=offline` and stored only as an Actions secret. This step **cannot be completed automatically from ChatGPT** without YouTube OAuth permission.
4. Store encrypted repository secrets `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_REFRESH_TOKEN`. In repository variables, set `YOUTUBE_CHANNEL_ID` to Transition2CS's verified channel **ID** (not name or Gmail address).
5. Google may restrict videos inserted through unverified API projects or require an API compliance audit. Verify current channel/project restrictions before relying on public publication. If blocked, uploads may remain private despite your public setting.

### 3. GitHub Actions (schedule)

1. Create a separate **private** repository named `transition2cs-automation` in GitHub. Upload this project's `.github/workflows/daily.yml`, `publish.py` and `requirements.txt` preserving paths. Verify Actions are enabled.
2. Set GitHub **Actions secrets** as above and `HF_TOKEN`; set Actions **variables**: `HF_SPACE_ID`, `YOUTUBE_CHANNEL_ID`, `UPLOAD_ENABLED=false` initially.
3. Open Actions > `Transition2CS daily Wan upload` > Run workflow; while disabled it only logs that upload is disabled.
4. Complete successful Space inference and OAuth connection, then set `UPLOAD_ENABLED=true`. Run the workflow manually once; note that it publishes a **public video** if generation succeeds and OAuth check matches.
5. The scheduled cron `30 12 * * *` is 12:30 UTC, i.e. **18:00 IST** daily. GitHub cron start may be delayed and jobs are not guaranteed to run precisely at 18:00.

### Important limitations

- Strict ₹0 is enforced by choosing free-only resources, but it cannot guarantee **daily free Wan 2.2 video generation** or guaranteed daily YouTube publishing.
- Github Actions scheduled workflow does not itself supply GPU hardware. Generation occurs at the Space; GitHub just calls it.
- If enabled, retries following ambiguous upload network failures could cause duplicate uploads; this starter has no persistent idempotency ledger. Keep disabled until a production duplication safeguard is added.
- True 9:16/YouTube Short compatibility requires the Space to produce a vertical MP4. The scaffold requests vertical composition, but does not verify width/height. Verify output manually before public automation.
- There are no auto-generated narration/captions, no quality review, and scripts do not claim otherwise.
