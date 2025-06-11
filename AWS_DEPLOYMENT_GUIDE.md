# FinSolve AI Assistant - AWS Deployment Guide

## 🚀 **Complete AWS Production Deployment**

**Author:** Dr. Erick K. Yegon  
**Version:** 1.0.0  
**Last Updated:** December 11, 2024

---

## 📋 **Deployment Overview**

This guide provides step-by-step instructions for deploying the FinSolve AI Assistant on AWS with enterprise-grade infrastructure, including:

- **EC2 instances** for application hosting
- **RDS PostgreSQL** for database
- **ElastiCache Redis** for session management
- **Application Load Balancer** for high availability
- **CloudFront CDN** for global performance
- **S3** for static assets and data storage
- **CloudWatch** for monitoring and logging

---

## 🏗️ **AWS Architecture Overview**

```
┌─────────────────────────────────────────────────────────────┐
│                        AWS Cloud                            │
├─────────────────────────────────────────────────────────────┤
│  CloudFront CDN                                            │
│  ├── Global Edge Locations                                 │
│  └── SSL/TLS Termination                                   │
├─────────────────────────────────────────────────────────────┤
│  Application Load Balancer (ALB)                          │
│  ├── Health Checks                                         │
│  ├── SSL Certificates                                      │
│  └── Traffic Distribution                                  │
├─────────────────────────────────────────────────────────────┤
│  Auto Scaling Group                                        │
│  ├── EC2 Instance 1 (FastAPI + Streamlit)                │
│  ├── EC2 Instance 2 (FastAPI + Streamlit)                │
│  └── EC2 Instance 3 (FastAPI + Streamlit)                │
├─────────────────────────────────────────────────────────────┤
│  Data Layer                                                │
│  ├── RDS PostgreSQL (Multi-AZ)                           │
│  ├── ElastiCache Redis (Cluster Mode)                    │
│  └── S3 Buckets (Data + Static Assets)                   │
├─────────────────────────────────────────────────────────────┤
│  Monitoring & Security                                     │
│  ├── CloudWatch (Logs + Metrics)                         │
│  ├── AWS WAF (Web Application Firewall)                  │
│  └── VPC with Private/Public Subnets                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ **Prerequisites**

### **AWS Account Setup:**
1. **AWS Account** with appropriate permissions
2. **AWS CLI** installed and configured
3. **Domain name** for the application (optional but recommended)
4. **SSL Certificate** (can be created via AWS Certificate Manager)

### **Local Development Setup:**
1. **Docker** installed for containerization
2. **Terraform** (optional) for Infrastructure as Code
3. **Git** for version control

---

## 📦 **Step 1: Containerization**

### **Create Dockerfile:**

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose ports
EXPOSE 8000 8501

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start script
COPY start.sh .
RUN chmod +x start.sh
CMD ["./start.sh"]
```

### **Create Start Script:**

```bash
#!/bin/bash
# start.sh

# Start FastAPI in background
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 &

# Start Streamlit
streamlit run src/frontend/streamlit_app.py --server.port 8501 --server.address 0.0.0.0

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?
```

### **Create Docker Compose for Local Testing:**

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
      - "8501:8501"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/finsolve
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - ./data:/app/data

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=finsolve
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

---

## 🌐 **Step 2: AWS Infrastructure Setup**

### **VPC and Networking:**

```bash
# Create VPC
aws ec2 create-vpc --cidr-block 10.0.0.0/16 --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=finsolve-vpc}]'

# Create Internet Gateway
aws ec2 create-internet-gateway --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=finsolve-igw}]'

# Create Public Subnets (2 AZs for high availability)
aws ec2 create-subnet --vpc-id vpc-xxxxxxxxx --cidr-block 10.0.1.0/24 --availability-zone us-east-1a
aws ec2 create-subnet --vpc-id vpc-xxxxxxxxx --cidr-block 10.0.2.0/24 --availability-zone us-east-1b

# Create Private Subnets
aws ec2 create-subnet --vpc-id vpc-xxxxxxxxx --cidr-block 10.0.3.0/24 --availability-zone us-east-1a
aws ec2 create-subnet --vpc-id vpc-xxxxxxxxx --cidr-block 10.0.4.0/24 --availability-zone us-east-1b
```

### **Security Groups:**

