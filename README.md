<h1>LibreChat for Business Finland</h1>
LibreChat for Business Finland is an AI Chat app. 
It is forked from Danny Avila's open-source project<a href="https://github.com/danny-avila/LibreChat"> LibreChat</a>.

<h2>Technical documentation</h2>
Documentation about the project and the usage of the chat is found in Business Finland's Confluence.
- <a href="https://businessfinland.atlassian.net/wiki/spaces/CHAT/overview">Confluence</a>

<h2>GitHub</h2>
Project is split into two repositories, one for the application itself and one custom-made for the infrastructure. 
They are found in Business Finland's GitHub page.  
- <a href="https://github.com/BusinessFinland/libre-chat-app">LibreChat App</a>
- <a href="https://github.com/BusinessFinland/libre-chat-infra">LibreChat Infra</a>

<h2>Upgrading LibreChat through fork through merging</h2>
Often rebasing is the way to go. However, in this case it would cause a lot more work, so it's suggested to merge the
changes instead. And while it'd be the easiest for the future to get a fork from upstream and just squash all our 
changes over that in one commit, it's best not to overwrite our branch history to avoid merge conflict mistakes nuking 
the personalisations. 

1. Create a branch from main (or any branch you want to merge the upgrade to)
   - This is "optional", but suggested to let a co-worker look through Pull Request before merging
2. Get upstream branches from the project fork
   - `git remote add upstream https://github.com/danny-avila/LibreChat.git`
3. Choose the branch/commit you want to take the fork from
4. Merge the chosen branch/commit to your new branch 
5. Solve all merge conflicts
   - Confluence has documentation on all changes we've made for our project file by file and reasons for them
   - Remember to keep this README.md as well!
   - In case of removed files (such as workflows etc.) use your own judgment. If they were removed earlier, they are 
     likely not important now either
6. Test the application in your local environment and see that all works as planned. Fix bugs caused by merge if needed.
7. Set `"version"` in `.github/upstream.json` to the release you merged.
8. Commit the branch to origin and create a PR for co-worker to go through
9. Merge the PR with **"Create a merge commit"**, never squash. A squash leaves upstream's history out of `main`, so
   git no longer knows the release was merged, and the next upgrade conflicts again on everything resolved here.

<h3>Upstream autopilot</h3>

`.github/workflows/upstream.yml` does the steps above for each new LibreChat release (modelled on Vimma's autopilot):
it checks upstream daily, opens a tracking issue per release (labelled `security` when the release fixes a published
advisory that affects our version), and merges the release into `main` on a branch. A clean merge becomes the PR
`upstream/librechat-vX.Y.Z`, tested by CI. A merge with conflicts becomes a `triage` issue listing the files and the
commands above. It also opens a drift issue and fails when we fall too far behind (`tools/upstream/detect.py`).

`.github/upstream.json` records the release `main` is merged up to.

For the PR to start CI on its own, the autopilot needs a GitHub App with contents, pull requests and issues write on
this repository: set the repository variable `UPSTREAM_APP_CLIENT_ID` and the secret `UPSTREAM_APP_KEY`. Without
them it opens the PR as a draft with `GITHUB_TOKEN`, and CI starts when someone pushes to the branch.

Every file we change is a merge conflict on each upgrade. Prefer configuration (`librechat.yaml`, environment
variables) or an upstream contribution over a code change, and keep the remaining changes small.