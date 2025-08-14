# 📸 Screenshots & Images Guide

This document shows different ways to include screenshots and images in markdown files.

## 🖼️ **Basic Image Syntax**

### **1. Local Images (Recommended)**
```markdown
![Alt Text](path/to/image.png)
![Screenshot Description](images/screenshot.png)
```

### **2. Images with Titles**
```markdown
![Alt Text](path/to/image.png "Title shown on hover")
```

### **3. Reference Style Images**
```markdown
![Alt Text][image-ref]

[image-ref]: path/to/image.png "Optional title"
```

## 📁 **Recommended Folder Structure**

```
orders-inventory/
├── screenshots.md
├── images/              # Create this folder
│   ├── screenshots/     # Screenshots subfolder
│   │   ├── api-docs.png
│   │   ├── health-check.png
│   │   └── product-creation.png
│   └── diagrams/        # Diagrams subfolder
│       └── architecture.png
└── docs/
    └── images/          # Alternative location
```

## 🎯 **Practical Examples for Your API**

### **API Documentation Screenshot**
```markdown
![FastAPI Swagger UI](images/screenshots/api-docs.png "Interactive API Documentation")
```

### **Health Check Response**
```markdown
![Health Check Endpoint](images/screenshots/health-check.png "API Health Status")
```

### **Product Creation Demo**
```markdown
![Creating a Product](images/screenshots/product-creation.png "POST /products/ endpoint")
```

### **Render Deployment**
```markdown
![Render Dashboard](images/screenshots/render-deployment.png "Successful Render.com deployment")
```

## 🔧 **Advanced Image Options**

### **HTML for Size Control**
```html
<img src="images/screenshot.png" alt="Description" width="600" height="400">
```

### **HTML with Alignment**
```html
<div align="center">
  <img src="images/screenshot.png" alt="Centered Image" width="80%">
</div>
```

### **Clickable Images (Links)**
```markdown
[![Click to view full size](images/thumbnail.png)](images/fullsize.png)
```

## 📱 **Different Image Formats**

### **Common Formats Supported**
- **PNG**: `![Screenshot](image.png)` - Best for screenshots
- **JPG/JPEG**: `![Photo](image.jpg)` - Good for photos
- **GIF**: `![Animation](demo.gif)` - For animated demos
- **SVG**: `![Diagram](diagram.svg)` - Scalable graphics
- **WebP**: `![Modern](image.webp)` - Modern format

## 🌐 **External Images (Use Carefully)**

### **Direct URLs**
```markdown
![External Image](https://example.com/image.png)
```

### **GitHub Raw URLs**
```markdown
![GitHub Image](https://raw.githubusercontent.com/user/repo/main/images/screenshot.png)
```

## 📋 **Step-by-Step: Adding Screenshots**

### **1. Create Images Folder**
```bash
mkdir -p images/screenshots
mkdir -p images/diagrams
```

### **2. Add Your Screenshots**
- Save screenshots to `images/screenshots/`
- Use descriptive names: `api-docs.png`, `health-check.png`

### **3. Reference in Markdown**
```markdown
## API Documentation
![Swagger UI showing all endpoints](images/screenshots/api-docs.png)

## Health Check
![Health endpoint returning status healthy](images/screenshots/health-check.png)

## Product Creation
![POST request creating a new product with 201 response](images/screenshots/product-creation.png)
```

## 🎨 **Best Practices**

### **File Naming**
- ✅ `api-docs.png` (descriptive, lowercase, hyphens)
- ✅ `health-check-response.png` 
- ❌ `Screenshot 2023-12-01 at 3.45.12 PM.png` (too verbose)

### **Alt Text Guidelines**
- ✅ Descriptive: `![API documentation showing all endpoints](image.png)`
- ✅ Context: `![Successful 201 response from POST /products](image.png)`
- ❌ Generic: `![Screenshot](image.png)`

### **Image Optimization**
- **Compress images** to reduce file size
- **Use appropriate dimensions** (max 1200px width for screenshots)
- **PNG for screenshots**, JPG for photos

## 🔄 **Live Example Template**

```markdown
# 🚀 Render.com Deployment Results

## 1. API Documentation
![FastAPI interactive documentation showing all endpoints](images/screenshots/swagger-ui.png)
*Interactive Swagger UI available at: https://your-app.onrender.com/docs*

## 2. Health Check
![Health endpoint returning healthy status](images/screenshots/health-check.png)
```json
{
  "status": "healthy",
  "database": {"connected": true, "type": "in-memory"},
  "api_version": "1.0.0"
}
```

## 3. Product Creation (201 Response)
![Creating a product via POST request](images/screenshots/product-creation.png)
```bash
curl -X POST "https://your-app.onrender.com/products/" \
     -H "Content-Type: application/json" \
     -d '{"sku": "TEST-001", "name": "Test Product", "price": 19.99, "stock": 50}'
```

**Response (201 Created):**
```json
{
  "id": 1,
  "sku": "TEST-001", 
  "name": "Test Product",
  "price": 19.99,
  "stock": 50,
  "created_at": "2023-12-01T10:00:00Z"
}
```
```

## 📝 **Quick Reference**

| Purpose | Syntax | Example |
|---------|--------|---------|
| Basic Image | `![Alt](path)` | `![API Docs](images/api.png)` |
| With Title | `![Alt](path "title")` | `![API](images/api.png "Swagger UI")` |
| HTML Sized | `<img src="path" width="600">` | `<img src="images/api.png" width="600">` |
| Clickable | `[![Alt](thumb)](full)` | `[![Thumb](small.png)](large.png)` |

## 🎯 **For Your Deployment Demo**

Create these specific screenshots:
1. **`images/screenshots/render-dashboard.png`** - Render deployment status
2. **`images/screenshots/api-docs.png`** - Swagger UI at `/docs`
3. **`images/screenshots/health-check.png`** - Health endpoint response
4. **`images/screenshots/product-creation.png`** - POST /products/ with 201 response
5. **`images/screenshots/curl-demo.png`** - Terminal showing curl commands

Then reference them in your documentation! 📸
