# Backend Badminton - Django REST API

Django REST Framework backend for Badminton event management system.

## Features

- User Registration Management
- Event Management (Upcoming and Completed Events)
- Event Results with Images
- Admin Authentication
- RESTful API endpoints

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run migrations:
```bash
python manage.py migrate
```

3. Create superuser:
```bash
python manage.py createsuperuser
```

4. Run development server:
```bash
python manage.py runserver
```

## API Endpoints

- `/api/registrations/` - Registration management
- `/api/events/` - Event management
- `/api/completed-events/` - Completed events
- `/api/event-results/` - Event results with images
- `/api/login/` - Admin login

## Models

- `Registration` - User registrations
- `Event` - Upcoming events
- `CompletedEvent` - Past events
- `EventResult` - Event results
- `EventResultImage` - Images for event results
- `AdminAccount` - Admin accounts

