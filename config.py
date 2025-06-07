import os
from flask_sqlalchemy import SQLAlchemy

basedir = os.path.abspath(os.path.dirname(__file__))

DATABASE_URL = f"sqlite:///{os.path.join(basedir, 'pro.db')}"

db = SQLAlchemy()