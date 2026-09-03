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
