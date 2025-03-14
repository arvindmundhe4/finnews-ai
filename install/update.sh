#!/bin/bash

# FinNews AI Update Script
# This script updates an existing FinNews AI installation

# Text colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default paths
INSTALL_PATH="/var/python/finnews"
VENV_PATH="${INSTALL_PATH}/venv"

# Print header
echo -e "\n${GREEN}=================================================${NC}"
echo -e "${GREEN}          FinNews AI Update Script          ${NC}"
echo -e "${GREEN}=================================================${NC}\n"

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
    echo -e "${RED}Error: This script must be run as root${NC}" 
    echo -e "Please run with: sudo bash update.sh"
    exit 1
fi

# Check if installation exists
if [ ! -d "$INSTALL_PATH" ] || [ ! -d "$INSTALL_PATH/.git" ]; then
    echo -e "${RED}Error: FinNews AI installation not found at $INSTALL_PATH${NC}"
    echo -e "Please run the installation script first."
    exit 1
fi

# Stop the service
echo -e "${YELLOW}Stopping FinNews AI service...${NC}"
systemctl stop finnews

# Backup current .env file
echo -e "${YELLOW}Backing up environment configuration...${NC}"
if [ -f "$INSTALL_PATH/finnews/.env" ]; then
    cp "$INSTALL_PATH/finnews/.env" "$INSTALL_PATH/finnews/.env.backup"
fi

# Pull latest changes
echo -e "${YELLOW}Pulling latest changes from repository...${NC}"
cd $INSTALL_PATH
git pull

# Update dependencies
echo -e "${YELLOW}Updating Python dependencies...${NC}"
source $VENV_PATH/bin/activate
cd $INSTALL_PATH/finnews
pip install --upgrade pip
pip install -r requirements.txt

# Restore .env file
echo -e "${YELLOW}Restoring environment configuration...${NC}"
if [ -f "$INSTALL_PATH/finnews/.env.backup" ]; then
    cp "$INSTALL_PATH/finnews/.env.backup" "$INSTALL_PATH/finnews/.env"
fi

# Set permissions
echo -e "${YELLOW}Setting permissions...${NC}"
chown -R www-data:www-data $INSTALL_PATH
chmod -R 755 $INSTALL_PATH

# Restart service
echo -e "${YELLOW}Starting FinNews AI service...${NC}"
systemctl start finnews

# Update complete
echo -e "\n${GREEN}=================================================${NC}"
echo -e "${GREEN}        FinNews AI Update Complete!         ${NC}"
echo -e "${GREEN}=================================================${NC}"
echo -e "\nYou can now access your updated FinNews AI instance at your domain."
echo -e "To check the service status: ${YELLOW}systemctl status finnews${NC}"
echo -e "To view logs: ${YELLOW}journalctl -u finnews${NC}\n"
