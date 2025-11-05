# AI Financial Statement Generation System

A production-grade AI-powered workflow for generating financial statements from 2024 PDF templates and 2025 input data with zero-touch automation, comprehensive auditability, and client-side editing capabilities.

## 🏗️ Architecture Overview

### Technology Stack
- **AI Models**: Google Gemini 2.5 Pro/Flash, Grok 4 Fast (via OpenRouter)
- **Frontend**: Next.js (React) on Vercel
- **Backend**: Python serverless functions on Vercel
- **Database/Storage**: Supabase (PostgreSQL + Auth + Storage)
- **Monitoring**: Prometheus metrics
- **Deployment**: Vercel + Supabase

### Model Assignment Strategy
| Task | Model | Rationale |
|------|-------|-----------|
| PDF Vision Extraction | Gemini 2.5 Pro | Best-in-class OCR + layout understanding |
| Data Cleaning/Healing | Gemini 2.5 Flash | Fast, cost-effective for structured text |
| Semantic Mapping | Grok 4 Fast | 2M context window, superior reasoning |
| Code Generation | Gemini 2.5 Pro | Precise formatting control |
| Final Audit/QA | Grok 4 Fast | Deep financial logic, anomaly detection |

## 📁 Project Structure

```
SmartStatements/
├── backend/                    # Python serverless backend
│   ├── api/                   # Vercel API endpoints
│   │   └── process.py      # Main processing endpoint
│   ├── config/                 # Configuration management
│   │   └── settings.py
│   ├── models/                 # AI model clients
│   │   ├── gemini_client.py
│   │   └── grok_client.py
│   ├── utils/                  # Utility modules
│   │   ├── workflow_engine.py
│   │   ├── database_manager.py
│   │   ├── file_monitor.py
│   │   ├── metrics_collector.py
│   │   └── alert_system.py
│   └── requirements.txt        # Python dependencies
├── frontend/                   # Next.js frontend
│   ├── src/
│   │   └── app/
│   │       ├── layout.tsx
│   │       ├── page.tsx
│   │       ├── dashboard/
│   │       └── upload/
│   └── package.json
├── database/                   # Database schema
│   └── schema.sql
├── docs/                      # Documentation
├── vercel.json               # Vercel deployment config
└── README.md                 # This file
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm
- Python 3.9+
- Supabase account
- Google Gemini API key
- OpenRouter API key (for Grok 4 Fast)

### 1. Environment Setup

#### Backend Environment Variables
Create `.env` in `backend/`:
```env
GEMINI_API_KEY=your_gemini_api_key
OPENROUTER_API_KEY=your_openrouter_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_key
SMTP_SERVER=your_smtp_server
SMTP_USERNAME=your_smtp_username
SMTP_PASSWORD=your_smtp_password
ALERT_EMAIL=your_alert_email
```

#### Frontend Environment Variables
Create `.env.local` in `frontend/`:
```env
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

### 2. Database Setup

1. Create a new Supabase project
2. Run the SQL schema from `database/schema.sql` in Supabase SQL Editor
3. Set up authentication (Email/Password + Google OAuth)
4. Create storage buckets:
   - `uploads` (private) - Input files
   - `outputs` (public) - Generated PDFs and certificates

### 3. Backend Setup

```bash
cd backend
pip install -r requirements.txt
```

### 4. Frontend Setup

```bash
cd frontend
npm install
```

## 🔧 Development

### Running Backend Locally
```bash
cd backend
python api/process.py
```

### Running Frontend Locally
```bash
cd frontend
npm run dev
```

### File Monitoring
The system includes automatic file monitoring. Drop files into the `./input` directory to trigger processing.

## 📊 Features

### Core Workflow
1. **File Analysis & Routing** - Automatic detection of file type and year
2. **PDF Template Extraction** - Gemini 2.5 Pro vision with OCR fallback
3. **Data Healing** - Gemini 2.5 Flash for quality issues
4. **Semantic Mapping** - Grok 4 Fast for account mapping
5. **Statement Generation** - Gemini 2.5 Pro for Excel code generation
6. **Quality Assurance** - Grok 4 Fast for comprehensive audit
7. **Verification Certificate** - Complete audit trail with mathematical proofs

