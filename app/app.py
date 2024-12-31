from flask import Flask, render_template, request, redirect, url_for, Blueprint, flash
from .models import db, Category, TopList, ListItem
from sqlalchemy import func, distinct
from functools import wraps
from .config import ADMIN_PASSWORD

# Create a Blueprint for our routes
main = Blueprint('main', __name__)

# Admin authentication (simple version - you might want something more secure)
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin_password = request.args.get('admin')
        if admin_password != ADMIN_PASSWORD:
            return "Unauthorized", 401
        return f(*args, **kwargs)
    return decorated_function

@main.route('/')
def index():
    return render_template('index.html')

def get_existing_items(original_list):
    """Helper function to get all existing items for a category/subcategory"""
    # Get all lists in the same category and subcategory
    category_lists = TopList.query.filter_by(
        category_id=original_list.category_id,
        subcategory=original_list.subcategory
    ).all()
    
    list_ids = [list.id for list in category_lists]
    
    # Get ALL items that have ever been ranked in these lists
    all_existing_items = db.session.query(
        ListItem.name,
        func.sum(ListItem.total_points).label('total_points'),
        func.sum(ListItem.total_votes).label('appearance_count')
    ).filter(
        ListItem.list_id.in_(list_ids)
    ).group_by(
        ListItem.name
    ).order_by(
        func.sum(ListItem.total_points).desc()
    ).all()
    
    # Also include items that were previously ranked but might have fallen out of top 10
    historical_items = db.session.query(
        ListItem.name
    ).filter(
        ListItem.list_id.in_(list_ids)
    ).distinct().all()
    
    # Convert historical items to set for quick lookup
    historical_names = {item.name for item in historical_items}
    
    # Ensure all historical items are included in all_existing_items
    existing_names = {item.name for item in all_existing_items}
    missing_items = historical_names - existing_names
    
    # Add missing items with 0 points and 1 appearance
    for name in missing_items:
        all_existing_items.append(type('Item', (), {
            'name': name,
            'total_points': 0,
            'appearance_count': 1
        }))
    
    # Resort the combined list by points
    return sorted(
        all_existing_items,
        key=lambda x: (x.total_points, x.name),
        reverse=True
    )

@main.route('/create', methods=['GET', 'POST'])
def create_list():
    if request.method == 'POST':
        # Get all item names and check for duplicates
        item_names = [
            request.form[f'item_name_{i}'].strip()
            for i in range(1, 11)
            if request.form[f'item_name_{i}'].strip()
        ]
        
        if len(item_names) != len(set(item_names)):
            flash('Error: Duplicate items are not allowed in rankings', 'error')
            return redirect(request.url)
            
        is_new_version = request.form.get('is_new_version') == 'true'
        
        if is_new_version:
            with db.session.no_autoflush:
                original_list_id = request.form['original_list_id']
                original_list = TopList.query.get(original_list_id)
                
                # Increment contribution count
                original_list.contribution_count += 1
                
                # Update points for each item in the list
                existing_items = {item.name: item for item in original_list.items}
                
                # Create or update items with their new points
                for i in range(1, 11):
                    name = request.form[f'item_name_{i}'].strip()
                    if name:
                        points = (11 - i) ** 2
                        
                        if name in existing_items:
                            item = existing_items[name]
                            item.total_points += points
                            item.total_votes += 1
                        else:
                            item = ListItem(
                                name=name,
                                total_points=points,
                                total_votes=1,
                                list_id=original_list.id
                            )
                            db.session.add(item)
                
                db.session.commit()
                return redirect(url_for('main.view_list', list_id=original_list_id))
        else:
            # Creating entirely new list
            new_list = TopList(
                title=request.form['title'],
                category_id=request.form['category_id'],
                subcategory=request.form['subcategory'],
                contribution_count=1
            )
            db.session.add(new_list)
            db.session.flush()
            
            # Add initial items
            for i in range(1, 11):
                name = request.form[f'item_name_{i}']
                if name.strip():
                    item = ListItem(
                        name=name.strip(),
                        total_points=(11 - i) ** 2,
                        total_votes=1,
                        list_id=new_list.id
                    )
                    db.session.add(item)
            
            db.session.commit()
            return redirect(url_for('main.view_list', list_id=new_list.id))
    
    # GET request - show the form
    categories = Category.query.all()
    
    # If this is a new version, get all existing items
    is_new_version = request.args.get('original_list_id') is not None
    original_list = None
    all_existing_items = []
    
    if is_new_version:
        original_list_id = request.args.get('original_list_id')
        original_list = TopList.query.get(original_list_id)
        
        # Get all lists in the same category and subcategory
        category_lists = TopList.query.filter_by(
            category_id=original_list.category_id,
            subcategory=original_list.subcategory
        ).all()
        
        list_ids = [list.id for list in category_lists]
        
        # Get ALL items that have ever been ranked in these lists
        all_existing_items = db.session.query(
            ListItem.name,
            func.sum(ListItem.total_points).label('total_points'),
            func.sum(ListItem.total_votes).label('appearance_count')
        ).filter(
            ListItem.list_id.in_(list_ids)
        ).group_by(
            ListItem.name
        ).order_by(
            func.sum(ListItem.total_points).desc()
        ).all()
        
        # Also include items that were previously ranked but might have fallen out of top 10
        historical_items = db.session.query(
            ListItem.name
        ).filter(
            ListItem.list_id.in_(list_ids)
        ).distinct().all()
        
        # Convert historical items to set for quick lookup
        historical_names = {item.name for item in historical_items}
        
        # Ensure all historical items are included in all_existing_items
        existing_names = {item.name for item in all_existing_items}
        missing_items = historical_names - existing_names
        
        # Add missing items with 0 points and 1 vote
        for name in missing_items:
            all_existing_items.append(type('Item', (), {
                'name': name,
                'total_points': 0,
                'appearance_count': 1
            }))
        
        # Resort the combined list by points
        all_existing_items = sorted(
            all_existing_items,
            key=lambda x: (x.total_points, x.name),
            reverse=True
        )
    
    return render_template('create_list.html', 
                         categories=categories,
                         is_new_version=is_new_version,
                         original_list=original_list,
                         all_existing_items=all_existing_items)


