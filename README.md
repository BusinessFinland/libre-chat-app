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
7. Commit the branch to origin and create a PR for co-worker to go through
8. (Optional, but highly suggested) when merging the PR, use squash and merge to not completely destroy our git tree. 