# lf12project2024-2025-BE
Backend for our school project

## Table of Contents
- [Introduction](#introduction)
- [Features](#features)
- [Installation](#installation)
- [API Endpoints](#api-endpoints)

## Introduction
This is the backend for the CrossSolver (name subject to change), a school project aimed at creating a crossword puzzle solver. The backend is built using Django and Django REST framework.

## Features
- Upload crossword images
- Retrieve crossword original and solved iamges
- Delete crossword entries

## Requirements
Download and install [Python3.11](https://www.python.org/downloads/release/python-31111/)

## Installation
1. **Clone the repository:**
    ```sh
    git clone https://github.com/Clashy13/lf12_project2024-2025-BE.git
    ```
    ```sh
    cd lf12project2024-2025-BE
    ```

2. **Create and activate a virtual environment:**
    ```sh
    python3.11 -m venv .venv
    ```
    On Linux & MacOS use
    ```sh
    source .venv/bin/activate 
    ```
    On Windows use
    ```sh
    .venv\Scripts\activate
    ```

3. **Install the dependencies:**
    ```sh
    pip install -r requirements.txt
    ```
  
4. **Install spaCy model**
    ```sh
    python -m spacy download de_core_news_lg
    ```

5. **Apply migrations:**
    ```sh
    python manage.py makemigrations lf12_crosswordReader_backend
   ```
    ```sh
    python manage.py migrate lf12_crosswordReader_backend
   ```

6. **Run the server:**
    ```sh
    python manage.py runserver
    ```


## API Endpoints
API documentation is available at:
- **Swagger UI:** `http://127.0.0.1:8000/`
- **Redoc:** `http://127.0.0.1:8000/api/schema/redoc/`

#### Overview of Crosswords
- **URL:** `/crosswords/overview/`
- **Method:** `GET`
- **Description:** Retrieve an overview of all crossword images with search and pagination.
- **Parameters:**
  - `limit` (optional): Number of results to return per page.
  - `offset` (optional): The initial index from which to return the results.
  - `title` (optional): Filter results by title.

#### Upload Crossword Image
- **URL:** `/crosswords/upload/`
- **Method:** `POST`
- **Description:** Upload a new crossword image.
- **Request Body:**
- `original_image` (file): The crossword image file to be uploaded for solving.

#### Get Crossword (original or solved) Image
- **URL:** `/crosswords/{id}/image/`
- **Method:** `GET`
- **Description:** Get a specific crossword image by ID and image type.
- **Query Parameters:**
  - `image_type` (required): `0` for original image, `1` for solved image.

#### Delete Crossword
- **URL:** `/crosswords/{id}/delete/`
- **Method:** `DELETE`
- **Description:** Delete a specific crossword entry by ID.
