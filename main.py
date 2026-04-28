# # ==============================
# # 📚 LIBRARY API 
# # ==============================


from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Render is working"}

# from fastapi import FastAPI, HTTPException, Depends
# from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
# from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, DateTime
# from sqlalchemy.orm import sessionmaker, declarative_base, Session
# from pydantic import BaseModel
# from datetime import datetime, timedelta
# from jose import jwt, JWTError
# from passlib.context import CryptContext
# import os



# SECRET_KEY = os.getenv("SECRET_KEY", "mysecretkey")
# ALGORITHM = "HS256"

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")



# DATABASE_URL = "sqlite:///./library.db"

# engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
# SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
# Base = declarative_base()



# class User(Base):
#     __tablename__ = "users"
#     id = Column(Integer, primary_key=True)
#     name = Column(String)
#     password = Column(String)
#     role = Column(String, default="student")

# class Book(Base):
#     __tablename__ = "books"
#     id = Column(Integer, primary_key=True)
#     title = Column(String)
#     author = Column(String)
#     category = Column(String)
#     available = Column(Boolean, default=True)

# class Borrow(Base):
#     __tablename__ = "borrowed_books"
#     id = Column(Integer, primary_key=True)
#     user_id = Column(Integer)
#     book_id = Column(Integer)
#     due_date = Column(DateTime)

# Base.metadata.create_all(bind=engine)



# app = FastAPI(title="Limkokwing Library")



# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()



# def hash_password(password: str):
#     return pwd_context.hash(password)

# def verify_password(plain, hashed):
#     return pwd_context.verify(plain, hashed)

# def create_token(data: dict):
#     return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

# def get_current_user(token: str = Depends(oauth2_scheme)):
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         return payload
#     except JWTError:
#         raise HTTPException(status_code=401, detail="Invalid token")


# def require_admin(user=Depends(get_current_user)):
#     if user.get("role") != "admin":
#         raise HTTPException(status_code=403, detail="Admin only")
#     return user



# class UserCreate(BaseModel):
#     name: str
#     password: str
#     role: str = "student"

# class BookCreate(BaseModel):
#     title: str
#     author: str
#     category: str

# class BorrowRequest(BaseModel):
#     user_id: int
#     book_id: int



# @app.post("/users")
# def create_user(user: UserCreate, db: Session = Depends(get_db)):
#     new_user = User(
#         name=user.name,
#         password=hash_password(user.password),
#         role=user.role
#     )
#     db.add(new_user)
#     db.commit()
#     db.refresh(new_user)
#     return {"message": "User created"}

# @app.post("/login")
# def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):

#     user = db.query(User).filter(User.name == form_data.username).first()

#     if not user or not verify_password(form_data.password, user.password):
#         raise HTTPException(status_code=401, detail="Invalid credentials")

#     token = create_token({
#         "sub": user.name,
#         "role": user.role
#     })

#     return {"access_token": token, "token_type": "bearer"}



# @app.get("/users")
# def get_users(user=Depends(require_admin), db: Session = Depends(get_db)):
#     return db.query(User).all()

# @app.post("/books")
# def create_book(book: BookCreate, user=Depends(require_admin), db: Session = Depends(get_db)):
#     new_book = Book(**book.dict())
#     db.add(new_book)
#     db.commit()
#     db.refresh(new_book)
#     return new_book



# @app.get("/books")
# def get_books(user=Depends(get_current_user), db: Session = Depends(get_db)):
#     return db.query(Book).all()



# @app.post("/borrow")
# def borrow_book(req: BorrowRequest, user=Depends(get_current_user), db: Session = Depends(get_db)):

#     book = db.query(Book).filter(Book.id == req.book_id).first()

#     if not book:
#         raise HTTPException(status_code=404, detail="Book not found")

#     if not book.available:
#         raise HTTPException(status_code=400, detail="Not available")

#     book.available = False

#     borrow = Borrow(
#         user_id=req.user_id,
#         book_id=req.book_id,
#         due_date=datetime.now() + timedelta(days=7)
#     )

#     db.add(borrow)
#     db.commit()

#     return {"message": "Book borrowed"}



# @app.post("/return")
# def return_book(req: BorrowRequest, user=Depends(get_current_user), db: Session = Depends(get_db)):

#     borrow = db.query(Borrow).filter(
#         Borrow.user_id == req.user_id,
#         Borrow.book_id == req.book_id
#     ).first()

#     if not borrow:
#         raise HTTPException(status_code=400, detail="Not borrowed")

#     book = db.query(Book).filter(Book.id == req.book_id).first()

#     days_late = (datetime.now() - borrow.due_date).days
#     fine = max(0, days_late * 2)

#     book.available = True
#     db.delete(borrow)
#     db.commit()

#     return {"message": "Returned", "fine": fine}



# print("Library API running...")