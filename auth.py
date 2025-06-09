import streamlit as st
from database import Database

class AuthManager:
    def __init__(self):
        self.db = Database()
        
    def show_login_page(self):
        """Display login/signup page"""
        st.markdown("""
            <style>
            .auth-container {
                max-width: 400px;
                margin: auto;
                padding: 2rem;
                background-color: #f0f2f6;
                border-radius: 10px;
                margin-top: 5rem;
            }
            .auth-header {
                text-align: center;
                color: #1f77b4;
                margin-bottom: 2rem;
            }
            </style>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown('<div class="auth-container">', unsafe_allow_html=True)
            st.markdown('<h1 class="auth-header">🔐 Smart Money Tracker</h1>', unsafe_allow_html=True)
            
            tab1, tab2 = st.tabs(["Login", "Sign Up"])
            
            with tab1:
                self.show_login_form()
            
            with tab2:
                self.show_signup_form()
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    def show_login_form(self):
        """Display login form"""
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            remember_me = st.checkbox("Remember me")
            
            submit = st.form_submit_button("Login", use_container_width=True)
            
            if submit:
                if username and password:
                    success, user_id, email = self.db.verify_user(username, password)
                    
                    if success:
                        # Set session state
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.session_state.user_id = user_id
                        st.session_state.user_email = email
                        
                        if remember_me:
                            st.session_state.remember_me = True
                        
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
                else:
                    st.error("Please enter both username and password")
    
    def show_signup_form(self):
        """Display signup form"""
        with st.form("signup_form"):
            new_username = st.text_input("Choose Username")
            new_email = st.text_input("Email Address")
            new_password = st.text_input("Choose Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            
            submit = st.form_submit_button("Create Account", use_container_width=True)
            
            if submit:
                if not all([new_username, new_email, new_password, confirm_password]):
                    st.error("Please fill all fields")
                elif new_password != confirm_password:
                    st.error("Passwords do not match")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters")
                elif "@" not in new_email:
                    st.error("Please enter a valid email address")
                else:
                    success, message = self.db.create_user(new_username, new_password, new_email)
                    
                    if success:
                        st.success("Account created successfully! Please login.")
                    else:
                        st.error(message)
    
    def check_authentication(self):
        """Check if user is authenticated"""
        if "authenticated" not in st.session_state:
            st.session_state.authenticated = False
        
        return st.session_state.authenticated
    
    def logout(self):
        """Logout user"""
        for key in ['authenticated', 'username', 'user_id', 'user_email']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()