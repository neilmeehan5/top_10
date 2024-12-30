from flask import Flask, render_template, request, redirect, url_for
from models import db, Category, TopList, ListItem
from sqlalchemy import func

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///top10.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create', methods=['GET', 'POST'])
def create_list():
    if request.method == 'POST':
        is_new_version = request.form.get('is_new_version') == 'true'
        
        if is_new_version:
            # Get the original list to maintain consistency
            original_list_id = request.form['original_list_id']
            original_list = TopList.query.get(original_list_id)
            
            # Use the original list's metadata
            new_list = TopList(
                title=original_list.title,
                category_id=original_list.category_id,
                subcategory=original_list.subcategory,
                total_votes=1
            )
        else:
            # Creating entirely new list
            new_list = TopList(
                title=request.form['title'],
                category_id=request.form['category_id'],
                subcategory=request.form['subcategory'],
                total_votes=1
            )
        
        db.session.add(new_list)
        db.session.flush()  # This gets us the new_list.id
        
        # Add items
        for i in range(1, 11):
            name = request.form[f'item_name_{i}']
            if name.strip():  # Only add non-empty items
                item = ListItem(
                    rank=i,
                    name=name.strip(),
                    total_points=(11 - i) ** 2,
                    total_votes=1,
                    top_list=new_list
                )
                db.session.add(item)
        
        db.session.commit()
        
        if is_new_version:
            # Redirect to the aggregated view of all versions
            return redirect(url_for('view_list', list_id=original_list_id, show_aggregate=1))
        else:
            return redirect(url_for('view_list', list_id=new_list.id))
    
    # GET request - show the form
    categories = Category.query.all()
    
    # Get category and subcategory from URL parameters
    category_name = request.args.get('category')
    subcategory = request.args.get('subcategory')
    
    # Find the category ID if category_name is provided
    pre_selected_category = None
    if category_name:
        pre_selected_category = Category.query.filter_by(name=category_name).first()
    
    return render_template('create_list.html',
                         categories=categories,
                         pre_selected_category=pre_selected_category,
                         pre_selected_subcategory=subcategory)


@app.route('/list/<int:list_id>')
def view_list(list_id):
    show_aggregate = request.args.get('show_aggregate', type=int)
    top_list = TopList.query.get_or_404(list_id)
    
    if show_aggregate:
        # Get all versions of this list (matching title and category)
        related_lists = TopList.query.filter_by(
            title=top_list.title,
            category_id=top_list.category_id,
            subcategory=top_list.subcategory
        ).all()
        list_ids = [l.id for l in related_lists]
        
        # Aggregate items across all versions
        items = db.session.query(
            ListItem.name,
            func.sum(ListItem.total_points).label('total_points'),
            func.sum(ListItem.total_votes).label('total_votes')
        ).filter(
            ListItem.list_id.in_(list_ids)
        ).group_by(
            ListItem.name
        ).order_by(
            func.sum(ListItem.total_points).desc()
        ).limit(10).all()
        
        # Calculate ranks for aggregated items
        ranked_items = []
        for rank, item in enumerate(items, 1):
            ranked_items.append({
                'rank': rank,
                'name': item.name,
                'total_points': item.total_points,
                'total_votes': item.total_votes,
                'average_points': item.total_points / item.total_votes
            })
        
        return render_template('view_list.html', 
                             list=top_list, 
                             items=ranked_items, 
                             show_aggregate=True,
                             version_count=len(related_lists))
    else:
        items = ListItem.query.filter_by(list_id=list_id).order_by(ListItem.rank).all()
        return render_template('view_list.html', 
                             list=top_list, 
                             items=items, 
                             show_aggregate=False)

@app.route('/list/<int:original_list_id>/create_version')
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

@app.route('/category/<category_name>')
@app.route('/category/<category_name>/<subcategory>')
def category_view(category_name, subcategory=None):
    # Get the category
    category = Category.query.filter_by(name=category_name).first_or_404()
    
    # Get lists for this category
    query = TopList.query.filter_by(category_id=category.id)
    
    # If subcategory is specified, filter by it
    if subcategory:
        query = query.filter_by(subcategory=subcategory)
    
    lists = query.all()
    
    return render_template('category.html', 
                         category_name=category_name,
                         subcategory=subcategory,
                         lists=lists)

@app.template_filter('slice')
def slice_filter(iterable, slc):
    return list(iterable)[:slc]

if __name__ == '__main__':
    app.run(debug=True)