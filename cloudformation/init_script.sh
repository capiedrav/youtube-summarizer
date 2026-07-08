#!/bin/bash
set -e

STACK_NAME=$1
REGION=$2

# 1. Update and install cfn-bootstrap tools
apt-get update -y
apt-get install -y python3-pip
pip3 install https://s3.amazonaws.com/cloudformation-examples/aws-cfn-bootstrap-py3-latest.tar.gz

# 2. Signal cfn-init to process metadata packages (git, curl, etc.)
/usr/local/bin/cfn-init -v --stack "${STACK_NAME}" --resource DebianInstance --region "${REGION}"

# 3. Configure /home Volume (/dev/xvdb is ready immediately)
if ! blkid /dev/xvdb; then
  mkfs.ext4 /dev/xvdb
fi
mkdir -p /mnt/home_tmp
mount /dev/xvdb /mnt/home_tmp
rsync -aHAXx /home/ /mnt/home_tmp/
umount /mnt/home_tmp
mount /dev/xvdb /home
echo "/dev/xvdb /home ext4 defaults,nofail 0 2" >> /etc/fstab

# 4. Configure Swap Volume (/dev/xvdc is ready immediately)
mkswap /dev/xvdc
swapon /dev/xvdc
echo "/dev/xvdc none swap sw 0 0" >> /etc/fstab

# 5. Install Docker Engine
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
systemctl enable docker
systemctl start docker

# 6. Signal back to CloudFormation instance resource directly
/usr/local/bin/cfn-signal -e $? --stack "${STACK_NAME}" --resource DebianInstance --region "${REGION}"