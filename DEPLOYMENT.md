# 🚀 Deployment Guide - Render.com

This guide covers deploying the Orders & Inventory Management API to Render.com using Infrastructure as Code (render.yaml).

## 🎯 Deployment Approach: render.yaml vs Dashboard

### **Why I Chose render.yaml (Infrastructure as Code)**

I chose **render.yaml** over the Render dashboard for several key reasons:

#### ✅ **Advantages of render.yaml:**
1. **Version Control**: Configuration is tracked in git alongside code
2. **Reproducibility**: Exact same deployment configuration every time
3. **Team Collaboration**: All team members see the same deployment setup
4. **Environment Parity**: Dev/staging/prod configurations can be managed consistently
5. **Automation**: Easy CI/CD integration and automated deployments
6. **Documentation**: Configuration serves as deployment documentation
7. **Rollback Capability**: Easy to revert to previous configurations

#### ❌ **Dashboard Limitations:**
- Configuration changes not tracked
- Manual setup required for each environment
- Prone to configuration drift
- Difficult to share exact setup with team
- No easy way to backup/restore configuration

### **When to Use Each Approach:**
- **render.yaml**: Production apps, team projects, complex configurations
- **Dashboard**: Quick prototypes, personal projects, one-off deployments

## ⚙️ Build and Start Commands

### **Build Command:**
```bash
pip install poetry && poetry config virtualenvs.create false && poetry install --only=main
```

**Breakdown:**
1. `pip install poetry` - Install Poetry package manager
2. `poetry config virtualenvs.create false` - Don't create virtual env (Render handles this)
3. `poetry install --only=main` - Install only production dependencies (excludes dev/test packages)

### **Start Command:**
```bash
uvicorn src.orders_inventory.api.main:app --host 0.0.0.0 --port $PORT
```

**Breakdown:**
1. `uvicorn` - ASGI server for FastAPI
2. `src.orders_inventory.api.main:app` - Python path to FastAPI app instance
3. `--host 0.0.0.0` - Bind to all network interfaces (required for Render)
4. `--port $PORT` - Use Render's assigned port

### **Where $PORT Comes From:**
- **$PORT** is an **environment variable automatically set by Render**
- Render assigns a dynamic port for each service instance
- This allows Render's load balancer to route traffic properly
- **You cannot hardcode ports** on Render - must use $PORT
- Example: Render might assign PORT=10000 for your service

## 🔧 Environment Variables Configuration

### **Required Environment Variables:**

```yaml
envVars:
  - key: PYTHON_VERSION
    value: 3.12.0
  - key: DATABASE_URL
    value: sqlite:///./orders_inventory.db
  - key: ENVIRONMENT
    value: production
  - key: LOG_LEVEL
    value: INFO
  - key: CORS_ORIGINS
    value: "*"
```

### **Variable Explanations:**

#### **PYTHON_VERSION**
- **Purpose**: Specify Python runtime version
- **Value**: `3.12.0`
- **Why**: Ensures consistent Python version across deployments

#### **DATABASE_URL**
- **Purpose**: Database connection string
- **Value**: `sqlite:///./orders_inventory.db` (for simplicity)
- **Production Alternative**: PostgreSQL connection string
- **Format**: `postgresql://user:password@host:port/database`

#### **ENVIRONMENT**
- **Purpose**: Application environment indicator
- **Value**: `production`
- **Usage**: Controls logging, debug modes, error handling

#### **LOG_LEVEL**
- **Purpose**: Control logging verbosity
- **Value**: `INFO`
- **Options**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

#### **CORS_ORIGINS**
- **Purpose**: Configure Cross-Origin Resource Sharing
- **Value**: `"*"` (allow all origins) or specific domains
- **Production**: Should be restricted to actual frontend domains
- **Example**: `"https://myapp.com,https://app.mycompany.com"`

### **Optional Environment Variables:**

#### **For PostgreSQL (Production):**
```yaml
- key: DATABASE_URL
  value: postgresql://user:password@host:port/orders_inventory
- key: DB_POOL_SIZE
  value: "10"
- key: DB_MAX_OVERFLOW
  value: "20"
```

#### **For Enhanced Security:**
```yaml
- key: SECRET_KEY
  value: "your-secret-key-here"
- key: JWT_SECRET_KEY
  value: "jwt-signing-key"
- key: WEBHOOK_SECRET
  value: "webhook-validation-secret"
```

## 📁 File Structure for Deployment

```
orders-inventory/
├── render.yaml              # Render deployment configuration
├── requirements.txt         # Production dependencies
├── Procfile                # Alternative start command
├── runtime.txt             # Python version specification
├── src/
│   └── orders_inventory/
│       └── api/
│           └── main.py     # FastAPI app entry point
└── ...
```

