#!/bin/bash

# Update package list
sudo apt update

# Install UFW if not already installed
sudo apt install -y ufw

# Reset to a clean state
sudo ufw reset

# Default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow essential services
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https

# Enable logging
sudo ufw logging on

# Enable firewall
sudo ufw enable

# Show status
sudo ufw status verbose
