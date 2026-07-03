

## Repository-specific instructions

- Keep changes minimal and lean.

## Tailscale SSH

- If a task depends on SSH access and it is not working, stop and report back instead of committing speculative changes.
- Make sure the runner is on the tailnet first. This repo already wires that up in `.github/workflows/copilot-setup-steps.yml` with `tailscale/github-action@v2`.
- Connect from a terminal:

   ```bash
   ssh -o ConnectTimeout=20 -o StrictHostKeyChecking=no "${RPI_STREAM_CAM_USERNAME}@${RPI_STREAM_CAM_HOSTNAME}.${TAILNET_ID}.ts.net"
   ```

- If the SSH flow prints a Tailscale login URL, send that URL to the user and wait for them to complete the auth step.
- Do not hardcode hostnames, API keys, or other secrets. Use environment variables and never print secret values.
