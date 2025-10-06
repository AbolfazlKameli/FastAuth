<h1 align="center">🚀 FastAuth</h1>

<p align="center">
A lightweight authentication system built with <b>FastAPI</b>, featuring JWT, verification codes, blacklist, password reset/change and more.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13-blue" />
  <img src="https://img.shields.io/badge/FastAPI-0.117.1-green?link=https://google.com" />
  <img src="https://img.shields.io/badge/PostgreSQL-17+-blue" />
  <img src="https://img.shields.io/badge/License-MIT-yellow" />
</p>

## ✨ Features

* 🔑 **JWT Authentication** (access & refresh tokens)
* 📧 **Email verification codes** (OTP-style)
* 🚫 **Blacklist system** (prevent spamming & abuse)
* 🔄 **Password change & reset flows**
* ⚡ **Async support** with FastAPI & SQLAlchemy
* 🛠 **Background tasks** powered by Celery
* 🗄 **PostgreSQL** database with migrations via Alembic
* 🧾 **Pydantic** for request/response validation



## 🛠 Tech Stack

* **[FastAPI](https://fastapi.tiangolo.com/):** Modern, fast (high-performance) web framework
* **[SQLAlchemy](https://www.sqlalchemy.org/):** ORM with async support
* **[Celery](https://docs.celeryq.dev/):** Distributed task queue for background jobs
* **[PostgreSQL](https://www.postgresql.org/):** Relational database
* **[Alembic](https://alembic.sqlalchemy.org/):** Database migrations
* **[Pydantic](https://docs.pydantic.dev/):** Data validation & serialization


## ⚙️ Installation

Clone the repository:

```bash
git clone https://github.com/AbolfazlKameli/FastAuth.git
cd FastAuth
```

Create your own `.env` file

```bash
cp .example.env envs/.dev.env
```

Create a virtual environment & install dependencies:

```bash
pipenv install 
```


## 📦 Database Migrations

Run migrations with Alembic:

```bash
alembic upgrade head
```


## ▶️ Running the App

Start the FastAPI server:

```bash
uvicorn src.main:app --reload
```

Start the Celery worker:

```bash
celery -A src.infrastructure worker -l info  
```


## 📚 API Documentation

Once running, open your browser at:

* Swagger UI → `http://localhost:8000/docs`
* ReDoc → `http://localhost:8000/redoc`


## 🚀 Roadmap

* [ ] Docker support
* [X] Rate limiting & IP-based throttling
* [ ] Social login (Google, GitHub, etc.)
* [ ] Automatic tests


## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