### Frontend Features
- **Dashboard** - Report listing and management
- **Upload Interface** - Drag-and-drop file handling
- **Edit Interface** - React-Table for financial grid editing
- **Preview/Export** - PDF generation and certificate download

### Monitoring & Metrics
- **Prometheus Metrics** - Real-time performance monitoring
- **SQLite Audit Trail** - Complete processing logs
- **Email Alerts** - Automatic notifications for issues
- **Health Checks** - System status monitoring

## 🚀 Deployment

### Vercel Deployment

1. **Install Vercel CLI**
```bash
npm i -g vercel
```

2. **Deploy Backend**
```bash
cd backend
vercel --prod
```

3. **Deploy Frontend**
```bash
cd frontend
vercel --prod
```

### Environment Variables in Vercel
Set the following in Vercel dashboard:
- `GEMINI_API_KEY`
- `OPENROUTER_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_KEY`
- `SMTP_SERVER`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `ALERT_EMAIL`

## 📈 Performance & Scaling

### Optimization Features
- **90%+ Token Savings** - Intelligent caching and Flash model usage
- **Parallel Processing** - Multi-threaded extraction and analysis
- **Auto-Scaling** - Vercel serverless infrastructure
- **Cost Efficiency** - Strategic model assignment based on task complexity

### Monitoring Dashboard
Access live metrics at: `http://localhost:8000/metrics`

### Cost Analysis
- **Vercel**: Free tier (sufficient for most use cases)
- **Supabase**: Starter plan (~$25/month)
- **AI APIs**: ~$0.01 per report (varies by usage)
- **Total**: ~$50-100/month for typical client loads

## 🔒 Security & Compliance

### Access Controls
- Row-Level Security (RLS) on all data
- User-specific file access
- JWT-based authentication
- Admin audit capabilities

### Data Protection
- Encrypted storage
- Secure API key management
- Rate limiting and usage monitoring
- GDPR compliance considerations

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

### Email Configuration Test
```bash
curl -X POST http://localhost:5000/api/test-email \
  -H "Content-Type: application/json" \
  -d '{}'
```

## 📚 API Documentation

### Main Processing Endpoint
```http
POST /api/process
Content-Type: application/json

{
  "file_path": "/path/to/file.pdf",
  "user_id": "user-uuid",
  "year": 2025
}
```

### Status Check
```http
GET /api/status/{report_id}
```

### User Reports
```http
GET /api/reports/{user_id}
```

### System Metrics
```http
GET /api/metrics
```

## 🔧 Configuration

### Model Thresholds
- **Auto-Map Threshold**: 0.85 (cosine similarity)
- **Review Threshold**: 0.7 (cosine similarity)
- **Cache TTL**: 1 hour
- **Max Workers**: 4 (parallel processing)

### File Processing Limits
- **Max File Size**: 50MB
- **Max PDF Pages**: 100
- **Supported Formats**: PDF, Excel (.xlsx, .xls)

## 🐛 Troubleshooting

### Common Issues

1. **PDF Extraction Fails**
   - Check file size and page count
   - Verify Gemini API key
   - Check OCR fallback configuration

2. **Email Alerts Not Working**
   - Verify SMTP configuration
   - Check email settings in environment
   - Test email configuration endpoint

3. **Database Connection Issues**
   - Verify Supabase URL and keys
   - Check RLS policies
   - Test database connection

### Debug Mode
Enable debug logging by setting:
```env
DEBUG=true
LOG_LEVEL=debug
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For support and questions:
- Create an issue in the repository
- Email: support@yourcompany.com
- Documentation: [Link to docs]

---

**Version**: 1.0.0  
**Last Updated**: November 5, 2025  
**Status**: Production Ready
