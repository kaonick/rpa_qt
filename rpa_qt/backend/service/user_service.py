from smtplib import SMTP

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .auth_service import password_hash
from ..config import settings
from ..model.models import User
from fastapi import HTTPException
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from ..model.schemas import UserCreate, UserProfile

# def user_create(user_signup:UserCreate, db):
#     user = db.query(User).filter(User.email == user_signup.email).first()
#     if user:
#         raise HTTPException(
#             status_code=400, detail="This email has already exists")
#     new_user = User()
#     new_user.email=user_signup.email
#     new_user.password=password_hash(user_signup.password)
#     db.add(new_user)
#     db.commit()
#     db.refresh(new_user)
#     return new_user

async def user_create(user_signup:UserCreate, db:AsyncSession ):
    q = await db.execute(select(User).where(User.email == user_signup.email))
    user = q.scalars().first()
    if user:
        raise HTTPException(
            status_code=400, detail="This email has already exists")
    new_user = User()
    new_user.email=user_signup.email
    new_user.password=password_hash(user_signup.password)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

# {待完善}
async def user_profile_editor(user_profile:UserProfile,db:AsyncSession):
    q = await db.execute(select(User).where(User.email == user_profile.email))
    user = q.scalars().first()
    if user is None:
        raise HTTPException(
            status_code=400, detail="This user is not found")
    user.name=user_profile.name
    await db.commit()
    await db.refresh(user)
    return user




def send_email(receiver_email, data):
    sender_email = "your_email@example.com"
    sender_password = "your_password"
    subject = "Email Verification"
    body = f"Please verify your email by clicking the following link: {data['verification_link']}"

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    # Establish a connection with Gmail's SMTP server and send the email
    try:
        # Connect to Gmail's SMTP server
        server: SMTP = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()  # Encrypt the connection

        # Log in to your Gmail account
        server.login(sender_email, sender_password)

        # Send email
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)
        print("Email sent successfully!")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        # Terminate the SMTP session
        server.quit()

def send_email_outlook(receiver_email, data):
    sender_email = "kaonick@fpg.com.tw"
    sender_password = "20253Kaonick"
    subject = "Email Verification"
    body = f"Please verify your email by clicking the following link: {data['verification_link']}"

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    # Establish a connection with Gmail's SMTP server and send the email
    try:
        # Connect to Gmail's SMTP server
        server: SMTP = smtplib.SMTP('mail.fpg.com.tw', 25)
        server.starttls()  # Encrypt the connection

        # Log in to your Gmail account
        server.login(user="twfpg/N000000930", password=sender_password)

        # Send email
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)
        print("Email sent successfully!")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        # Terminate the SMTP session
        server.quit()


def send_email(subject,body,receiver_email):
    sender_email = settings.sender_email #"kaonick@fpg.com.tw"
    email_user= settings.mail_user #"twfpg/N000000930"
    sender_password = settings.mail_password #""
    # subject = "Email Verification"
    # body = f"Please verify your email by clicking the following link: {data['verification_link']}"

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    # Establish a connection with Gmail's SMTP server and send the email
    try:
        # Connect to Gmail's SMTP server
        server: SMTP = smtplib.SMTP(settings.smtp_server, settings.smtp_port)
        server.starttls()  # Encrypt the connection

        # Log in to your Gmail account
        server.login(user=email_user, password=sender_password)

        # Send email
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)
        print("Email sent successfully!")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        # Terminate the SMTP session
        server.quit()


