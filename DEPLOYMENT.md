# Streamlit Community Cloud Deployment Checklist

## ✅ Pre-Deployment Checklist

### 1. Code Issues Fixed
- [x] Created missing `advisor.py` module
- [x] Removed hardcoded database credentials
- [x] Updated all files to use Streamlit secrets
- [x] Added proper error handling for missing secrets
- [x] Updated `requirements.txt` with version pins
- [x] Fixed OpenAI API key configuration

### 2. Repository Setup
- [ ] Ensure repository is public (required for free Streamlit Cloud)
- [ ] Verify all code is committed and pushed to GitHub
- [ ] Check that sensitive files are in `.gitignore`:
  - `.streamlit/secrets.toml`
  - `*.db` files
  - `.env` files

### 3. Database Configuration
- [ ] PostgreSQL database is accessible from internet
- [ ] Database allows connections from Streamlit Cloud IPs
- [ ] Connection string includes `?sslmode=require` for Supabase
- [ ] Database tables are initialized (run `db.py` if needed)

### 4. API Keys
- [ ] OpenAI API key is ready (optional, for LLM features)
- [ ] API key has sufficient credits

## 🚀 Deployment Steps

### Step 1: Connect Repository
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click "New app"
4. Select repository: `cottonball95/LLM-Advisor`
5. Select branch: `main` (or your default branch)

### Step 2: Configure App Settings
- **Main file path**: `login.py`
- **Python version**: 3.12.7 (auto-detected from `runtime.txt`)

### Step 3: Add Secrets
Click "Advanced settings" → "Secrets" and add:

```toml
[connections.postgres]
url = "postgresql://postgres:YOUR_PASSWORD@db.lagyctcgaqulkpmflcjs.supabase.co:5432/postgres?sslmode=require"

[openai]
api_key = "sk-YOUR_OPENAI_API_KEY"
```

**Important**: Replace `YOUR_PASSWORD` and `YOUR_OPENAI_API_KEY` with actual values.

### Step 4: Deploy
Click "Deploy" and wait for the build to complete.

## 🔍 Post-Deployment Verification

1. **Check Build Logs**
   - Look for any import errors
   - Verify all packages installed correctly
   - Check for database connection issues

2. **Test the Application**
   - Visit the deployed URL
   - Test login functionality
   - Verify database connections work
   - Test student and advisor dashboards

3. **Monitor for Errors**
   - Check Streamlit Cloud logs regularly
   - Watch for API rate limits
   - Monitor database connection stability

## 🐛 Common Issues & Solutions

### Issue: "ModuleNotFoundError: No module named 'advisor'"
**Solution**: Ensure `advisor.py` is committed to the repository.

### Issue: "Database connection failed"
**Solution**: 
- Verify PostgreSQL connection string in secrets
- Check that database allows external connections
- Ensure SSL mode is set correctly

### Issue: "OpenAI API key not found"
**Solution**: 
- Verify API key is set in Streamlit secrets
- Check that key format is correct (starts with `sk-`)
- LLM features will gracefully degrade if key is missing

### Issue: "Port already in use"
**Solution**: This shouldn't happen on Streamlit Cloud, but if it does, check your `config.toml`.

## 📝 Notes

- The main entry point is `login.py`, not `app.py`
- `app.py` is a legacy SQLite-based version (optional)
- All database connections now use Streamlit secrets
- OpenAI features are optional and will work without API key (with reduced functionality)

## 🔐 Security Reminders

- Never commit `.streamlit/secrets.toml` to git
- Never commit database passwords or API keys
- Use Streamlit Cloud secrets for all sensitive data
- Regularly rotate API keys and passwords

