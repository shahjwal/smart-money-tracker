# Smart Money Flow Tracker

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Streamlit-1.29.0-red.svg" alt="Streamlit">
  <img src="https://img.shields.io/badge/Status-Active-success.svg" alt="Status">
</p>

<p align="center">
  <strong>Real-time options flow analyzer that detects unusual institutional trading activity and sends automated alerts</strong>
</p>

##  Overview

Smart Money Flow Tracker is a financial analytics platform that monitors the options market for unusual trading activity, helping retail investors identify when institutional investors ("smart money") are making significant trades. The system analyzes options volume, calculates unusual activity ratios, and sends real-time alerts for potential trading opportunities.

##  Key Features

- ** Real-time Options Scanning**: Monitors 10+ major stocks simultaneously for unusual options activity
- ** Unusual Activity Detection**: Identifies trades with 10-100x normal volume or >$1M premium
- ** Automated Email Alerts**: Sends HTML-formatted alerts when significant activity is detected
- ** Performance Tracking**: Tracks the success rate of alerts with historical performance data
- ** Interactive Visualizations**: 
  - Market sentiment gauge
  - 3D options flow visualization
  - Activity heatmaps
  - Performance analytics
- ** Secure Authentication**: User accounts with encrypted passwords and session management
- ** Data Persistence**: SQLite database for storing alerts and tracking performance

##  Tech Stack

- **Backend**: Python 3.8+
- **Frontend**: Streamlit
- **Data Source**: Yahoo Finance API (yfinance)
- **Database**: SQLite
- **Visualization**: Plotly
- **Email**: SMTP with HTML templates
- **Authentication**: Custom auth with bcrypt hashing

##  How It Works

1. **Data Collection**: Fetches real-time options data from Yahoo Finance
2. **Analysis**: Calculates volume-to-open-interest ratios to identify unusual activity
3. **Detection**: Flags trades exceeding thresholds (10x volume, $1M+ premium)
4. **Alerts**: Sends email notifications and stores in database
5. **Tracking**: Monitors stock performance post-alert to validate strategy

##  Quick Start

### Prerequisites

- Python 3.8 or higher
- Gmail account for email alerts (optional)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/smart-money-tracker.git
cd smart-money-tracker
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure email alerts (optional):
Create a `.env` file in the root directory:
```env
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_app_password
```

5. Run the application:
```bash
streamlit run app.py
```

6. Open browser and navigate to `http://localhost:8501`

##  Project Structure

```
smart-money-tracker/
│
├── app.py                 # Main Streamlit application
├── auth.py               # Authentication module
├── database.py           # Database operations
├── email_config.py       # Email configuration and templates
├── utils.py              # Data fetching and analysis utilities
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables (create this)
└── README.md            # Project documentation
```

##  Configuration

### Email Setup (Gmail)

1. Enable 2-factor authentication on your Gmail account
2. Generate an app-specific password
3. Add credentials to `.env` file

### Adjusting Detection Thresholds

Edit `utils.py` to modify detection sensitivity:

```python
# Minimum volume ratio (default: 10x normal volume)
VOLUME_RATIO_THRESHOLD = 10

# Minimum premium spent (default: $50,000)
PREMIUM_THRESHOLD = 50000
```

##  Monitored Metrics

- **Volume Ratio**: Current volume vs average volume
- **Premium Spent**: Total dollar value of options traded
- **Put/Call Ratio**: Market sentiment indicator
- **Success Rate**: Percentage of alerts leading to profitable moves
- **ROI**: Return on investment if all alerts were followed

