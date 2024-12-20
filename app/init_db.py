from app import app
from models import db, Category, TopList, ListItem

def init_db():
    with app.app_context():
        # Create all tables
        db.create_all()

        # Add categories if they don't exist
        if not Category.query.first():
            categories = [
                Category(name='Sports'),
                Category(name='Universities'),
                Category(name='Entertainment')
            ]
            db.session.add_all(categories)
            db.session.commit()
            print("Categories added successfully!")


if __name__ == '__main__':
    init_db()