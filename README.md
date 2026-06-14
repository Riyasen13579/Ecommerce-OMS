# BazaarCart — E-Commerce Order Management System

A full-stack e-commerce order management system built with Python Flask, MySQL, HTML, CSS, and JavaScript. It includes user authentication, a shopping cart, wishlist, admin dashboard with sales analytics, Cloudinary image uploads, and dark mode.

## Features

- User signup, login, and logout with hashed passwords
- Product catalog with search, category filter, and price sorting
- Shopping cart with quantity updates
- Wishlist (save products for later)
- Checkout flow that creates orders and updates stock
- Order history for customers and order management for admins
- Admin dashboard with revenue analytics (Chart.js), low-stock alerts, and recent orders
- Add, edit, and delete products with image upload via Cloudinary
- Dark mode toggle
- Auto-seeded demo data (25 products across 7 categories + admin account)

## Tech Stack

- **Backend** — Python, Flask, Flask-Login, Flask-Bcrypt
- **Database** — SQLAlchemy ORM (MySQL / PostgreSQL compatible)
- **Image hosting** — Cloudinary
- **Frontend** — HTML, CSS, JavaScript, Chart.js
- **Environment management** — python-dotenv

## Project Structure

```
Ecommerce-OMS/
├── app.py              # main Flask app and routes
├── models.py           # database models (User, Product, Cart, Order, etc.)
├── database.py         # database initialization
├── wsgi.py             # WSGI entry point for deployment
├── requirements.txt    # Python dependencies
├── static/             # CSS, JS, images
└── templates/          # HTML templates
```

## Getting Started

### Prerequisites

- Python 3.8 or above
- MySQL (or PostgreSQL) database
- A free Cloudinary account for image uploads (https://cloudinary.com)

### Installation

```bash
git clone https://github.com/Riyasen13579/Ecommerce-OMS.git
cd Ecommerce-OMS
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root with the following variables:

```
SECRET_KEY=your-secret-key
DATABASE_URL=mysql+pymysql://username:password@localhost/ecommerce_oms
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
```

### Run locally

```bash
python app.py
```

The app will create all tables and seed demo data (products + admin account) automatically on first run.

**Default admin login:**
```
Email: admin@bazaarcart.com
Password: Admin@1234
```

Visit http://localhost:5000 in your browser.

## Key Routes

| Route | Description |
|---|---|
| `/` | Home page with featured products |
| `/products` | Browse all products (search, filter, sort) |
| `/signup`, `/login`, `/logout` | User authentication |
| `/cart` | View and manage shopping cart |
| `/wishlist` | View saved products |
| `/checkout` | Place an order |
| `/orders` | View order history (admin sees all orders) |
| `/dashboard` | Admin dashboard with analytics |
| `/admin/products/add` | Add a new product (admin only) |

## Deployment

This project includes a `wsgi.py` entry point, making it ready to deploy on platforms like Render, Railway, or PythonAnywhere:

1. Push the repo to GitHub
2. Create a new Web Service and connect your repo
3. Set the build command to `pip install -r requirements.txt`
4. Set the start command to `gunicorn wsgi:app`
5. Add the environment variables listed above in your hosting platform's settings

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you'd like to change.

## License

MIT
