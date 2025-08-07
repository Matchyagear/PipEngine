# ShadowBeta Deployment Guide

## 🚀 Getting Your App Live on pipengine.com

### Prerequisites
- [ ] pipengine.com domain purchased and configured
- [ ] GitHub account (free)
- [ ] Vercel account (free)
- [ ] Railway account (free tier)
- [ ] MongoDB Atlas account (free tier)

### Step 1: Set Up MongoDB Atlas (Database)
1. Go to [MongoDB Atlas](https://www.mongodb.com/atlas)
2. Create free account
3. Create new cluster (free tier)
4. Create database user
5. Get connection string
6. Update `backend/.env` with your MongoDB connection string

### Step 2: Deploy Backend to Railway
1. Go to [Railway](https://railway.app)
2. Sign up with GitHub
3. Create new project
4. Connect your GitHub repository
5. Set environment variables in Railway dashboard:
   - Copy all variables from `backend/.env`
   - Replace placeholder values with real API keys
6. Deploy

### Step 3: Deploy Frontend to Vercel
1. Go to [Vercel](https://vercel.com)
2. Sign up with GitHub
3. Import your GitHub repository
4. Configure build settings:
   - Framework: Create React App
   - Root Directory: `frontend`
   - Build Command: `yarn build`
   - Output Directory: `build`
5. Set environment variables:
   - `REACT_APP_BACKEND_URL`: Your Railway backend URL
6. Deploy

### Step 4: Configure Domain
1. In Vercel dashboard, go to your project settings
2. Add custom domain: `pipengine.com`
3. Configure DNS settings as instructed by Vercel
4. Wait for DNS propagation (up to 24 hours)

### Step 5: Update Frontend Backend URL
1. Once backend is deployed, get the Railway URL
2. Update `frontend/.env` with the Railway URL
3. Redeploy frontend

### Step 6: Test Everything
1. Visit pipengine.com
2. Test all features
3. Check API endpoints
4. Verify database connections

## 🔧 Environment Variables Needed

### Backend (.env)
```
MONGO_URL=mongodb+srv://username:password@cluster.mongodb.net/shadowbeta
DB_NAME=shadowbeta
MONGODB_DISABLED=false
FINNHUB_API_KEY=your_key
GEMINI_API_KEY=your_key
OPENAI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
NEWS_API_KEY=your_key
ENVIRONMENT=production
```

### Frontend (.env)
```
REACT_APP_BACKEND_URL=https://your-backend.railway.app
```

## 💰 Cost Breakdown (Free Tier)
- **Vercel**: Free (100GB bandwidth/month)
- **Railway**: $5 free credit/month (enough for small apps)
- **MongoDB Atlas**: Free (512MB database)
- **Domain**: Already purchased

## 🚨 Important Notes
- Keep your API keys secure
- Monitor usage to stay within free tiers
- Set up monitoring for your production app
- Consider setting up automatic backups

## 🔄 Continuous Deployment
Once set up, every push to your main branch will automatically deploy to production!
