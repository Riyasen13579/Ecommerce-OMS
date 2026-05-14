from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from database import db
from models import User, Product, Cart, Order, OrderItem, Payment, Wishlist
from datetime import datetime
from dotenv import load_dotenv
import cloudinary, cloudinary.uploader
import json, os

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'bazaarcart-secret-2025')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL',
    'mysql+pymysql://root:riya2003@localhost/ecommerce_oms'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def cart_count():
    if current_user.is_authenticated and not current_user.is_admin:
        return Cart.query.filter_by(user_id=current_user.id).count()
    return 0

def get_wishlist_ids():
    if current_user.is_authenticated and not current_user.is_admin:
        return [w.product_id for w in Wishlist.query.filter_by(user_id=current_user.id).all()]
    return []

# ══ PUBLIC ROUTES ══════════════════════════════════════════════

@app.route('/')
def index():
    featured = Product.query.filter(Product.stock > 0).limit(12).all()
    return render_template('index.html', products=featured,
                           cart_count=cart_count(), wishlist_ids=get_wishlist_ids())

@app.route('/products')
def products():
    category = request.args.get('category', '')
    sort = request.args.get('sort', 'name')
    search = request.args.get('search', '')
    query = Product.query
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))
    if category:
        query = query.filter_by(category=category)
    if sort == 'price_asc':
        query = query.order_by(Product.price.asc())
    elif sort == 'price_desc':
        query = query.order_by(Product.price.desc())
    else:
        query = query.order_by(Product.name.asc())
    all_products = query.all()
    return render_template('products.html', products=all_products,
                           cart_count=cart_count(), wishlist_ids=get_wishlist_ids(),
                           selected_category=category, sort=sort, search=search)

# ══ AUTH ═══════════════════════════════════════════════════════

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password']
        confirm = request.form['confirm']
        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('signup'))
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('signup'))
        if User.query.filter_by(username=username).first():
            flash('Username taken.', 'danger')
            return redirect(url_for('signup'))
        hashed = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email, password=hashed)
        db.session.add(user)
        db.session.commit()
        flash('Account created! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html', cart_count=0)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form['email'].strip()
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash(f'Welcome back, {user.username}! 👋', 'success')
            return redirect(request.args.get('next') or url_for('index'))
        flash('Invalid email or password.', 'danger')
    return render_template('login.html', cart_count=0)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# ══ WISHLIST ════════════════════════════════════════════════════

@app.route('/wishlist')
@login_required
def wishlist():
    items = Wishlist.query.filter_by(user_id=current_user.id).all()
    return render_template('wishlist.html', items=items,
                           cart_count=cart_count(), wishlist_ids=get_wishlist_ids())

@app.route('/wishlist/toggle/<int:product_id>', methods=['POST'])
@login_required
def toggle_wishlist(product_id):
    existing = Wishlist.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
    else:
        db.session.add(Wishlist(user_id=current_user.id, product_id=product_id))
        db.session.commit()
    return redirect(request.referrer or url_for('products'))

# ══ CART ════════════════════════════════════════════════════════

@app.route('/cart')
@login_required
def cart():
    items = Cart.query.filter_by(user_id=current_user.id).all()
    total = sum(i.product.price * i.quantity for i in items)
    return render_template('cart.html', cart_items=items,
                           total=total, cart_count=len(items))

@app.route('/cart/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    if current_user.is_admin:
        flash('Admins cannot add to cart.', 'warning')
        return redirect(url_for('index'))
    product = Product.query.get_or_404(product_id)
    existing = Cart.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if existing:
        existing.quantity += 1
    else:
        db.session.add(Cart(user_id=current_user.id, product_id=product_id, quantity=1))
    db.session.commit()
    flash(f'{product.name} added to cart! 🛒', 'success')
    return redirect(request.referrer or url_for('products'))

@app.route('/cart/remove/<int:item_id>')
@login_required
def remove_from_cart(item_id):
    item = Cart.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash('Unauthorised.', 'danger')
        return redirect(url_for('cart'))
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('cart'))

@app.route('/cart/update/<int:item_id>', methods=['POST'])
@login_required
def update_cart(item_id):
    item = Cart.query.get_or_404(item_id)
    qty = int(request.form.get('quantity', 1))
    if qty < 1:
        db.session.delete(item)
    else:
        item.quantity = qty
    db.session.commit()
    return redirect(url_for('cart'))

# ══ ORDERS ══════════════════════════════════════════════════════

@app.route('/checkout', methods=['POST'])
@login_required
def checkout():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('cart'))
    total = sum(i.product.price * i.quantity for i in cart_items)
    order = Order(user_id=current_user.id, total_amount=total, status='processing')
    db.session.add(order)
    db.session.flush()
    for item in cart_items:
        db.session.add(OrderItem(order_id=order.id, product_id=item.product_id,
                                 quantity=item.quantity, price=item.product.price))
        item.product.stock = max(0, item.product.stock - item.quantity)
    Cart.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    flash(f'Order #{order.id} placed successfully! 🎉', 'success')
    return redirect(url_for('orders'))

