#!/bin/bash
# FinSolve AI Assistant - EC2 User Data Script
# Author: Dr. Erick K. Yegon

# Update system
yum update -y

# Install Docker
amazon-linux-extras install docker -y
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
./aws/install

# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
rpm -U ./amazon-cloudwatch-agent.rpm

# Configure CloudWatch agent
cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << 'EOF'
{
    "logs": {
        "logs_collected": {
            "files": {
                "collect_list": [
                    {
                        "file_path": "/var/log/finsolve/application.log",
                        "log_group_name": "/aws/ec2/finsolve/application",
                        "log_stream_name": "{instance_id}"
                    },
                    {
                        "file_path": "/var/log/finsolve/access.log",
                        "log_group_name": "/aws/ec2/finsolve/access",
                        "log_stream_name": "{instance_id}"
                    }
                ]
            }
        }
    },
    "metrics": {
        "namespace": "FinSolve/Application",
        "metrics_collected": {
            "cpu": {
                "measurement": [
                    "cpu_usage_idle",
                    "cpu_usage_iowait",
                    "cpu_usage_user",
                    "cpu_usage_system"
                ],
                "metrics_collection_interval": 60
            },
            "disk": {
                "measurement": [
                    "used_percent"
                ],
                "metrics_collection_interval": 60,
                "resources": [
                    "*"
                ]
            },
            "diskio": {
                "measurement": [
                    "io_time"
                ],
                "metrics_collection_interval": 60,
                "resources": [
                    "*"
                ]
            },
            "mem": {
                "measurement": [
                    "mem_used_percent"
                ],
                "metrics_collection_interval": 60
            }
        }
    }
}
EOF

# Start CloudWatch agent
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json -s

# Create application directories
mkdir -p /app/data
mkdir -p /var/log/finsolve
chown ec2-user:ec2-user /app/data
chown ec2-user:ec2-user /var/log/finsolve

# Download application data from S3
aws s3 sync s3://${s3_data_bucket}/data/ /app/data/ --region ${aws_region}

# Login to ECR
aws ecr get-login-password --region ${aws_region} | docker login --username AWS --password-stdin ${ecr_repository_uri}

# Create environment file
cat > /app/.env << EOF
DATABASE_URL=${database_url}
REDIS_URL=${redis_url}
AWS_DEFAULT_REGION=${aws_region}
S3_DATA_BUCKET=${s3_data_bucket}
ENVIRONMENT=production
LOG_LEVEL=INFO
EOF

# Create Docker Compose file for production
cat > /app/docker-compose.prod.yml << 'EOF'
version: '3.8'

services:
  app:
    image: ${ecr_repository_uri}:latest
    ports:
      - "8000:8000"
      - "8501:8501"
    env_file:
      - .env
    volumes:
      - ./data:/app/data:ro
      - /var/log/finsolve:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
EOF

# Pull and start the application
cd /app
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d

# Create systemd service for auto-restart
cat > /etc/systemd/system/finsolve-app.service << 'EOF'
[Unit]
Description=FinSolve AI Assistant
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/app
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
systemctl enable finsolve-app.service
systemctl start finsolve-app.service

# Create log rotation configuration
cat > /etc/logrotate.d/finsolve << 'EOF'
/var/log/finsolve/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 ec2-user ec2-user
    postrotate
        docker-compose -f /app/docker-compose.prod.yml restart app
    endscript
}
EOF

# Create health check script
cat > /usr/local/bin/finsolve-health-check.sh << 'EOF'
#!/bin/bash

# Check if application is responding
API_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
UI_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8501/)

if [ "$API_HEALTH" != "200" ] || [ "$UI_HEALTH" != "200" ]; then
    echo "$(date): Health check failed. API: $API_HEALTH, UI: $UI_HEALTH" >> /var/log/finsolve/health-check.log
    
    # Restart the application
    cd /app
    docker-compose -f docker-compose.prod.yml restart
    
    # Send CloudWatch metric
    aws cloudwatch put-metric-data \
        --namespace "FinSolve/Application" \
        --metric-data MetricName=HealthCheckFailure,Value=1,Unit=Count \
        --region ${aws_region}
else
    echo "$(date): Health check passed. API: $API_HEALTH, UI: $UI_HEALTH" >> /var/log/finsolve/health-check.log
    
    # Send CloudWatch metric
    aws cloudwatch put-metric-data \
        --namespace "FinSolve/Application" \
        --metric-data MetricName=HealthCheckSuccess,Value=1,Unit=Count \
        --region ${aws_region}
