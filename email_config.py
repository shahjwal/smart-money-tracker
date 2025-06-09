import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

class EmailManager:
    def __init__(self):
        # Email configuration - You'll need to set these in .env file
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = os.getenv("SENDER_EMAIL", "")
        self.sender_password = os.getenv("SENDER_PASSWORD", "")
        
    def send_alert_email(self, recipient_email, alert_data):
        """Send alert email to user"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"🚨 Smart Money Alert: {alert_data['symbol']} - {alert_data['alert_type']}"
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            
            # Create HTML content
            html_content = self.create_html_email(alert_data)
            
            # Attach HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            if self.sender_email and self.sender_password:
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.sender_email, self.sender_password)
                    server.send_message(msg)
                return True
            else:
                print("Email credentials not configured")
                return False
                
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return False
    
    def create_html_email(self, alert_data):
        """Create HTML email template"""
        return f"""
        <html>
            <head>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        background-color: #f4f4f4;
                        margin: 0;
                        padding: 0;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: 20px auto;
                        background-color: #ffffff;
                        border-radius: 10px;
                        overflow: hidden;
                        box-shadow: 0 0 10px rgba(0,0,0,0.1);
                    }}
                    .header {{
                        background-color: #1f77b4;
                        color: white;
                        padding: 20px;
                        text-align: center;
                    }}
                    .content {{
                        padding: 30px;
                    }}
                    .alert-box {{
                        background-color: #fff3cd;
                        border: 1px solid #ffeaa7;
                        border-radius: 5px;
                        padding: 15px;
                        margin: 20px 0;
                    }}
                    .details {{
                        background-color: #f8f9fa;
                        padding: 15px;
                        border-radius: 5px;
                        margin: 15px 0;
                    }}
                    .metric {{
                        display: inline-block;
                        margin: 10px 20px 10px 0;
                    }}
                    .metric-label {{
                        color: #666;
                        font-size: 12px;
                    }}
                    .metric-value {{
                        font-size: 18px;
                        font-weight: bold;
                        color: #1f77b4;
                    }}
                    .footer {{
                        background-color: #f8f9fa;
                        padding: 20px;
                        text-align: center;
                        color: #666;
                        font-size: 12px;
                    }}
                    .button {{
                        display: inline-block;
                        padding: 10px 20px;
                        background-color: #1f77b4;
                        color: white;
                        text-decoration: none;
                        border-radius: 5px;
                        margin: 10px 0;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🚨 Smart Money Flow Alert</h1>
                        <p>Unusual Trading Activity Detected</p>
                    </div>
                    
                    <div class="content">
                        <div class="alert-box">
                            <h2 style="margin-top: 0;">Alert Summary</h2>
                            <p><strong>{alert_data['message']}</strong></p>
                        </div>
                        
                        <div class="details">
                            <h3>📊 Trading Details</h3>
                            
                            <div class="metric">
                                <div class="metric-label">Symbol</div>
                                <div class="metric-value">{alert_data['symbol']}</div>
                            </div>
                            
                            <div class="metric">
                                <div class="metric-label">Alert Type</div>
                                <div class="metric-value">{alert_data['alert_type']}</div>
                            </div>
                            
                            <div class="metric">
                                <div class="metric-label">Current Price</div>
                                <div class="metric-value">${alert_data.get('current_price', 'N/A')}</div>
                            </div>
                            
                            {self._format_details(alert_data.get('details', {}))}
                        </div>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <p style="color: #666;">Detected at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} EST</p>
                        </div>
                    </div>
                    
                    <div class="footer">
                        <p><strong>Disclaimer:</strong> This alert is for informational purposes only and should not be considered as financial advice.</p>
                        <p>Smart Money Flow Tracker | Automated Alert System</p>
                    </div>
                </div>
            </body>
        </html>
        """
    
    def _format_details(self, details):
        """Format additional details for email"""
        if not details:
            return ""
        
        html = "<div style='margin-top: 15px;'>"
        
        if 'volume' in details:
            html += f"""
                <div class="metric">
                    <div class="metric-label">Volume</div>
                    <div class="metric-value">{details['volume']:,}</div>
                </div>
            """
        
        if 'volume_ratio' in details:
            html += f"""
                <div class="metric">
                    <div class="metric-label">Volume Ratio</div>
                    <div class="metric-value">{details['volume_ratio']}x normal</div>
                </div>
            """
        
        if 'option_type' in details:
            html += f"""
                <div class="metric">
                    <div class="metric-label">Option Type</div>
                    <div class="metric-value">{details['option_type']}</div>
                </div>
            """
        
        if 'strike' in details:
            html += f"""
                <div class="metric">
                    <div class="metric-label">Strike Price</div>
                    <div class="metric-value">${details['strike']}</div>
                </div>
            """
        
        if 'premium' in details:
            html += f"""
                <div class="metric">
                    <div class="metric-label">Total Premium</div>
                    <div class="metric-value">${details['premium']:,.0f}</div>
                </div>
            """
        
        html += "</div>"
        return html