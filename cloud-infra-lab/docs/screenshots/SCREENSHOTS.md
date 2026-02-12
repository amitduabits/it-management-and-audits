# Screenshots Reference

This document describes the screenshots that should be captured while completing the lab exercises. Each entry describes what the screenshot should show.

---

## Lab 1: Cloud Account Setup
- **01_aws_console_login.png** — Shows the AWS Management Console home page after successful login
- **02_iam_user_created.png** — IAM Users page showing the `lab-admin` user with AdministratorAccess policy
- **03_aws_cli_configured.png** — Terminal showing successful `aws sts get-caller-identity` output

## Lab 2: Provisioning Virtual Machines
- **04_ec2_launch_wizard.png** — EC2 Launch Instance wizard with Ubuntu 22.04 AMI selected and t2.micro instance type
- **05_ec2_instance_running.png** — EC2 Instances dashboard showing the instance in "running" state with public IP
- **06_ssh_connected.png** — Terminal showing successful SSH connection to the EC2 instance

## Lab 3: Networking Configuration
- **07_vpc_created.png** — VPC dashboard showing `cloud-lab-vpc` with CIDR 10.0.0.0/16
- **08_subnet_created.png** — Subnets page showing the public subnet 10.0.1.0/24
- **09_igw_attached.png** — Internet Gateways page showing the IGW attached to the VPC
- **10_route_table.png** — Route table showing the 0.0.0.0/0 route pointing to the IGW
- **11_security_group_rules.png** — Security group inbound rules showing ports 22, 80, and 3000

## Lab 4: Application Deployment
- **12_setup_script_running.png** — Terminal showing the setup.sh script executing on the EC2 instance
- **13_health_check_response.png** — Browser or curl showing the JSON health check response from the deployed app
- **14_pm2_status.png** — Terminal showing `pm2 status` with the cloud-lab-app running
- **15_nginx_status.png** — Terminal showing `systemctl status nginx` confirming Nginx is active

## Lab 5: Monitoring and Observability
- **16_cloudwatch_dashboard.png** — CloudWatch dashboard with CPU, network, and disk widgets
- **17_cloudwatch_alarm.png** — CloudWatch alarm configuration for CPU utilization > 80%
- **18_monitor_script_output.png** — Terminal showing the monitor.sh script output with health check results

## Lab 6: Infrastructure as Code
- **19_terraform_init.png** — Terminal showing successful `terraform init` output
- **20_terraform_plan.png** — Terminal showing `terraform plan` output with resources to be created
- **21_terraform_apply.png** — Terminal showing `terraform apply` output with all resources created
- **22_terraform_outputs.png** — Terminal showing terraform output values (public IP, SSH command)
- **23_terraform_destroy.png** — Terminal showing `terraform destroy` output confirming cleanup
