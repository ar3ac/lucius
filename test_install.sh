#!/bin/bash
apt-get update && apt-get install -y sudo curl git
mkdir -p /home/user
useradd -m -d /home/user -s /bin/bash user
echo "user ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
su - user -c "curl -sSL https://raw.githubusercontent.com/ar3ac/lucius/main/install.sh > install.sh; chmod +x install.sh"
# wait, the repo in github might not have the fixes I just made!