@app.route('/orders')
@login_required
def orders():
    if current_user.is_admin:
        all_orders = Order.query.order_by(Order.created_at.desc()).all()
    else:
        all_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('orders.html', orders=all_orders, cart_count=cart_count())

@app.route('/orders/update/<int:order_id>', methods=['POST'])
@login_required
def update_order_status(order_id):
    if not current_user.is_admin:
        return redirect(url_for('orders'))
    order = Order.query.get_or_404(order_id)
    order.status = request.form.get('status', order.status)
    db.session.commit()
    flash(f'Order #{order.id} updated.', 'success')
    return redirect(url_for('orders'))

# ══ ADMIN ════════════════════════════════════════════════════════

@app.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_admin:
        flash('Admin access required.', 'danger')
        return redirect(url_for('index'))
    total_orders = Order.query.count()
    total_revenue = db.session.query(db.func.sum(Order.total_amount)).scalar() or 0
    total_products = Product.query.count()
    low_stock = Product.query.filter(Product.stock < 5).all()
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    monthly = []
    for m in range(1, 13):
        rev = db.session.query(db.func.sum(Order.total_amount))\
            .filter(db.extract('month', Order.created_at) == m,
                    db.extract('year', Order.created_at) == datetime.utcnow().year)\
            .scalar() or 0
        monthly.append(round(rev, 2))
    all_products = Product.query.order_by(Product.created_at.desc()).all()
    return render_template('dashboard.html',
                           total_orders=total_orders,
                           total_revenue=round(total_revenue, 2),
                           total_products=total_products,
                           low_stock=low_stock,
                           recent_orders=recent_orders,
                           monthly_revenue=json.dumps(monthly),
                           all_products=all_products,
                           cart_count=0)

def upload_image_to_cloudinary(file):
    try:
        result = cloudinary.uploader.upload(file, folder='bazaarcart',
                    transformation=[{'width': 600, 'height': 600, 'crop': 'fill'}])
        return result.get('secure_url')
    except Exception as e:
        print(f'Cloudinary error: {e}')
        return None

@app.route('/admin/products/add', methods=['GET', 'POST'])
@login_required
def add_product():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    if request.method == 'POST':
        image_url = '/static/images/placeholder.png'
        uploaded_file = request.files.get('image_file')
        if uploaded_file and uploaded_file.filename:
            url = upload_image_to_cloudinary(uploaded_file)
            if url:
                image_url = url
        elif request.form.get('image_url'):
            image_url = request.form.get('image_url')
        product = Product(
            name=request.form['name'],
            description=request.form['description'],
            price=float(request.form['price']),
            stock=int(request.form['stock']),
            category=request.form['category'],
            image_url=image_url
        )
        db.session.add(product)
        db.session.commit()
        flash('Product added!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_product.html', cart_count=0)

@app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    if not current_user.is_admin:
        return redirect(url_for('index'))
    product = Product.query.get_or_404(product_id)
    if request.method == 'POST':
        product.name = request.form['name']
        product.description = request.form['description']
        product.price = float(request.form['price'])
        product.stock = int(request.form['stock'])
        product.category = request.form['category']
        uploaded_file = request.files.get('image_file')
        if uploaded_file and uploaded_file.filename:
            url = upload_image_to_cloudinary(uploaded_file)
            if url:
                product.image_url = url
        elif request.form.get('image_url'):
            product.image_url = request.form.get('image_url')
        db.session.commit()
        flash('Product updated!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_product.html', product=product, cart_count=0)

@app.route('/admin/products/delete/<int:product_id>')
@login_required
def delete_product(product_id):
    if not current_user.is_admin:
        return redirect(url_for('index'))
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted.', 'info')
    return redirect(url_for('dashboard'))

@app.route('/blog')
def blog():
    return render_template('blog.html', cart_count=cart_count())


@app.route('/api/revenue')
@login_required
def api_revenue():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorised'}), 403
    months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    values = []
    for m in range(1, 13):
        rev = db.session.query(db.func.sum(Order.total_amount))\
            .filter(db.extract('month', Order.created_at) == m,
                    db.extract('year', Order.created_at) == datetime.utcnow().year)\
            .scalar() or 0
        values.append(round(rev, 2))
    return jsonify({'months': months, 'values': values})

# ══ SEED DATA ════════════════════════════════════════════════════

