# FastAPI Google OAuth Project

This is a FastAPI project integrated with Google OAuth for authentication. It allows users to sign in with their Google accounts and access a simple web application.

## Features

- Google OAuth login and authentication.
- Redirect URL and session management.
- Configurable using external `.env` and `config.ini` files.
- Easy-to-extend FastAPI project structure.
```
/home/user/                  # Assuming this is your home directory or any external folder
├── data_requirements/
│   └── lite_driver_dot_in/  # External directory for your config files
│       ├── config.ini
│       └── .env
```

## Project Structure

```
project/ 
│ ├── app/ 
│ ├── init.py 
│ ├── main.py # FastAPI app logic 
│ ├── config.py # Configuration and settings 
│ └── static/ # Static assets (CSS, images, etc.) 
│ └── css/ 
│ └── icons/ 
├── templates/ # HTML templates for Jinja2 
│ ├── home.html 
│ └── welcome.html 
├── .env # Environment variables (for sensitive data) 
├── config.ini # External configuration settings 
└── requirements.txt # Python dependencies
```

## Prerequisites

Make sure you have the following installed:

- Python 3.8+
- pip (Python package installer)
- Virtual environment (recommended)