```bash
# Application Security Group
aws ec2 create-security-group \
    --group-name finsolve-app-sg \
    --description "Security group for FinSolve application" \
    --vpc-id vpc-xxxxxxxxx

# Allow HTTP/HTTPS from ALB
aws ec2 authorize-security-group-ingress \
    --group-id sg-xxxxxxxxx \
    --protocol tcp \
    --port 8000 \
    --source-group sg-alb-xxxxxxxxx

aws ec2 authorize-security-group-ingress \
    --group-id sg-xxxxxxxxx \
    --protocol tcp \
    --port 8501 \
    --source-group sg-alb-xxxxxxxxx

# Database Security Group
aws ec2 create-security-group \
    --group-name finsolve-db-sg \
    --description "Security group for FinSolve database" \
    --vpc-id vpc-xxxxxxxxx

# Allow PostgreSQL from application
aws ec2 authorize-security-group-ingress \
    --group-id sg-db-xxxxxxxxx \
    --protocol tcp \
    --port 5432 \
    --source-group sg-xxxxxxxxx
```

---

## 🗄️ **Step 3: Database Setup (RDS)**

### **Create RDS PostgreSQL Instance:**

```bash
# Create DB Subnet Group
aws rds create-db-subnet-group \
    --db-subnet-group-name finsolve-db-subnet-group \
    --db-subnet-group-description "Subnet group for FinSolve database" \
    --subnet-ids subnet-xxxxxxxxx subnet-yyyyyyyyy

# Create RDS Instance
aws rds create-db-instance \
    --db-instance-identifier finsolve-db \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --engine-version 15.4 \
    --master-username finsolve_admin \
    --master-user-password "YourSecurePassword123!" \
    --allocated-storage 20 \
    --storage-type gp2 \
    --vpc-security-group-ids sg-db-xxxxxxxxx \
    --db-subnet-group-name finsolve-db-subnet-group \
    --backup-retention-period 7 \
    --multi-az \
    --storage-encrypted \
    --deletion-protection
```

### **Create ElastiCache Redis:**

```bash
# Create Cache Subnet Group
aws elasticache create-cache-subnet-group \
    --cache-subnet-group-name finsolve-cache-subnet-group \
    --cache-subnet-group-description "Subnet group for FinSolve cache" \
    --subnet-ids subnet-xxxxxxxxx subnet-yyyyyyyyy

# Create Redis Cluster
aws elasticache create-cache-cluster \
    --cache-cluster-id finsolve-redis \
    --cache-node-type cache.t3.micro \
    --engine redis \
    --num-cache-nodes 1 \
    --cache-subnet-group-name finsolve-cache-subnet-group \
    --security-group-ids sg-cache-xxxxxxxxx
```

---

## 📦 **Step 4: Application Deployment**

### **Create S3 Buckets:**

```bash
# Create S3 bucket for application data
aws s3 mb s3://finsolve-app-data-$(date +%s)

# Create S3 bucket for static assets
aws s3 mb s3://finsolve-static-assets-$(date +%s)

# Upload application data
aws s3 sync ./data s3://finsolve-app-data-xxxxxxxxx/data/

# Set bucket policies for appropriate access
```

### **Create ECR Repository:**

```bash
# Create ECR repository
aws ecr create-repository --repository-name finsolve-ai-assistant

# Get login token
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com

# Build and push Docker image
docker build -t finsolve-ai-assistant .
docker tag finsolve-ai-assistant:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/finsolve-ai-assistant:latest
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/finsolve-ai-assistant:latest
```

### **Create Launch Template:**

```bash
# Create launch template
aws ec2 create-launch-template \
    --launch-template-name finsolve-launch-template \
    --launch-template-data '{
        "ImageId": "ami-0c02fb55956c7d316",
        "InstanceType": "t3.medium",
        "SecurityGroupIds": ["sg-xxxxxxxxx"],
        "IamInstanceProfile": {"Name": "finsolve-ec2-role"},
        "UserData": "'$(base64 -w 0 user-data.sh)'"
    }'
```

### **User Data Script:**

```bash
#!/bin/bash
# user-data.sh

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

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com

# Pull and run application
docker run -d \
    --name finsolve-app \
    -p 8000:8000 \
    -p 8501:8501 \
    -e DATABASE_URL="postgresql://finsolve_admin:YourSecurePassword123!@finsolve-db.xxxxxxxxx.us-east-1.rds.amazonaws.com:5432/postgres" \
    -e REDIS_URL="redis://finsolve-redis.xxxxxxxxx.cache.amazonaws.com:6379" \
    -e AWS_DEFAULT_REGION="us-east-1" \
    123456789012.dkr.ecr.us-east-1.amazonaws.com/finsolve-ai-assistant:latest

# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
rpm -U ./amazon-cloudwatch-agent.rpm
```

---

## ⚖️ **Step 5: Load Balancer Setup**

### **Create Application Load Balancer:**

