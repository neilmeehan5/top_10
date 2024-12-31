from . import db
from datetime import datetime
import pytz

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    lists = db.relationship('TopList', backref='category', lazy=True)

class TopList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    subcategory = db.Column(db.String(50))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.now(pytz.timezone('US/Eastern')))
    contribution_count = db.Column(db.Integer, default=1)  # Track number of contributions
    items = db.relationship('ListItem', backref='top_list', lazy=True)

class ListItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    total_points = db.Column(db.Integer, nullable=False)
    total_votes = db.Column(db.Integer, nullable=False)
    list_id = db.Column(db.Integer, db.ForeignKey('top_list.id'), nullable=False)