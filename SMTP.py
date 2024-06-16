
from sqlalchemy.orm import Session
import smtplib
from email.message import EmailMessage
import os 
from dotenv import load_dotenv
from fastapi import  HTTPException
from crud import create_URLToken
from security import encrypt_token, generate_otp
import models, crud
import pyotp, time

#sending SMTP
load_dotenv()

USER_EMAIL = os.getenv("USER_EMAIL")
USER_PASSWORD = os.getenv("USER_PASSWORD")

def send_Email(recipientEmail:str, subject:str, message:str):
    try:

        msg = EmailMessage()
        msg['Subject'] = subject
        msg["From"] = USER_EMAIL
        msg["To"] = recipientEmail
        msg.set_content(message, subtype ="html")

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(USER_EMAIL, USER_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("Email sent successfully")

    except Exception as e:
        print(f"Failed to send email: {e}")
        raise HTTPException(status_code=500, detail="Failed to send email.")
    
def send_setPassEmail(user: models.User, db:Session):

    url_token = crud.create_URLToken(db, userid=user.UserID) #24 hrs
    encrypted = encrypt_token(url_token.value)


    subject = " Welcome to the Mori Web App!"
    setup_link = f"http://localhost:5173/setpassword?token={encrypted}"
    message= f"""
                 <html>
        <body>
    <div id="email">
        
        <img src="https://i.imgur.com/YAJcRx0.png" alt="Descriptive Text" style="width: 100%;" />
               
       
        <h1>Welcome to the Mori App!</h1>
        <p>Hello {user.FirstName},</p>
        <p>To complete the registration process and ensure the security of your account, we kindly ask you to set up your password by clicking on the link below:</p>
        <p><a href="{setup_link}">{setup_link}</a></p>
        <p>Mori Team</p>
             
            </div>
        </body>
        </html>

            """
    send_Email(user.Email, subject, message)
    
def send_OTP(user: models.User):
    key = user.secret_key

 
    otp = generate_otp(key)


    subject = f"OTP Code: {otp}"
   
    message= f"""
                 <html>
        <body>
    <div id="email">
        
        <img src="https://i.imgur.com/YAJcRx0.png" alt="Descriptive Text" style="width: 100%;" />
        <p>Hello {user.FirstName},</p>
        <p>We have received a request to log in to your account. Use the OTP code below to enter:</p>
        <h1 style="text-align:center; font-weight: bold;">{otp}</h1>
        <p>If you did not make any request, you can kindly ignore this email. <b>This code will expire in 2 minutes!</b></p>
        
        <p>Mori Team</p>
             
            </div>
        </body>
        </html>

            """
    send_Email(user.Email, subject, message)


def send_resetPassword_OTP(user: models.User):
    key = user.secret_key
    print(key)
 
    otp = generate_otp(key)


    subject = f" Reset Password Request"
   
    message= f"""
                 <html>
        <body>
    <div id="email">
        
        <img src="https://i.imgur.com/YAJcRx0.png" alt="Descriptive Text" style="width: 100%;" />
        <p>Hello {user.FirstName},</p>
        <p>We've received a request to reset your password. Please use the OTP code provided below to continue with the process.</p>
        <h1 style="text-align:center; font-weight: bold;">{otp}</h1>
        <p>If you did not make any request, you can kindly ignore this email. <b>This code will expire in 2 minutes!</b></p>
        
        <p>Mori Team</p>
             
            </div>
        </body>
        </html>

            """
    send_Email(user.Email, subject, message)