# Instead

Instead is an AI-powered Flask web application that helps students and newcomers discover personalized local businesses, services, and places based on their preferences, budget, and location.

> **Status:**  Early development

## Tech Stack

- Flask
- Python
- HTML/CSS/JavaScript
- SQLite (Development)
- OpenAI API *(planned)*

## Project Structure

```text
cityguide-ai/
├── app/
│   ├── routes/          # Application routes
│   ├── services/        # Business logic & AI services
│   ├── static/          # CSS, JavaScript, images
│   ├── templates/       # Jinja templates
│   ├── models.py        # Database models
│   └── __init__.py      # Flask application factory
│
├── instance/            # Local database
├── migrations/          # Database migrations
├── tests/               # Unit & integration tests
│
├── config.py            # Application configuration
├── run.py               # Application entry point
├── requirements.txt     # Project dependencies
└── README.md
```

## Getting Started

```bash
git clone <repository-url>
cd cityguide-ai

python -m venv .venv
source .venv/bin/activate    # macOS/Linux
# .venv\Scripts\activate     # Windows

pip install -r requirements.txt
python run.py
```

## Contributing

Create a feature branch, commit your changes, and open a pull request. Direct commits to `main` are protected.
