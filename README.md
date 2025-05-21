# travel-plan
A comprehensive travel planning application built with Flask that helps users organize their trips, track expenses, and manage travel tasks.

## Features

- User authentication (login/register)
- Trip management
- Expense tracking
- To-do lists
- Interactive map visualization
- Responsive design with Tailwind CSS

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/wanderlust.git
   cd wanderlust
   python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install flask werkzeug
python app.py
Access the application at: http://localhost:5000
wanderlust/
├── app.py
├── templates/
│   ├── base.html
│   ├── homepage.html
│   ├── login.html
│   ├── register.html
│   ├── trip.html
│   ├── expense.html
│   ├── todo.html
│   ├── map.html
│   └── about.html
└── static/
    └── (optional for CSS/images)
