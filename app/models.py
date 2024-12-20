from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz

db = SQLAlchemy()

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    lists = db.relationship('TopList', backref='category', lazy=True)

class TopList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    total_votes = db.Column(db.Integer, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.now(pytz.timezone('US/Eastern')))
    items = db.relationship('ListItem', backref='top_list', lazy=True)

class ListItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rank = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    total_points = db.Column(db.Integer, nullable=False)
    total_votes = db.Column(db.Integer, nullable=False)
    list_id = db.Column(db.Integer, db.ForeignKey('top_list.id'), nullable=False)