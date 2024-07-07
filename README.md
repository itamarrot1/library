# Library Management System

This project is a Flask-based Library Management System (LMS) that allows users to manage books, loans, and user accounts through a RESTful API.

## Table of Contents

- [About](#about)
- [Features](#features)
- [Technologies Used](#technologies-used)
- [Setup Instructions](#setup-instructions)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Endpoints](#endpoints)
  - [Authentication](#authentication)
  - [User Management](#user-management)
  - [Book Management](#book-management)
  - [Loan Management](#loan-management)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgements](#acknowledgements)

## About

The Library Management System is designed to facilitate the management of books, loans, and user accounts. It provides endpoints for adding books, registering users, managing loans, and more.

## Features

- User registration and authentication using JWT tokens
- CRUD operations for books and users
- Book loan management with due dates and return functionality
- Admin access for managing users and books

## Technologies Used

- Flask
- SQLAlchemy
- Flask-JWT-Extended
- Flask-CORS
- SQLite (for local development)
- Werkzeug

## Setup Instructions

1. clone repository 

2. open virtual env

3.install requirements 

pip install -r requirements.txt

4. run flask server

## if you create a new user he will not be an admin 
to see the admin Permissions 
username : itamar 
password : ir123

