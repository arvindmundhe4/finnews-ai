# FinNews AI Installation Guide

This directory contains scripts and configurations for installing FinNews AI on an Ubuntu server with Nginx and systemd.

## Prerequisites

- An Ubuntu server (preferably Ubuntu 20.04 LTS or later)
- A domain name pointing to your server (default: fin.marketcalls.in)
- Root or sudo access to the server
- OpenAI API key

## Installation Steps

1. Upload the contents of this directory to your server.

2. Make the install script executable:
   ```bash
   chmod +x install.sh
   ```

3. Run the installation script as root:
   ```bash
   sudo ./install.sh
   ```

4. Follow the prompts to enter your domain name and OpenAI API key.

5. The script will:
   - Install required system packages
   - Clone the FinNews AI repository to `/var/python/finnews/`
   - Set up a Python virtual environment at `/var/python/finnews/venv/`
   - Install Python dependencies
   - Configure Nginx as a reverse proxy
   - Set up Let's Encrypt SSL certificates
   - Create and start a systemd service

6. Once completed, your FinNews AI instance will be available at `https://your-domain.com`

## Manual Configuration

If you prefer to install manually or need to troubleshoot, here are the key files created by the script:

- **Environment Variables**: `/var/python/finnews/finnews/.env`
- **Systemd Service**: `/etc/systemd/system/finnews.service`
- **Nginx Configuration**: `/etc/nginx/sites-available/finnews`

## Management Commands

- Check service status:
  ```bash
  systemctl status finnews
  ```

- View logs:
  ```bash
  journalctl -u finnews
  ```

- Restart the service:
  ```bash
  systemctl restart finnews
  ```

- Reload Nginx:
  ```bash
  systemctl reload nginx
  ```

## Troubleshooting

1. **Service won't start**: Check logs with `journalctl -u finnews`
2. **Nginx issues**: Check configuration with `nginx -t`
3. **SSL problems**: Run `certbot --nginx -d your-domain.com` manually

## Support

For support, please open an issue on the GitHub repository:
[https://github.com/marketcalls/finnews-ai](https://github.com/marketcalls/finnews-ai)
