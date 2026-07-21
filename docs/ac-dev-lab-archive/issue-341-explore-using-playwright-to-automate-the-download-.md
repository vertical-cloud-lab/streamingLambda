# Issue #341: Explore using playwright to automate the download of new videos

- **URL:** https://github.com/AccelerationConsortium/ac-dev-lab/issues/341
- **Author:** @sgbaird
- **State:** closed
- **Created:** 2025-06-20T18:29:26Z  **Closed:** 2025-08-01T15:22:17Z
- **Comments archived:** 1 issue comments

---

## Original description

> Another option we could consider is using [playwright](https://playwright.dev/python/) (I've been using the MCP server for it at times, saw it listed on one of GitHub's tutorials as an example MCP) and having it login and go directly to the download button on the YouTube UI for the various videos.
> 
> I'm not sure if playwright could handle that, but maybe worth a shot (either for automatically retrieving cookies or for navigating to YouTube's built-in download link for self-owned videos). 

 _Originally posted by @sgbaird in [#223](https://github.com/AccelerationConsortium/ac-training-lab/issues/223#issuecomment-2953314650)_

This would involve using a fresh Google account with access to the ac-hardware-streams channel (I can supply), passing in the credentials to playwright to be able to login and click the "download" button for various videos

cc @zweaung1014 



---

## Comments (complete, in chronological order)

### Comment 1 — @sgbaird at 2025-06-20T21:38:50Z

I made an assignment to copilot agent so you can see an example of what my usage of the playwright MCP has been like. I don't know if this is the right tool for doing the downloading or getting the cookies, especially considering that it might be a disallowed tool from a bot perspective.

https://github.com/AccelerationConsortium/ac-training-lab/actions/runs/15788239612/job/44509152107

---
