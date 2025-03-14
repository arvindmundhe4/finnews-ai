#!/bin/bash

# FinNews AI Installation Script
# This script will install FinNews AI on an Ubuntu server with Nginx and systemd

# Text colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default values
DEFAULT_DOMAIN="fin.marketcalls.in"
INSTALL_PATH="/var/python/finnews"
VENV_PATH="${INSTALL_PATH}/venv"
GITHUB_REPO="https://github.com/marketcalls/finnews-ai.git"

# Print header
echo -e "\n${GREEN}=================================================${NC}"
echo -e "${GREEN}       FinNews AI Installation Script       ${NC}"
echo -e "${GREEN}=================================================${NC}\n"

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
    echo -e "${RED}Error: This script must be run as root${NC}" 
    echo -e "Please run with: sudo bash install.sh"
    exit 1
fi

# Prompt for domain
read -p "Enter your domain name [default: ${DEFAULT_DOMAIN}]: " DOMAIN
DOMAIN=${DOMAIN:-$DEFAULT_DOMAIN}
echo -e "${GREEN}Using domain: ${DOMAIN}${NC}\n"

# Prompt for OpenAI API key
read -p "Enter your OpenAI API key: " OPENAI_API_KEY
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${RED}Error: OpenAI API key is required${NC}"
    exit 1
fi

# Install required system packages
echo -e "${YELLOW}Installing system dependencies...${NC}"
apt update
apt install -y python3 python3-venv python3-pip nginx certbot python3-certbot-nginx sqlite3 git curl

# Create installation directory
echo -e "${YELLOW}Creating installation directory...${NC}"
mkdir -p $INSTALL_PATH
if [ -d "$INSTALL_PATH/.git" ]; then
    echo -e "${YELLOW}Git repository already exists. Pulling latest changes...${NC}"
    cd $INSTALL_PATH
    git pull
else
    echo -e "${YELLOW}Cloning repository from GitHub...${NC}"
    git clone $GITHUB_REPO $INSTALL_PATH
fi

# Navigate to the installation directory
cd $INSTALL_PATH

# Create and activate virtual environment
echo -e "${YELLOW}Setting up Python virtual environment...${NC}"
python3 -m venv $VENV_PATH
source $VENV_PATH/bin/activate

# Install Python dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
cd $INSTALL_PATH/finnews
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

# Create .env file
echo -e "${YELLOW}Creating environment file...${NC}"
cat > $INSTALL_PATH/finnews/.env << EOL
OPENAI_API_KEY=${OPENAI_API_KEY}
DATABASE_URL=sqlite://${INSTALL_PATH}/finnews/database.sqlite
EOL

# Create systemd service file
echo -e "${YELLOW}Creating/updating systemd service...${NC}"
if [ -f "/etc/systemd/system/finnews.service" ]; then
    echo -e "${YELLOW}Existing systemd service found. Overwriting...${NC}"
fi
cat > /etc/systemd/system/finnews.service << EOL
[Unit]
Description=FinNews AI Service
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=${INSTALL_PATH}/finnews
Environment="PATH=${VENV_PATH}/bin"
ExecStart=${VENV_PATH}/bin/gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker --bind unix:${INSTALL_PATH}/finnews.sock
Restart=always
RestartSec=5
SyslogIdentifier=finnews

[Install]
WantedBy=multi-user.target
EOL

# Create Nginx configuration
echo -e "${YELLOW}Creating/updating Nginx configuration...${NC}"
if [ -f "/etc/nginx/sites-available/finnews" ]; then
    echo -e "${YELLOW}Existing Nginx configuration found. Overwriting...${NC}"
fi
cat > /etc/nginx/sites-available/finnews << EOL
server {
    listen 80;
    server_name ${DOMAIN};

    location / {
        proxy_pass http://unix:${INSTALL_PATH}/finnews.sock;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$host;
        proxy_set_header X-Forwarded-Port \$server_port;
        proxy_buffering off;
    }
}
EOL

# Enable the site and restart Nginx
echo -e "${YELLOW}Enabling Nginx site...${NC}"
ln -sf /etc/nginx/sites-available/finnews /etc/nginx/sites-enabled/
nginx -t && systemctl restart nginx

# Set permissions
echo -e "${YELLOW}Setting permissions...${NC}"
chown -R www-data:www-data $INSTALL_PATH
chmod -R 755 $INSTALL_PATH

# Enable and start the service
echo -e "${YELLOW}Starting FinNews AI service...${NC}"
systemctl enable finnews
systemctl start finnews

# Configure Let's Encrypt
echo -e "${YELLOW}Setting up SSL with Let's Encrypt...${NC}"
certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN --redirect

# Installation complete
echo -e "\n${GREEN}=================================================${NC}"
echo -e "${GREEN}       FinNews AI Installation Complete!        ${NC}"
echo -e "${GREEN}=================================================${NC}"
echo -e "\nYou can now access your FinNews AI instance at: ${GREEN}https://${DOMAIN}${NC}"
echo -e "To check the service status: ${YELLOW}systemctl status finnews${NC}"
echo -e "To view logs: ${YELLOW}journalctl -u finnews${NC}"
echo -e "\nIf you encounter any issues, please check the logs or visit:"
echo -e "${GREEN}https://github.com/marketcalls/finnews-ai${NC}\n"
