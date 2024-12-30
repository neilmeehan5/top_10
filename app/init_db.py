from app import app
from models import db, Category, TopList, ListItem

def init_db():
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Only add initial data if the database is empty
        if not Category.query.first():
            # Create categories
            categories = [
                Category(name='Sports'),
                Category(name='Universities'),
                Category(name='Entertainment')
            ]
            
            db.session.add_all(categories)
            db.session.commit()
            print("Database initialized with categories!")
        else:
            print("Database already contains data!")

if __name__ == '__main__':
    init_db()