import bcrypt
from sqlalchemy.orm import Session
from app.models.models import User, AlertConfig, ScoreWeight
from app.auth.jwt_handler import create_access_token


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    pwd_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its hash."""
    pwd_bytes = plain_password.encode('utf-8')[:72]
    hash_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(pwd_bytes, hash_bytes)


def register_user(db: Session, name: str, email: str, password: str) -> User:
    """Register a new user with default settings.
    
    Raises ValueError if email already exists.
    """
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise ValueError("A user with this email already exists.")
    
    user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        theme="dark",
    )
    db.add(user)
    db.flush()
    
    # Create default alert config
    alert_config = AlertConfig(
        user_id=user.id,
        view_increase_threshold=25.0,
        view_decrease_threshold=20.0,
        engagement_low_threshold=3.0,
        follower_drop_threshold=10.0,
    )
    db.add(alert_config)
    
    # Create default score weights
    score_weight = ScoreWeight(
        user_id=user.id,
    )
    db.add(score_weight)
    
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> str:
    """Authenticate a user and return a JWT access token.
    
    Raises ValueError on invalid credentials.
    """
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        raise ValueError("Invalid email or password.")
    
    token = create_access_token(data={"sub": str(user.id), "email": user.email})
    return token
