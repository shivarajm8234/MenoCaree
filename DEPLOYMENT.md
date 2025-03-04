# MenoCaree Deployment Guide

## PDF Generation Options

The application uses two methods for PDF generation:

1. **Primary Method (pdfkit with wkhtmltopdf)**: Produces high-quality, styled PDFs with full HTML/CSS support.
2. **Fallback Method (reportlab)**: A simpler PDF generation that works without additional system dependencies.

## Deployment on Koyeb

When deploying to Koyeb, you have two options:

### Option 1: Use the Built-in Fallback

The application will automatically detect it's running on Koyeb and use the reportlab fallback for PDF generation. This requires no additional configuration but produces simpler PDF reports.

### Option 2: Use Custom Dockerfile (Recommended)

For full PDF generation capability:

1. Use the provided Dockerfile in your repository
2. Set up your Koyeb deployment to use this custom Dockerfile
3. This will ensure wkhtmltopdf is installed in the container

In Koyeb dashboard:
- Select "Docker" as the deployment method
- Point to your repository containing the Dockerfile
- The Dockerfile will automatically install wkhtmltopdf

## Other Deployment Environments

For other environments (Heroku, DigitalOcean, etc.):

1. Make sure to install wkhtmltopdf on the server
2. Set `DEPLOYMENT_ENV=production` if you want to force using the reportlab fallback

### Installing wkhtmltopdf on Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install -y wkhtmltopdf
```

### Installing wkhtmltopdf on CentOS/RHEL:

```bash
sudo yum install -y wkhtmltopdf
```
