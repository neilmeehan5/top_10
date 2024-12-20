from models import db, Category, TopList, ListItem
from app import app

with app.app_context():
    # Create all tables
    db.create_all()
    
    # Only add initial data if the database is empty
    if not Category.query.first():
        # Create categories
        sports = Category(name='Sports')
        universities = Category(name='Universities')
        entertainment = Category(name='Entertainment')
        
        db.session.add_all([sports, universities, entertainment])
        
        # Add some example lists
        nba_list = TopList(
            title='Best NBA Players',
            category=sports
        )
        db.session.add(nba_list)
        
        # Add some items
        players = [
            ListItem(rank=1, name='Michael Jordan', description='GOAT', top_list=nba_list),
            ListItem(rank=2, name='LeBron James', description='King James', top_list=nba_list),
            # Add more players as needed
        ]
        db.session.add_all(players)
        
        db.session.commit()
        print("Database initialized with initial data!")
    else:
        print("Database already contains data!")