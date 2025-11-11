# Quiz Platform API


A Django REST Framework application.


## Features


JWT-based authentication

Redis caching for fast data retrieval

Admin-only endpoints



## Tech Stack


Backend: Django 4.2, Django REST Framework

Authentication: JWT (Simple JWT)

Database: PostgreSQL

Caching: Redis (django-redis)


## Installation


Option 1: Local Setup

Prerequisites


Python 3.11+

PostgreSQL 17+

Redis 7+


## Project Structure


```
quiz_platform/
├── apps/
│   ├── users/
│   |   ├── migrations/
│   |   ├── __init__.py
│   │   ├── models.py
│   │   ├── apps.py
│   │   ├── admin.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── permissions.py
│   └── quizzes/
│   |   ├── migrations/
│   |   ├── __init__.py
│   │   ├── utils.py.py
│   │   ├── apps.py
│   |   ├── models.py
│   |   ├── serializers.py
│   |   ├── views.py
│   |   ├── urls.py
│   |   ├── tasks.py
│   |   └── utils.py
├── quiz_platform/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── celery.py
├── manage.py
├── requirements.txt
└── .env
```


## Steps


Clone the repository


```bash 
git clone <repository-url> 
```
```bash 
cd quizz_platform 
```


## Create virtual environment


``` bash 
python -m venv venv 
```
``` bash 
source venv/bin/activate  # On Windows: venv\Scripts\activate
 ```


## Install dependencies


``` bash 
pip install -r requirements.txt 
```


## Create .env file


``` bash 
cp .env.example .env 
```


Edit .env with your configuration


Setup database


## Create PostgreSQL database 


``` bash 
createdb quiz_platform_db
```


## Run migrations


``` bash 
python manage.py makemigrations
```

``` bash 
python manage.py migrate 
```


## Create superuser (optional)


``` bash 
python manage.py createsuperuser
 ```


## Start Redis


```bash 
redis-server
```


# Run the application


## Open 4 terminal windows:

Terminal 1 - Django Server:

```bash
python manage.py runserver
```
Terminal 2 - Celery Worker:

```bash
celery -A quizz_platform worker --pool=solo --loglevel=info
```
Terminal 3 - Celery Beat (for periodic tasks):

```bash
celery -A quizz_platform beat --loglevel=info
```

The application will be available at http://localhost:8000


# API Endpoints

baseurl
``` http://localhost:8000/api/v1 ``` 

# API Docs URLs

Once your server is running (python manage.py runserver), you can view:

Swagger UI: 

```http://127.0.0.1:8000/api/schema/```



Redoc: 

```http://127.0.0.1:8000/api/redoc/```



Raw OpenAPI JSON:

 ```http://127.0.0.1:8000/api/docs/```




# Authentication

All endpoints (except register and login) require JWT authentication.
Add to request headers:


```Authorization: Bearer <your_access_token>```


## Authentication

## Register User

Request:

### 1. User Authentication Endpoints

1.1 Register User (Normal User)

``` POST /auth/register/ ```

Body (JSON):
```json
{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePass123!",
    "password2": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe",
    "is_admin": false
}

```


 1.2 Register Admin User

```POST /auth/register/```
Body (JSON):
```json
{
    "username": "admin_user",
    "email": "admin@example.com",
    "password": "AdminPass123!",
    "password2": "AdminPass123!",
    "first_name": "Admin",
    "last_name": "User",
    "is_admin": true
}
```

1.3 Login

```POST /auth/login/```
Body (JSON):

```json
{
    "username_or_email": "john_doe",
    "password": "SecurePass123!"
}
```
Response:

```json
{
    "message": "Login successful",
    "user": {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "role": "user",
        "created_at": "2024-01-01T00:00:00Z"
    },
    "tokens": {
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
    }
}
```

1.4 Get Current User Profile


```GET /users/me/```
Headers:

Authorization: Bearer <access_token>

1.5 Refresh Token

```POST /token/refresh/```
Body (JSON):

```json
{
    "refresh": "your_refresh_token_here"
}
```


2. Category Endpoints (Admin Only for Create/Update/Delete)


2.1 Create Category (Admin)

``` POST /categories/ ```

Headers:

Authorization: Bearer <admin_access_token>

Body (JSON):

```json
{
    "name": "Science",
    "description": "Science related quizzes",
    "is_active": true
}

```

2.2 List Categories

```GET /categories/```
Headers:

Authorization: Bearer <access_token>

2.3 Get Category Detail

```GET /categories/{id}/```

2.4 Update Category (Admin)

```PUT /categories/{id}/```

```PATCH /categories/{id}/```
Body (JSON):

```json
{
    "name": "Updated Science",
    "is_active": false
}
```


2.5 Delete Category (Admin)


```DELETE /categories/{id}/```

3. Quiz Endpoints

3.1 Create Quiz (Admin)

```POST /quizzes/```

Headers:

Authorization: Bearer <admin_access_token>

Body (JSON):

```json
{
    "title": "Basic Science Quiz",
    "description": "Test your basic science knowledge",
    "category": 1,
    "time_limit": 30,
    "passing_score": 60,
    "is_active": true
}
```

