
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
import os



app = FastAPI(title="LIMKOKWING Library API")

SECRET_KEY = os.getenv("SECRET_KEY", "Festus")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")



DATABASE_URL = "sqlite:///./library.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()



class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    password = Column(String)
    role = Column(String, default="student")


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    author = Column(String)
    category = Column(String)
    available = Column(Boolean, default=True)


class Borrow(Base):
    __tablename__ = "borrows"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    book_id = Column(Integer)
    due_date = Column(DateTime)



@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)




def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)


def create_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")

        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = db.query(User).filter(User.name == username).first()

        if user is None:
            raise HTTPException(status_code=401, detail="User not found")

        return user

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def require_admin(user: User = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return user



class UserCreate(BaseModel):
    name: str
    password: str
    role: str = "student"


class BookCreate(BaseModel):
    title: str
    author: str
    category: str


class BorrowRequest(BaseModel):
    book_id: int




# Root
@app.get("/")
def home():
    return {"message": "Library API is running 🚀"}



@app.post("/users")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.name == user.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    new_user = User(
        name=user.name,
        password=hash_password(user.password),
        role=user.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User created successfully"}


@app.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.name == form_data.username).first()

    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token({
        "sub": user.name,
        "role": user.role
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }



@app.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@app.get("/users")
def get_users(user: User = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(User).all()



@app.post("/books")
def create_book(
    book: BookCreate,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    new_book = Book(**book.dict())
    db.add(new_book)
    db.commit()
    db.refresh(new_book)

    return new_book


@app.get("/books")
def get_books(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Book).all()


@app.get("/books/search")
def search_books(query: str, db: Session = Depends(get_db)):
    return db.query(Book).filter(Book.title.contains(query)).all()



@app.post("/borrow")
def borrow_book(
    req: BorrowRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    book = db.query(Book).filter(Book.id == req.book_id).first()

    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    if not book.available:
        raise HTTPException(status_code=400, detail="Book not available")

    book.available = False

    borrow = Borrow(
        user_id=current_user.id,
        book_id=req.book_id,
        due_date=datetime.now() + timedelta(days=7)
    )

    db.add(borrow)
    db.commit()

    return {"message": "Book borrowed successfully"}


@app.get("/my-books")
def my_books(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Borrow).filter(Borrow.user_id == current_user.id).all()


@app.post("/return")
def return_book(
    req: BorrowRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    borrow = db.query(Borrow).filter(
        Borrow.user_id == current_user.id,
        Borrow.book_id == req.book_id
    ).first()

    if not borrow:
        raise HTTPException(status_code=400, detail="Book not borrowed")

    book = db.query(Book).filter(Book.id == req.book_id).first()

    days_late = (datetime.now() - borrow.due_date).days
    fine = max(0, days_late * 2)

    book.available = True
    db.delete(borrow)
    db.commit()

    return {"message": "Book returned", "fine": fine}



@app.get("/admin/stats")
def stats(user: User = Depends(require_admin), db: Session = Depends(get_db)):
    return {
        "users": db.query(User).count(),
        "books": db.query(Book).count(),
        "borrowed": db.query(Borrow).count()
    }