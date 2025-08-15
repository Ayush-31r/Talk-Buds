# TalkBuds

TalkBuds is an online platform that enables users to engage in **topic-based discussions** within chat groups, supporting multiple users simultaneously. The platform features **robust user authentication**, allowing secure creation and management of active chat rooms.

## Requirements

- Python 3.10+ (recommended)
- Django >= 4.2, < 5.0
- channels >= 4.0, < 5.0
- channels-redis >= 4.1, < 5.0
- psycopg2-binary >= 2.9, < 3.0
- redis >= 5.3.0, < 6.0
- djangorestframework >= 3.15, < 4.0
- djangorestframework-simplejwt >= 6.0, < 7.0
- django-allauth >= 1.15, < 2.0
- python-dotenv >= 1.0, < 2.0
- asgiref >= 3.7, < 4.0
- django-crispy-forms >= 2.1, < 3.0
- loguru >= 0.7, < 1.0

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/yourusername/talkbuds.git
   cd talkbuds

2. **Create a virtual environment:**

   ```bash
   python -m venv venv


3. **Activate the virtual environment:**

   - On macOS/Linux:

     ```bash
     source venv/bin/activate
     ```

   - On Windows:

     ```bash
     venv\Scripts\activate

4. **Install dependencies:**

   ```bash
   pip install -r requirements.txt


5. **Set up environment variables:**

   ```bash
   # Create a .env file in the project root and add your configurations
   touch .env

6. **Apply migrations:**

   ```bash
   python manage.py migrate

7. **Run the development server:**

   ```bash
   python manage.py runserver


## Contributing

1. **Fork the repository.**

2. **Create a new branch:**

   ```bash
   git checkout -b feature-name

3. **Commit your changes:**

    ```bash
    git commit -m 'Add feature'

4. **Push to the branch:**

    ```bash
    git push origin feature-name

5. **Open a Pull Request.**