```bash
# Create ALB
aws elbv2 create-load-balancer \
    --name finsolve-alb \
    --subnets subnet-xxxxxxxxx subnet-yyyyyyyyy \
    --security-groups sg-alb-xxxxxxxxx \
    --scheme internet-facing \
    --type application

# Create Target Groups
aws elbv2 create-target-group \
    --name finsolve-api-tg \
    --protocol HTTP \
    --port 8000 \
    --vpc-id vpc-xxxxxxxxx \
    --health-check-path /health \
    --health-check-interval-seconds 30 \
    --healthy-threshold-count 2 \
    --unhealthy-threshold-count 3

aws elbv2 create-target-group \
    --name finsolve-ui-tg \
    --protocol HTTP \
    --port 8501 \
    --vpc-id vpc-xxxxxxxxx \
    --health-check-path / \
    --health-check-interval-seconds 30

# Create Listeners
aws elbv2 create-listener \
    --load-balancer-arn arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/finsolve-alb/xxxxxxxxx \
    --protocol HTTP \
    --port 80 \
    --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/finsolve-ui-tg/xxxxxxxxx

# Create HTTPS listener (if SSL certificate available)
aws elbv2 create-listener \
    --load-balancer-arn arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/finsolve-alb/xxxxxxxxx \
    --protocol HTTPS \
    --port 443 \
    --certificates CertificateArn=arn:aws:acm:us-east-1:123456789012:certificate/xxxxxxxxx \
    --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/finsolve-ui-tg/xxxxxxxxx
```

---

## 🔄 **Step 6: Auto Scaling Setup**

### **Create Auto Scaling Group:**

```bash
# Create Auto Scaling Group
aws autoscaling create-auto-scaling-group \
    --auto-scaling-group-name finsolve-asg \
    --launch-template LaunchTemplateName=finsolve-launch-template,Version='$Latest' \
    --min-size 2 \
    --max-size 6 \
    --desired-capacity 3 \
    --target-group-arns arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/finsolve-api-tg/xxxxxxxxx arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/finsolve-ui-tg/xxxxxxxxx \
    --vpc-zone-identifier "subnet-xxxxxxxxx,subnet-yyyyyyyyy" \
    --health-check-type ELB \
    --health-check-grace-period 300

# Create Scaling Policies
aws autoscaling put-scaling-policy \
    --auto-scaling-group-name finsolve-asg \
    --policy-name finsolve-scale-up \
    --policy-type TargetTrackingScaling \
    --target-tracking-configuration '{
        "TargetValue": 70.0,
        "PredefinedMetricSpecification": {
            "PredefinedMetricType": "ASGAverageCPUUtilization"
        }
    }'
```

---

## 📊 **Step 7: Monitoring and Logging**

### **CloudWatch Setup:**

```bash
# Create CloudWatch Log Groups
aws logs create-log-group --log-group-name /aws/ec2/finsolve/application
aws logs create-log-group --log-group-name /aws/ec2/finsolve/access

# Create CloudWatch Alarms
aws cloudwatch put-metric-alarm \
    --alarm-name "FinSolve-High-CPU" \
    --alarm-description "Alarm when CPU exceeds 80%" \
    --metric-name CPUUtilization \
    --namespace AWS/EC2 \
    --statistic Average \
    --period 300 \
    --threshold 80 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 2

# Create Dashboard
aws cloudwatch put-dashboard \
    --dashboard-name "FinSolve-Dashboard" \
    --dashboard-body file://dashboard.json
```

### **CloudWatch Dashboard Configuration:**

```json
{
    "widgets": [
        {
            "type": "metric",
            "properties": {
                "metrics": [
                    ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", "finsolve-alb"],
                    ["AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", "finsolve-alb"],
                    ["AWS/EC2", "CPUUtilization", "AutoScalingGroupName", "finsolve-asg"]
                ],
                "period": 300,
                "stat": "Average",
                "region": "us-east-1",
                "title": "FinSolve Application Metrics"
            }
        }
    ]
}
```

---

## 🔒 **Step 8: Security Hardening**

### **WAF Configuration:**

```bash
# Create WAF Web ACL
aws wafv2 create-web-acl \
    --name finsolve-waf \
    --scope CLOUDFRONT \
    --default-action Allow={} \
    --rules file://waf-rules.json
```

### **SSL/TLS Certificate:**

```bash
# Request SSL certificate
aws acm request-certificate \
    --domain-name finsolve.yourdomain.com \
    --validation-method DNS \
    --subject-alternative-names "*.finsolve.yourdomain.com"
```

---

## 🌍 **Step 9: CloudFront CDN**

### **Create CloudFront Distribution:**

```bash
# Create CloudFront distribution
aws cloudfront create-distribution \
    --distribution-config file://cloudfront-config.json
```

### **CloudFront Configuration:**