3.2 List All Quizzes


```GET /quizzes/```
Response (for users - without correct answers):


```json
[
    {
        "id": 1,
        "title": "Basic Science Quiz",
        "description": "Test your basic science knowledge",
        "category": 1,
        "category_name": "Science",
        "time_limit": 30,
        "passing_score": 60,
        "question_count": 5,
        "created_at": "2024-01-01T00:00:00Z"
    }
]

```

3.3 Get Quiz Detail

```GET /quizzes/{id}/```

Response (for admin - with correct answers):

```json
{
    "id": 1,
    "title": "Basic Science Quiz",
    "description": "Test your basic science knowledge",
    "category": 1,
    "category_name": "Science",
    "time_limit": 30,
    "passing_score": 60,
    "is_active": true,
    "created_by": "admin_user",
    "questions": [
        {
            "id": 1,
            "question_text": "What is the chemical symbol for water?",
            "option_a": "H2O",
            "option_b": "CO2",
            "option_c": "O2",
            "option_d": "N2",
            "correct_answer": "A",
            "marks": 1,
            "is_active": true
        }
    ],
    "question_count": 1,
    "created_at": "2024-01-01T00:00:00Z"
}
```

3.4 Update Quiz (Admin)


```PUT /quizzes/{id}/```

```PATCH /quizzes/{id}/```
Body (JSON):

```json
{
    "title": "Updated Science Quiz",
    "is_active": false
}
```

3.5 Add Question to Quiz (Admin)


```POST /quizzes/{quiz_id}/add_question/```
Body (JSON):

```json
{
    "question_text": "What is the chemical symbol for water?",
    "option_a": "H2O",
    "option_b": "CO2",
    "option_c": "O2",
    "option_d": "N2",
    "correct_answer": "A",
    "marks": 1,
    "is_active": true
}

```

4. Question Endpoints (Admin Only)

4.1 List All Questions


```GET /questions/```

4.2 Get Question Detail


```GET /questions/{id}/```

4.3 Update Question


```PUT /questions/{id}/``
```PATCH /questions/{id}/```

Body (JSON):

```json
{
    "question_text": "Updated question text?",
    "correct_answer": "B",
    "is_active": false
}
```

4.4 Delete Question

```DELETE /questions/{id}/```

5. Submission Endpoints


5.1 Submit Quiz Answers (User)

```POST /submissions/```

Headers:

Authorization: Bearer <user_access_token>

Body (JSON):

```json
{
    "quiz_id": 1,
    "answers": [
        {
            "question_id": 1,
            "selected_answer": "A"
        },
        {
            "question_id": 2,
            "selected_answer": "C"
        },
        {
            "question_id": 3,
            "selected_answer": "B"
        }
    ]
}
```
Response:

```json
{
    "id": 1,
    "user": "john_doe",
    "quiz_title": "Basic Science Quiz",
    "submitted_at": "2024-01-01T12:00:00Z",
    "score": 66.67,
    "total_marks": 3,
    "obtained_marks": 2,
    "passed": true,
    "answers": [
        {
            "question_text": "What is the chemical symbol for water?",
            "selected_answer": "A",
            "correct_answer": "A",
            "is_correct": true,
            "marks_obtained": 1
        },
        {
            "question_text": "What is photosynthesis?",
            "selected_answer": "C",
            "correct_answer": "B",
            "is_correct": false,
            "marks_obtained": 0
        }
    ]
}
```

5.2 List All Submissions

```GET /submissions/```

For Users: Returns only their submissions

For Admins: Returns all submissions

5.3 Get Submission Detail

```GET /submissions/{id}/```

5.4 Get My Submissions (User)

```GET /submissions/my_submissions/```



## Testing Flow

## For Normal Users:

Register as normal user

Login to get access token

View active quizzes

Get quiz details

Submit quiz answers

View submission history



## For Admin Users:

Register as admin user

Login to get access token

Create categories

Create quizzes

Add questions to quizzes

View all submissions

Get quiz statistics

Activate/deactivate quizzes or questions


## Environment Setup for Postman

Create Environment Variable:

```base_url: http://localhost:8000/api/v1```

access_token: (will be set after login)

refresh_token: (will be set after login)

## Auto-update tokens in Postman:

In the login request, add this to the Tests tab:

```javascript
javascriptvar jsonData = pm.response.json();
pm.environment.set("access_token", jsonData.tokens.access);
pm.environment.set("refresh_token", jsonData.tokens.refresh);
```

## Common HTTP Status Codes


200 OK: Successful GET, PUT, PATCH

201 Created: Successful POST (resource created)

400 Bad Request: Validation error

401 Unauthorized: Invalid or missing token

403 Forbidden: Insufficient permissions

404 Not Found: Resource not found

500 Internal Server Error: Server error


## Redis Caching


The following data is cached for performance:

Active categories (10 minutes)

Quiz lists (5 minutes)

User profiles (5 minutes)

User submissions (5 minutes)


Cache is automatically invalidated on updates.

