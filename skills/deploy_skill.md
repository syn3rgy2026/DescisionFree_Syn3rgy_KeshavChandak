# Deploy & GitHub Skill

## Description

This skill enables the agent to push code to GitHub and deploy projects to Vercel.
Both tools handle authentication automatically — they open the browser for OAuth login if needed.
**No credentials are stored by the agent** — all auth is managed by the GitHub CLI and Vercel CLI.

## Available Tools

### GitHub Tools
- **`github_create_and_push(project_dir, repo_name, private=False, description="")`**
  Creates a new GitHub repo and pushes code. Opens browser for login if not authenticated.
- **`github_push(project_dir, message="Update", branch="main")`**
  Commits and pushes changes to an existing repo.
- **`github_clone(repo_url, target_dir="")`**
  Clones a repository.
- **`github_status()`**
  Check current GitHub authentication status — shows username and auth method.
- **`github_logout()`**
  Log out of GitHub CLI. Clears stored credentials so you can switch accounts.

### Vercel Tools
- **`vercel_login()`**
  Proactively log into Vercel CLI. Opens browser for OAuth. Not required before deploy (deploy handles it automatically).
- **`vercel_logout()`**
  Log out of Vercel CLI. Clears stored credentials.
- **`vercel_deploy(project_dir, production=False)`**
  Deploys to Vercel. Opens browser for login if not authenticated. Opens the live URL after deploy.
- **`vercel_status(project_dir)`**
  Shows recent deployments.
- **`vercel_env_set(project_dir, key, value)`**
  Sets environment variables on Vercel.

## Trigger Conditions

Use this skill when the user says any of:
- "deploy", "push", "publish", "host", "launch"
- "github", "git", "repo", "repository"
- "vercel", "put it online", "make it live"
- "login", "logout", "auth", "credentials", "switch account"

## Instructions — FOLLOW THIS EXACT ORDER

### When user says "deploy" or "put it on Vercel":
```python
# Step 1: Create GitHub repo FIRST
github_create_and_push(project_dir="output/myapp", repo_name="myapp", description="My app")

# Step 2: Deploy to Vercel (preview first)
vercel_deploy(project_dir="output/myapp", production=False)

# Step 3: If preview looks good, deploy to production
vercel_deploy(project_dir="output/myapp", production=True)
```

### When user says "push to github" or "create repo":
```python
github_create_and_push(project_dir="output/myapp", repo_name="myapp")
```

### When user says "update" or "push changes":
```python
github_push(project_dir="output/myapp", message="Updated feature X")
```

### When user says "check github login" or "am I logged in":
```python
github_status()
```

### When user says "logout" or "switch github account":
```python
github_logout()
# Next time a GitHub tool runs, it will prompt for re-authentication
```

### When user says "login to vercel" or "set up vercel":
```python
vercel_login()
```

## CRITICAL RULES

1. **ALWAYS create a GitHub repo when deploying.** Do NOT skip this step.
2. **NEVER say "I don't have access to credentials"** — the tools handle login automatically via browser OAuth.
3. **ALWAYS do preview deploy first**, then production after verifying.
4. **ALWAYS verify the deployment** using `browser_navigate` or `browser_screenshot` after deploying.
5. `ask_human_confirmation` is already built into the deploy tools — no need to call it separately.
6. **Authentication is interactive** — when login is triggered, the user sees prompts directly in their terminal and a browser window opens for OAuth authorization.
7. **No credentials are stored by the agent** — auth tokens are managed by `gh` CLI and `vercel` CLI respectively.

## Output Format

Always include in your final answer:
- GitHub repo URL (if created)
- Vercel deployment URL
- Verification screenshot path
