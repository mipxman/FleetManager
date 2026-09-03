# FleetManager
Easy WEB-APP To manage company's cars


## Install Docker dependcies on your Server
apt-get update && apt-get install -y ca-certificates curl gnupg


install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc



apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin



docker compose up -d --build




docker compose down
rm -rf database.db
touch database.db


docker compose up -d --build



docker ps -a 


docker logs 