## 🔗 **After Deployment - Testing Guide**

### **1. Get Your Public URL**
After deployment, Render provides a URL like:
```
https://orders-inventory-api-xxxx.onrender.com
```

### **2. Test API Documentation**
```bash
# Open in browser - should show interactive API docs
https://your-service-url.onrender.com/docs

# Alternative documentation
https://your-service-url.onrender.com/redoc
```

### **3. Test Health Endpoint**
```bash
curl https://your-service-url.onrender.com/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "database": {
    "connected": true,
    "type": "sqlite",
    "url": "sqlite:///./orders_inventory.db"
  },
  "api_version": "1.0.0"
}
```

### **4. Test Product Creation**
```bash
# Create a new product
curl -X POST "https://your-service-url.onrender.com/products/" \
     -H "Content-Type: application/json" \
     -d '{
       "sku": "DEPLOY-TEST-001",
       "name": "Deployment Test Product",
       "price": 99.99,
       "stock": 50
     }'
```

**Expected Response (201 Created):**
```json
{
  "id": 1,
  "sku": "DEPLOY-TEST-001",
  "name": "Deployment Test Product",
  "price": 99.99,
  "stock": 50,
  "created_at": "2023-12-01T10:00:00Z",
  "updated_at": "2023-12-01T10:00:00Z"
}
```

### **5. Test Order Creation**
```bash
# Create an order for the product
curl -X POST "https://your-service-url.onrender.com/orders/" \
     -H "Content-Type: application/json" \
     -d '{
       "product_id": 1,
       "quantity": 2
     }'
```

**Expected Response (201 Created):**
```json
{
  "id": 1,
  "product_id": 1,
  "quantity": 2,
  "status": "PENDING",
  "created_at": "2023-12-01T10:01:00Z",
  "updated_at": "2023-12-01T10:01:00Z"
}
```

## 🚀 Deployment Steps

### **Method 1: GitHub Integration (Recommended)**

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "feat: Add Render deployment configuration"
   git push origin main
   ```

2. **Connect to Render:**
   - Go to [render.com](https://render.com)
   - Click "New +" → "Blueprint"
   - Connect your GitHub repository
   - Render automatically detects `render.yaml`

3. **Deploy:**
   - Review the configuration
   - Click "Apply"
   - Render builds and deploys automatically

### **Method 2: Manual Dashboard Setup**

If you prefer the dashboard approach:

1. **Create Web Service:**
   - Go to Render Dashboard
   - Click "New +" → "Web Service"
   - Connect repository

2. **Configure Service:**
   - **Name**: `orders-inventory-api`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install poetry && poetry config virtualenvs.create false && poetry install --only=main`
   - **Start Command**: `uvicorn src.orders_inventory.api.main:app --host 0.0.0.0 --port $PORT`

3. **Set Environment Variables:**
   - Add all the environment variables listed above
   - Set CORS_ORIGINS to your frontend domains

## 🔍 Monitoring and Troubleshooting

### **Check Deployment Status:**
```bash
# View deployment logs in Render dashboard
# Monitor service health
curl https://your-service-url.onrender.com/health
```

### **Common Issues:**

#### **Build Failures:**
- Check Python version compatibility
- Verify requirements.txt has all dependencies
- Ensure Poetry configuration is correct

#### **Start Command Failures:**
- Verify the Python path to your app
- Check that all imports work
- Ensure FastAPI app is named `app`

#### **Database Issues:**
- SQLite file permissions
- Database initialization on startup
- Connection string format

#### **CORS Issues:**
- Configure CORS_ORIGINS properly
- Check frontend domain matches
- Verify protocol (http vs https)

### **Performance Monitoring:**
- Use Render's built-in monitoring
- Monitor response times via `/health` endpoint
- Set up external monitoring (e.g., UptimeRobot)

## 📊 Production Considerations

### **Database Upgrade:**
For production, consider upgrading to PostgreSQL:

```yaml
# Add to render.yaml
services:
  - type: pserv
    name: orders-inventory-db
    runtime: postgresql
    databases:
      - name: orders_inventory
        user: orders_user
```

### **Environment Variables Security:**
- Use Render's environment variable encryption
- Never commit secrets to git
- Rotate secrets regularly
- Use different values for staging/production

### **Scaling:**
```yaml
# Add to render.yaml web service
scaling:
  minInstances: 1
  maxInstances: 3
  targetMemoryPercent: 70
  targetCPUPercent: 70
```

### **Custom Domain:**
- Configure custom domain in Render dashboard
- Set up SSL certificate (automatic with Render)
- Update CORS_ORIGINS to include custom domain

This deployment configuration ensures a robust, scalable, and maintainable production deployment! 🎯