```json
{
    "CallerReference": "finsolve-cdn-2024",
    "Comment": "FinSolve AI Assistant CDN",
    "DefaultCacheBehavior": {
        "TargetOriginId": "finsolve-alb",
        "ViewerProtocolPolicy": "redirect-to-https",
        "TrustedSigners": {
            "Enabled": false,
            "Quantity": 0
        },
        "ForwardedValues": {
            "QueryString": true,
            "Cookies": {
                "Forward": "all"
            }
        },
        "MinTTL": 0
    },
    "Origins": {
        "Quantity": 1,
        "Items": [
            {
                "Id": "finsolve-alb",
                "DomainName": "finsolve-alb-xxxxxxxxx.us-east-1.elb.amazonaws.com",
                "CustomOriginConfig": {
                    "HTTPPort": 80,
                    "HTTPSPort": 443,
                    "OriginProtocolPolicy": "https-only"
                }
            }
        ]
    },
    "Enabled": true,
    "PriceClass": "PriceClass_100"
}
```

---

## 🚀 **Step 10: Deployment Automation**

### **GitHub Actions Workflow:**

```yaml
# .github/workflows/deploy.yml
name: Deploy to AWS

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v1
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: us-east-1
    
    - name: Login to Amazon ECR
      id: login-ecr
      uses: aws-actions/amazon-ecr-login@v1
    
    - name: Build, tag, and push image to Amazon ECR
      env:
        ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        ECR_REPOSITORY: finsolve-ai-assistant
        IMAGE_TAG: ${{ github.sha }}
      run: |
        docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
    
    - name: Update Auto Scaling Group
      run: |
        aws autoscaling update-auto-scaling-group \
          --auto-scaling-group-name finsolve-asg \
          --launch-template LaunchTemplateName=finsolve-launch-template,Version='$Latest'
```

---

## 💰 **Cost Optimization**

### **Estimated Monthly Costs:**

| Service | Configuration | Estimated Cost |
|---------|---------------|----------------|
| **EC2 Instances** | 3x t3.medium | $100-150 |
| **RDS PostgreSQL** | db.t3.micro Multi-AZ | $30-40 |
| **ElastiCache Redis** | cache.t3.micro | $15-20 |
| **Application Load Balancer** | Standard ALB | $20-25 |
| **CloudFront** | 1TB data transfer | $10-15 |
| **S3 Storage** | 100GB | $5-10 |
| **Data Transfer** | Moderate usage | $10-20 |
| **CloudWatch** | Standard monitoring | $5-10 |
| **Total Estimated** | | **$195-290/month** |

### **Cost Optimization Tips:**
1. **Use Reserved Instances** for predictable workloads (up to 75% savings)
2. **Implement Auto Scaling** to scale down during low usage
3. **Use S3 Intelligent Tiering** for data storage
4. **Enable CloudWatch cost monitoring** and alerts
5. **Regular review** of unused resources

---

## 🔧 **Maintenance and Updates**

### **Regular Maintenance Tasks:**
1. **Security Updates**: Monthly OS and application updates
2. **Database Backups**: Automated daily backups with 7-day retention
3. **Log Rotation**: Automated log cleanup to manage storage costs
4. **Performance Monitoring**: Weekly performance reviews
5. **Cost Optimization**: Monthly cost analysis and optimization

### **Update Deployment Process:**
1. **Test in staging environment**
2. **Create new Docker image**
3. **Update launch template**
4. **Rolling deployment** via Auto Scaling Group
5. **Monitor application health**
6. **Rollback if issues detected**

---

## ✅ **Deployment Checklist**

- [ ] AWS account setup and permissions configured
- [ ] VPC and networking infrastructure created
- [ ] Security groups configured
- [ ] RDS PostgreSQL database created and configured
- [ ] ElastiCache Redis cluster created
- [ ] S3 buckets created and data uploaded
- [ ] ECR repository created and Docker image pushed
- [ ] Launch template created with user data script
- [ ] Auto Scaling Group configured
- [ ] Application Load Balancer setup with target groups
- [ ] CloudFront distribution created (optional)
- [ ] SSL certificate configured
- [ ] WAF rules configured
- [ ] CloudWatch monitoring and alarms setup
- [ ] Domain name configured (if applicable)
- [ ] Application tested and verified
- [ ] Backup and disaster recovery plan implemented
- [ ] Documentation updated with deployment details

---

## 🆘 **Troubleshooting**

### **Common Issues:**

1. **Application not starting**: Check CloudWatch logs for errors
2. **Database connection issues**: Verify security groups and connection strings
3. **Load balancer health checks failing**: Check target group health check settings
4. **High costs**: Review CloudWatch cost explorer and optimize resources
5. **Performance issues**: Monitor CloudWatch metrics and scale resources

### **Support Resources:**
- **AWS Documentation**: https://docs.aws.amazon.com/
- **AWS Support**: Available through AWS Console
- **Community Forums**: AWS Developer Forums
- **Application Logs**: CloudWatch Logs for detailed troubleshooting

---

This comprehensive guide provides everything needed to deploy the FinSolve AI Assistant on AWS with enterprise-grade infrastructure, security, and monitoring.
