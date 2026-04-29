import os

class Config:
    SECRET_KEY = os.urandom(24)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    
    ADMIN_USERNAME = 'admin'
    ADMIN_PASSWORD = 'admin123'
    
    GEMINI_API_KEY = 'AIzaSyCho6eThloiMDPiPgLw2Q6L6iFtW2Z9Iog'
    GEMINI_MODEL = 'gemini-2.5-flash-lite'
    
    YOLO_MODEL_PATH = 'models/bestglacier.pt'
    HYBRID_MODEL_PATH = 'models/hybrid_risk_model.pkl'
    
    LOW_RISK_THRESHOLD = 25
    MEDIUM_RISK_THRESHOLD = 60
    
    DATABASE_PATH = 'database/glacier_analysis.db'