fi
EOF

chmod +x /usr/local/bin/finsolve-health-check.sh

# Add health check to crontab
echo "*/5 * * * * /usr/local/bin/finsolve-health-check.sh" | crontab -

# Create update script
cat > /usr/local/bin/finsolve-update.sh << 'EOF'
#!/bin/bash

# Update script for FinSolve AI Assistant
echo "$(date): Starting application update" >> /var/log/finsolve/update.log

cd /app

# Login to ECR
aws ecr get-login-password --region ${aws_region} | docker login --username AWS --password-stdin ${ecr_repository_uri}

# Pull latest image
docker-compose -f docker-compose.prod.yml pull

# Restart with new image
docker-compose -f docker-compose.prod.yml up -d

# Clean up old images
docker image prune -f

echo "$(date): Application update completed" >> /var/log/finsolve/update.log
EOF

chmod +x /usr/local/bin/finsolve-update.sh

# Create backup script
cat > /usr/local/bin/finsolve-backup.sh << 'EOF'
#!/bin/bash

# Backup script for FinSolve AI Assistant
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/tmp/finsolve_backup_$BACKUP_DATE"

echo "$(date): Starting backup" >> /var/log/finsolve/backup.log

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup application data
cp -r /app/data $BACKUP_DIR/
cp /app/.env $BACKUP_DIR/
cp /app/docker-compose.prod.yml $BACKUP_DIR/

# Backup logs
cp -r /var/log/finsolve $BACKUP_DIR/

# Create tar archive
tar -czf "/tmp/finsolve_backup_$BACKUP_DATE.tar.gz" -C /tmp "finsolve_backup_$BACKUP_DATE"

# Upload to S3
aws s3 cp "/tmp/finsolve_backup_$BACKUP_DATE.tar.gz" "s3://${s3_data_bucket}/backups/" --region ${aws_region}

# Clean up local backup files
rm -rf $BACKUP_DIR
rm "/tmp/finsolve_backup_$BACKUP_DATE.tar.gz"

echo "$(date): Backup completed" >> /var/log/finsolve/backup.log
EOF

chmod +x /usr/local/bin/finsolve-backup.sh

# Schedule daily backups
echo "0 2 * * * /usr/local/bin/finsolve-backup.sh" | crontab -

# Install security updates automatically
echo "0 3 * * 0 yum update -y --security" | crontab -

# Create monitoring script
cat > /usr/local/bin/finsolve-monitor.sh << 'EOF'
#!/bin/bash

# Monitoring script for FinSolve AI Assistant

# Get container stats
CONTAINER_ID=$(docker ps -q --filter "name=app_app")

if [ ! -z "$CONTAINER_ID" ]; then
    # Get memory usage
    MEMORY_USAGE=$(docker stats --no-stream --format "{{.MemUsage}}" $CONTAINER_ID | cut -d'/' -f1 | sed 's/[^0-9.]//g')
    
    # Get CPU usage
    CPU_USAGE=$(docker stats --no-stream --format "{{.CPUPerc}}" $CONTAINER_ID | sed 's/%//g')
    
    # Send metrics to CloudWatch
    aws cloudwatch put-metric-data \
        --namespace "FinSolve/Application" \
        --metric-data MetricName=ContainerMemoryUsage,Value=$MEMORY_USAGE,Unit=Megabytes \
        --region ${aws_region}
    
    aws cloudwatch put-metric-data \
        --namespace "FinSolve/Application" \
        --metric-data MetricName=ContainerCPUUsage,Value=$CPU_USAGE,Unit=Percent \
        --region ${aws_region}
fi

# Check disk usage
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//g')
aws cloudwatch put-metric-data \
    --namespace "FinSolve/Application" \
    --metric-data MetricName=DiskUsage,Value=$DISK_USAGE,Unit=Percent \
    --region ${aws_region}
EOF

chmod +x /usr/local/bin/finsolve-monitor.sh

# Schedule monitoring every 5 minutes
echo "*/5 * * * * /usr/local/bin/finsolve-monitor.sh" | crontab -

# Signal that user data script has completed
/opt/aws/bin/cfn-signal -e $? --stack ${AWS::StackName} --resource AutoScalingGroup --region ${aws_region} || true

echo "$(date): FinSolve AI Assistant deployment completed" >> /var/log/finsolve/deployment.log