def seed_data():
    if not User.query.filter_by(email='admin@bazaarcart.com').first():
        hashed = bcrypt.generate_password_hash('Admin@1234').decode('utf-8')
        db.session.add(User(username='admin', email='admin@bazaarcart.com', password=hashed, is_admin=True))
        db.session.commit()
        print('Admin: admin@bazaarcart.com / Admin@1234')

    if Product.query.count() == 0:
        products = [
            ('iPhone 15 Pro', 'Latest Apple iPhone with A17 Pro chip', 134900, 20, 'Electronics', 'https://images.unsplash.com/photo-1697565583748-ffd0e046ed0a?w=400'),
            ('Samsung Galaxy S24', 'Android flagship with 200MP camera', 79999, 15, 'Electronics', 'https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?w=400'),
            ('Sony WH-1000XM5', 'Industry leading noise cancellation headphones', 24990, 30, 'Electronics', 'https://images.unsplash.com/photo-1618366712010-f4ae9c647dcb?w=400'),
            ('MacBook Air M2', 'Supercharged by M2 chip, all day battery', 114900, 10, 'Electronics', 'https://images.unsplash.com/photo-1611186871348-b1ce696e52c9?w=400'),
            ('boAt Airdopes 141', 'True wireless earbuds with 42hr battery', 1299, 100, 'Electronics', 'https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=400'),
            ('Nike Running Shoes', 'Lightweight mesh shoes for daily runs', 4999, 50, 'Sports', 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400'),
            ('Yoga Mat', 'Non-slip 6mm thick exercise mat', 799, 80, 'Sports', 'https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=400'),
            ('Cricket Bat', 'Kashmir willow bat for leather ball', 1499, 25, 'Sports', 'https://images.unsplash.com/photo-1531415074968-036ba1b575da?w=400'),
            ('Men Casual T-Shirt', '100% cotton round-neck regular fit', 499, 200, 'Clothing', 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400'),
            ('Women Kurta Set', 'Ethnic embroidered kurta with palazzo', 1299, 60, 'Clothing', 'https://images.unsplash.com/photo-1583391733956-6c78276477e2?w=400'),
            ('Denim Jeans', 'Slim fit stretch denim dark blue', 1799, 45, 'Clothing', 'https://images.unsplash.com/photo-1542272604-787c3835535d?w=400'),
            ('Woolen Sweater', 'Warm knitted sweater for winters', 899, 35, 'Clothing', 'https://images.unsplash.com/photo-1556821840-3a63f15732ce?w=400'),
            ('Atomic Habits', 'James Clear — build good habits', 399, 150, 'Books', 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=400'),
            ('Rich Dad Poor Dad', 'Robert Kiyosaki — financial literacy', 299, 120, 'Books', 'https://images.unsplash.com/photo-1553729459-efe14ef6055d?w=400'),
            ('The Alchemist', 'Paulo Coelho — magical bestseller', 249, 90, 'Books', 'https://images.unsplash.com/photo-1512820790803-83ca734da794?w=400'),
            ('Instant Pot Duo', '7-in-1 electric pressure cooker 6qt', 7499, 20, 'Kitchen', 'https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=400'),
            ('Non-stick Cookware Set', '5-piece granite coated pots and pans', 2499, 18, 'Kitchen', 'https://images.unsplash.com/photo-1585771724684-38269d6639fd?w=400'),
            ('Air Fryer', '5L digital air fryer with 8 presets', 3499, 22, 'Kitchen', 'https://images.unsplash.com/photo-1648358622945-f78c3fca2a05?w=400'),
            ('LED Desk Lamp', 'Touch control 3 brightness USB lamp', 599, 70, 'Home', 'https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=400'),
            ('Bed Sheet Set', 'King size 300TC cotton bedsheet', 1299, 40, 'Home', 'https://images.unsplash.com/photo-1631049307264-da0ec9d70304?w=400'),
            ('Scented Candle Set', 'Luxury soy wax candles lavender set of 3', 699, 55, 'Home', 'https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=400'),
            ('Maybelline Foundation', 'Fit Me matte + poreless foundation', 499, 80, 'Beauty', 'https://images.unsplash.com/photo-1512496015851-a90fb38ba796?w=400'),
            ('Hair Dryer', 'Professional 2000W ionic hair dryer', 1799, 30, 'Beauty', 'https://images.unsplash.com/photo-1522338242992-e1a54906a8da?w=400'),
            ('LEGO Classic Set', '1500 piece classic brick set', 3499, 25, 'Toys', 'https://images.unsplash.com/photo-1587654780291-39c9404d746b?w=400'),
            ('Remote Control Car', 'High speed 1:18 RC off-road car', 1299, 40, 'Toys', 'https://images.unsplash.com/photo-1594736797933-d0501ba2fe65?w=400'),
        ]
        for name, desc, price, stock, cat, img in products:
            db.session.add(Product(name=name, description=desc, price=price,
                                   stock=stock, category=cat, image_url=img))
        db.session.commit()
        print(f'Seeded {len(products)} products.')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_data()
    app.run(debug=True)