@main.route('/list/<int:list_id>')
def view_list(list_id):
    top_list = TopList.query.get_or_404(list_id)
    
    # Get all items for this list, sorted by total points
    items = ListItem.query.filter_by(list_id=list_id)\
        .order_by(ListItem.total_points.desc())\
        .limit(10)\
        .all()
    
    # Create ranked items list with proper ranking
    ranked_items = []
    for rank, item in enumerate(items, 1):
        ranked_items.append({
            'rank': rank,
            'name': item.name,
            'total_points': item.total_points,
            'total_votes': item.total_votes,
            'average_points': round(item.total_points / item.total_votes, 2) if item.total_votes > 0 else 0
        })
    
    return render_template('view_list.html', 
                         list=top_list, 
                         items=ranked_items)

@main.route('/list/<int:original_list_id>/create_version')
def create_version(original_list_id):
    original_list = TopList.query.get_or_404(original_list_id)
    original_items = ListItem.query.filter_by(list_id=original_list_id).order_by(ListItem.rank).all()
    
    # Get all items ever ranked in lists with the same title
    all_existing_items = db.session.query(
        ListItem.name,
        func.sum(ListItem.total_points).label('total_points'),
        func.count(ListItem.id).label('appearance_count')
    ).join(TopList).filter(
        TopList.title == original_list.title,
        TopList.category_id == original_list.category_id,
        TopList.subcategory == original_list.subcategory
    ).group_by(
        ListItem.name
    ).order_by(
        func.sum(ListItem.total_points).desc()
    ).all()
    
    return render_template('create_list.html',
                         categories=Category.query.all(),
                         is_new_version=True,
                         original_list=original_list,
                         original_items=original_items,
                         all_existing_items=all_existing_items)

@main.route('/category/<category_name>')
@main.route('/category/<category_name>/<subcategory>')
def category_view(category_name, subcategory=None):
    # Get the category
    category = Category.query.filter_by(name=category_name).first_or_404()
    
    # Get lists for this category
    query = TopList.query.filter_by(category_id=category.id)
    
    # If subcategory is specified, filter by it
    if subcategory:
        query = query.filter_by(subcategory=subcategory)
    
    top_lists = query.all()
    
    # For each list, get its top 5 items
    category_lists = []
    for list_obj in top_lists:
        # Get top 5 items for this list, sorted by total points
        items = ListItem.query.filter_by(list_id=list_obj.id)\
            .order_by(ListItem.total_points.desc())\
            .limit(5)\
            .all()
        
        # Create ranked items list
        ranked_items = []
        for rank, item in enumerate(items, 1):
            ranked_items.append({
                'rank': rank,
                'name': item.name,
                'total_points': item.total_points,
                'total_votes': item.total_votes,
                'average_points': round(item.total_points / item.total_votes, 2) if item.total_votes > 0 else 0
            })
        
        category_lists.append({
            'list': list_obj,
            'rankings': ranked_items
        })
    
    return render_template('category.html', 
                         category_name=category_name,
                         subcategory=subcategory,
                         category_lists=category_lists)

@main.route('/admin/rankings')
@admin_required
def admin_rankings():
    lists = TopList.query.all()
    
    # Get contribution details for each list
    list_details = []
    for list_obj in lists:
        # Get item history for this list
        contributions = []
        for i in range(list_obj.contribution_count):
            # Calculate what the rankings were after this contribution
            items_at_point = ListItem.query.filter_by(list_id=list_obj.id).order_by(
                ListItem.rank
            ).all()
            
            contribution = {
                'number': i + 1,
                'items': [{'name': item.name, 'rank': item.rank} for item in items_at_point]
            }
            contributions.append(contribution)
        
        list_details.append({
            'list': list_obj,
            'contributions': contributions
        })
    
    return render_template('admin_rankings.html', list_details=list_details)

@main.route('/admin/delete_contribution/<int:list_id>/<int:contribution_number>', methods=['POST'])
@admin_required
def delete_contribution(list_id, contribution_number):
    top_list = TopList.query.get_or_404(list_id)
    
    if contribution_number >= top_list.contribution_count:
        return "Invalid contribution number", 400
    
    # Decrease contribution count
    top_list.contribution_count -= 1
    
    # Get all items for this list
    items = ListItem.query.filter_by(list_id=list_id).all()
    
    # For each item, reduce points based on rank
    for item in items:
        points_per_rank = (11 - item.rank) ** 2
        item.total_points -= points_per_rank
        item.total_votes -= 1
        
        # If item has no more votes, delete it
        if item.total_votes <= 0:
            db.session.delete(item)
    
    # Recalculate rankings for remaining items
    remaining_items = ListItem.query.filter_by(list_id=list_id).order_by(
        ListItem.total_points.desc()
    ).all()
    
    # Update ranks
    for new_rank, item in enumerate(remaining_items, 1):
        item.rank = new_rank
    
    db.session.commit()
    
    return redirect(url_for('main.admin_rankings'))

# Create the Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///top10.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db.init_app(app)

# Register the blueprint
app.register_blueprint(main)

if __name__ == '__main__':
    app.run(debug=True)