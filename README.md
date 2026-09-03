# FleetManager

A lightweight, containerized web application built with Python (Flask), SQLite, and Bootstrap 5 to manage company vehicle check-outs, returns, and driver logs.

---

## Key Features

* **Role-Based Access:** Distinct portals for **Admin** and **Normal Users**.
* **Fleet Management:** Add/remove vehicles with odometer tracking and photo uploads.
* **Driver Check-Out/In:** Select vehicles, record mileage, and add trip destination notes.
* **Reporting:** View trip histories with local timestamps (Europe/Rome) and export data to CSV or HTML formats.
* **Multi-Language Support:** Instant runtime UI toggle between English (EN) and Italian (IT).
* **Mobile Responsive:** Card-based UI optimized for mobile browsers and tablets.

---

## Tech Stack

* **Backend:** Python (Flask, Flask-SQLAlchemy, Flask-Login, Pandas, PyTZ)
* **Frontend:** HTML5, Bootstrap 5, JavaScript (i18n client-side translation)
* **Database:** SQLite
* **Containerization:** Docker & Docker Compose

---

## Prerequisites & Installation

### 1. Install Docker Dependencies on Linux (Ubuntu/Debian)

```bash
# Update package list and install system prerequisites
apt-get update && apt-get install -y ca-certificates curl gnupg

# Add Docker's official GPG key
install -m 0755 -d /etc/apt/keyrings
curl -fsSL [https://download.docker.com/linux/ubuntu/gpg](https://download.docker.com/linux/ubuntu/gpg) -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc

# Install Docker Engine and Docker Compose Plugin
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

```
### 2. CI/CD pipeline steps 
#### Step 1: Generate an SSH Key Pair for GitHub
Open the terminal on your server (A.B.C.D) and generate a dedicated deployment key:
```bash
ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/github_deploy -N ""
```
Add the public key to your server's authorized keys list:
```bash
cat ~/.ssh/github_deploy.pub >> ~/.ssh/authorized_keys
```

Display the private key and copy the entire output (including -----BEGIN OPENSSH PRIVATE KEY----- and -----END OPENSSH PRIVATE KEY-----):
```bash
cat ~/.ssh/github_deploy
```

#### Step 2: Add Secrets to Your GitHub Repository
1.Go to your repository on GitHub (GithubPROFILE/FleetManager).

2.Click Settings > Secrets and variables > Actions.

3. Click New repository secret and add the following three secrets:

| Secret Name | Value | 
|-------------|-------|
|SERVER_HOST  | A.B.C.D|
|SERVER_USER |  $USER | 
|SSH_PRIVATE_KEY| (Paste the private key copied in Step 1)|

#### Step 3: Create the GitHub Actions Workflow File
On your PC (or via VS Code), create a new file in your repository at this exact path:
`.github/workflows/deploy.yml`

Paste the following workflow configuration:
```bash
name: Deploy FleetManager to Server

on:
  push:
    branches:
      - main  # Triggers deployment when pushing to the main branch

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Deploying to Remote Server via SSH
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            # Navigate to project directory
            cd ~/car-management-app || cd ~/FleetManager

            # Pull latest changes from GitHub
            git pull origin main

            # Rebuild and restart containers
            docker compose up -d --build
```
#### Step 4: Clone the Repo on the Server (One-Time Setup)
Ensure your project directory on the server is a valid Git repository connected to GitHub:
```bash
cd ~
# If your project isn't linked to git yet, clone it into place:
git clone https://github.com/mipxman/FleetManager.git ~/FleetManager
```

How to Test It

1. Edit any file locally on your PC (e.g., change a text label in templates/base.html).

2. Commit and push your changes to GitHub:

```bash
git add .
git commit -m "Updated translation labels"
git push origin main
```
