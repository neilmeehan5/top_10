from app import create_app, db
from app.models import Category

def init_db():
    app = create_app()
    
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Add categories if they don't exist
        categories = [
            'Sports',
            'Universities',
            'Entertainment',
            'Movies',
            'TV Shows',
            'Books',
            'Music',
            'Video Games',
            'Food',
            'Travel',
            'Technology',
            'Other'
        ]
        
        for cat_name in categories:
            if not Category.query.filter_by(name=cat_name).first():
                category = Category(name=cat_name)
                db.session.add(category)
                print(f"Added category: {cat_name}")
        
        db.session.commit()
        print("Database initialization complete!")

if __name__ == '__main__':
    init_db() 