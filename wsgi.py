from app import app, db, seed_data

with app.app_context():
    db.create_all()
    try:
        seed_data()
    except Exception as e:
        print(f"Seed error: {e}")

if __name__ == "__main__":
    app.run()