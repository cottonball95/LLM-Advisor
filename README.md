# AI Academic Advisor — Hybrid (Streamlit + PostgreSQL + OpenAI)

An AI-powered academic advising system built with Streamlit that helps students plan their course schedules using deterministic eligibility rules and optional OpenAI-powered recommendations.

## Features

- **Student Dashboard**: View programs, mark completed courses, and get AI-generated multi-term schedules
- **Advisor Dashboard**: Manage academic programs, sections, and courses
- **Hybrid Planning**: Combines deterministic prerequisite checking with optional LLM-based scheduling recommendations
- **Multi-term Planning**: Generate semester-by-semester course plans

## Prerequisites

- Python 3.12.7 (see `runtime.txt`)
- PostgreSQL database (Supabase recommended)
- OpenAI API key (optional, for LLM features)

## Create Virtual Environment
Create a folder for your project, Open command prompt and update the directory location: 

cd "C:\path\to\your\project"

python -m venv .venv

.venv\Scripts\activate


## Local Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/cottonball95/LLM-Advisor.git
   cd LLM-Advisor
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure secrets**
   
   Create `.streamlit/secrets.toml` in the parent directory (create a folder called ".streamlit" and in that folder create a text file with the '.toml' extension:
   ```toml
  Paste the content from this file (https://drive.google.com/file/d/1oNGDBiUaSk4cW96DhTStIZ3w5sqmm8El/view?usp=drive_link)  into the secrets.toml file. This constains the API keys and database connections.

4. **Initialize the database** (if needed)
   ```bash
   python db.py
   ```

5. **Run the application**
   ```bash
   streamlit run login.py
   ```
   
   The app will start at `http://localhost:8501`

## Deployment to Streamlit Community Cloud

### Step 1: Prepare Your Repository

1. **Ensure all files are committed and pushed to GitHub**
   ```bash
   git add .
   git commit -m "Prepare for Streamlit Cloud deployment"
   git push origin main
   ```

2. **Verify your repository is public** (required for free tier)

### Step 2: Configure Streamlit Cloud Secrets

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with your GitHub account
3. Click "New app"
4. Select your repository (`cottonball95/LLM-Advisor`)
5. Set **Main file path** to: `login.py`
6. Click "Advanced settings"
7. Add secrets in the format:
   ```toml
   [connections.postgres]
   url = "postgresql://user:password@host:port/database?sslmode=require"
   
   [openai]
   api_key = "sk-your-api-key-here"
   ```
8. Click "Deploy"

### Step 3: Verify Deployment

- The app will build and deploy automatically
- Check the logs for any errors
- Visit your app URL (e.g., `https://your-app-name.streamlit.app`)

## Project Structure

```
├── login.py                    # Main entry point (login page)
├── app.py                      # Legacy SQLite-based advisor (optional)
├── db.py                       # Database initialization
├── llm.py                      # OpenAI integration
├── advisor.py                  # Course eligibility and scheduling logic
├── prereq.py                   # Prerequisite evaluation
├── utils_db.py                 # Database utilities
├── pages/
│   ├── 1_Advisor_Dashboard.py  # Advisor interface
│   └── 2_Student_Dashboard.py  # Student interface
├── requirements.txt            # Python dependencies
├── runtime.txt                 # Python version
└── README.md                   # This file
```

## Configuration Files

- **`.streamlit/config.toml`**: Streamlit configuration (optional)
- **`.streamlit/secrets.toml`**: Local secrets (DO NOT commit to git)
- **`requirements.txt`**: Python package dependencies
- **`runtime.txt`**: Python version specification

## Troubleshooting

### Database Connection Issues
- Verify your PostgreSQL connection string is correct
- Ensure SSL mode is set to `require` for Supabase
- Check that your database allows connections from Streamlit Cloud IPs

### OpenAI API Errors
- Verify your API key is correct and has credits
- Check that the `openai` package is installed
- LLM features will gracefully degrade if API key is missing

### Import Errors
- Ensure all dependencies in `requirements.txt` are installed
- Check that Python version matches `runtime.txt` (3.12.7)

## Security Notes

⚠️ **IMPORTANT**: Never commit secrets or credentials to git!

- Add `.streamlit/secrets.toml` to `.gitignore`
- Use Streamlit Cloud secrets for production
- Use environment variables for local development

## License

This project is part of ENGT 434/435 coursework at Old Dominion University.
