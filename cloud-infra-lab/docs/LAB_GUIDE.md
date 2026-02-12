# Cloud Infrastructure Lab Guide

A comprehensive, step-by-step walkthrough for building cloud infrastructure from scratch.

---

## Lab 1: Cloud Account Setup {#lab-1}

### Objective
Create an AWS Free Tier account and configure local CLI access.

### Steps

**Step 1.1: Create an AWS Account**
1. Navigate to [aws.amazon.com/free](https://aws.amazon.com/free/)
2. Click "Create a Free Account"
3. Enter your email address and choose a root account name
4. Complete identity verification (phone number + credit card)
5. Select the "Basic Support — Free" plan

**Step 1.2: Create an IAM User**
1. Log into the AWS Console
2. Navigate to **IAM** → **Users** → **Add Users**
3. Username: `lab-admin`
4. Select **"Provide user access to the AWS Management Console"**
5. Attach the policy: `AdministratorAccess` (for lab purposes only)
6. Download the credentials CSV file — store it securely

**Step 1.3: Install and Configure AWS CLI**
```bash
# Install AWS CLI v2
# macOS:
brew install awscli
# Linux:
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip && sudo ./aws/install

# Configure with your IAM user credentials
aws configure
# AWS Access Key ID: [from CSV]
# AWS Secret Access Key: [from CSV]
# Default region name: us-east-1
# Default output format: json

# Verify
aws sts get-caller-identity
```

**Step 1.4: Create an SSH Key Pair**
```bash
aws ec2 create-key-pair \
  --key-name cloud-lab-key \
  --query 'KeyMaterial' \
  --output text > cloud-lab-key.pem

chmod 400 cloud-lab-key.pem
```

### Verification
- [ ] AWS account is active
- [ ] IAM user `lab-admin` created
- [ ] `aws sts get-caller-identity` returns your account info
- [ ] SSH key pair created and saved

---

## Lab 2: Provisioning Virtual Machines {#lab-2}

### Objective
Launch an EC2 instance manually through the AWS Console.

### Steps

**Step 2.1: Navigate to EC2 Dashboard**
1. Open the AWS Console
2. Search for "EC2" in the service search bar
3. Click **"Launch Instance"**

**Step 2.2: Configure the Instance**
1. **Name:** `cloud-lab-server`
2. **AMI:** Ubuntu Server 22.04 LTS (Free Tier eligible)
3. **Instance Type:** t2.micro (Free Tier eligible)
4. **Key Pair:** Select `cloud-lab-key` (created in Lab 1)
5. **Network:** Leave defaults for now (we'll customize in Lab 3)
6. **Security Group:** Create new — allow SSH (port 22) from your IP
7. **Storage:** 20 GB gp3 (Free Tier allows up to 30 GB)

**Step 2.3: Launch and Connect**
```bash
# Wait for instance to reach "running" state
# Find the public IP in the EC2 Console → Instances

# Connect via SSH
ssh -i cloud-lab-key.pem ubuntu@<PUBLIC_IP>

# Verify you're connected
hostname
uname -a
```

**Step 2.4: Explore the Instance**
```bash
# Check system resources
free -h          # Memory
df -h            # Disk space
nproc            # CPU cores
cat /etc/os-release  # OS info
```

### Verification
- [ ] EC2 instance is running
- [ ] SSH connection successful
- [ ] Can run commands on the instance

---

## Lab 3: Networking Configuration {#lab-3}

### Objective
Create a custom VPC with proper networking for production-like infrastructure.

### Steps

**Step 3.1: Create a VPC**
1. Navigate to **VPC** → **Your VPCs** → **Create VPC**
2. Name: `cloud-lab-vpc`
3. IPv4 CIDR: `10.0.0.0/16`
4. Click **Create VPC**

**Step 3.2: Create a Public Subnet**
1. **VPC Subnets** → **Create Subnet**
2. VPC: `cloud-lab-vpc`
3. Subnet Name: `cloud-lab-public-1a`
4. Availability Zone: `us-east-1a`
5. CIDR Block: `10.0.1.0/24`
6. Enable **Auto-assign Public IPv4**

**Step 3.3: Create an Internet Gateway**
1. **Internet Gateways** → **Create Internet Gateway**
2. Name: `cloud-lab-igw`
3. **Attach** to `cloud-lab-vpc`

**Step 3.4: Configure Route Table**
1. **Route Tables** → select the main route table for `cloud-lab-vpc`
2. **Edit Routes** → Add Route:
   - Destination: `0.0.0.0/0`
   - Target: `cloud-lab-igw`
3. **Subnet Associations** → Associate `cloud-lab-public-1a`

**Step 3.5: Create Security Group**
```
Name: cloud-lab-web-sg
VPC: cloud-lab-vpc

Inbound Rules:
  - SSH (22)     → Your IP (/32)
  - HTTP (80)    → 0.0.0.0/0
  - Custom (3000) → 0.0.0.0/0

Outbound Rules:
  - All traffic → 0.0.0.0/0
```

**Step 3.6: Launch Instance in Custom VPC**
1. Terminate the instance from Lab 2
2. Launch a new instance using the same settings but:
   - **VPC:** `cloud-lab-vpc`
   - **Subnet:** `cloud-lab-public-1a`
   - **Security Group:** `cloud-lab-web-sg`

### Verification
- [ ] VPC created with correct CIDR
- [ ] Public subnet with auto-assign public IP
- [ ] Internet gateway attached
- [ ] Route table configured
- [ ] New instance accessible via SSH

---

## Lab 4: Application Deployment {#lab-4}

### Objective
Deploy the Express.js health-check server on your EC2 instance.

### Steps

**Step 4.1: Transfer Application Files**
```bash
# From your local machine
scp -i cloud-lab-key.pem -r app/ ubuntu@<PUBLIC_IP>:~/app/
scp -i cloud-lab-key.pem scripts/setup.sh ubuntu@<PUBLIC_IP>:~/setup.sh
```

**Step 4.2: Run the Setup Script**
```bash
# SSH into the instance
ssh -i cloud-lab-key.pem ubuntu@<PUBLIC_IP>

# Run the setup script
chmod +x ~/setup.sh
sudo bash ~/setup.sh
```

**Step 4.3: Verify the Deployment**
```bash
# On the instance
curl http://localhost/health

# From your local machine
curl http://<PUBLIC_IP>/health
curl http://<PUBLIC_IP>/metrics
```

**Step 4.4: Test Application Endpoints**
```bash
# Root endpoint
curl http://<PUBLIC_IP>/

# Health check with formatted output
curl -s http://<PUBLIC_IP>/health | python3 -m json.tool

# Metrics endpoint
curl http://<PUBLIC_IP>/metrics
```

### Verification
- [ ] Application running via PM2
- [ ] Nginx reverse proxy serving on port 80
- [ ] Health endpoint returns valid JSON
- [ ] Application accessible from your browser

---

## Lab 5: Monitoring and Observability {#lab-5}

### Objective
Set up CloudWatch monitoring for your EC2 instance.

### Steps

**Step 5.1: Enable Detailed Monitoring**
1. EC2 Console → Select instance → **Actions** → **Monitor and troubleshoot** → **Manage detailed monitoring**
2. Enable detailed monitoring (1-minute intervals)

**Step 5.2: Create CloudWatch Alarms**
1. Navigate to **CloudWatch** → **Alarms** → **Create Alarm**
2. Create a **CPU Utilization** alarm:
   - Metric: EC2 → Per-Instance Metrics → CPUUtilization
   - Threshold: > 80% for 2 consecutive periods
   - Period: 5 minutes
3. Create a **Status Check** alarm:
   - Metric: StatusCheckFailed
   - Threshold: >= 1 for 1 period

**Step 5.3: Create a CloudWatch Dashboard**
1. **CloudWatch** → **Dashboards** → **Create Dashboard**
2. Name: `cloud-lab-dashboard`
3. Add widgets:
   - **Line chart:** CPU Utilization
   - **Number:** Network In/Out
   - **Line chart:** Disk Read/Write Operations
   - **Number:** Status Checks

**Step 5.4: Set Up the Health Monitor Script**
```bash
# On your local machine or another instance
scp -i cloud-lab-key.pem scripts/monitor.sh ubuntu@<PUBLIC_IP>:~/monitor.sh
ssh -i cloud-lab-key.pem ubuntu@<PUBLIC_IP>

chmod +x ~/monitor.sh
# Run the monitor (checks every 30 seconds)
./monitor.sh http://localhost/health 30 ~/health.log
```

### Verification
- [ ] Detailed monitoring enabled
- [ ] CPU alarm created
- [ ] Dashboard showing metrics
- [ ] Health monitor script running and logging

---

## Lab 6: Infrastructure as Code {#lab-6}

### Objective
Use Terraform to automate the entire infrastructure from Labs 2-4.

### Steps

**Step 6.1: Install Terraform**
```bash
# macOS
brew install terraform

# Linux
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/

# Verify
terraform --version
```

**Step 6.2: Review the Terraform Files**
```bash
cd terraform/
cat main.tf       # Main configuration
cat variables.tf  # Input variables
cat outputs.tf    # Output values
```

**Step 6.3: Initialize and Plan**
```bash
terraform init

# Create a terraform.tfvars file
echo 'key_name = "cloud-lab-key"' > terraform.tfvars

# Preview what will be created
terraform plan
```

**Step 6.4: Apply the Configuration**
```bash
terraform apply
# Review the plan and type "yes" to proceed

# Note the outputs
terraform output public_ip
terraform output ssh_command
```

**Step 6.5: Verify the Automated Deployment**
```bash
# Wait 2-3 minutes for user_data script to complete
# Then test the deployment
curl http://$(terraform output -raw public_ip)/health
```

**Step 6.6: Clean Up**
```bash
# When done, destroy all resources to avoid charges
terraform destroy
# Type "yes" to confirm
```

### Verification
- [ ] Terraform initialized successfully
- [ ] Plan shows expected resources
- [ ] Apply creates all resources
- [ ] Application accessible at the output IP
- [ ] Destroy removes all resources

---

## Congratulations!

You've completed all six labs in the Cloud Infrastructure Exploration Lab. You now have hands-on experience with:

- Cloud account setup and IAM
- Virtual machine provisioning
- VPC networking and security groups
- Application deployment with Nginx reverse proxy
- CloudWatch monitoring
- Infrastructure as Code with Terraform
