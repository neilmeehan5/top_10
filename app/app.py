from flask import Flask, render_template, request, redirect, url_for
from models import db, Category, TopList, ListItem

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
        # Get form data
        title = request.form['title']
        category_id = request.form['category_id']
        
        # Create new list
        new_list = TopList(
            title=title,
            category_id=category_id,
            total_votes=0
        )
        db.session.add(new_list)
        db.session.flush()  # This gets us the new_list.id
        
        # TODO: Update the below for items that already exist
        # Create list items
        for i in range(1, 11):
            name = request.form[f'item_name_{i}']
            
            item = ListItem(
                rank=i,
                name=name,
                total_points=(11 - i) ** 2,
                total_votes=1,
                top_list=new_list
            )
            db.session.add(item)
        
        db.session.commit()
        return redirect(url_for('view_list', list_id=new_list.id))
    
    # GET request - show the form
    categories = Category.query.all()
    return render_template('create_list.html', categories=categories)

@app.route('/list/<int:list_id>')
def view_list(list_id):
    top_list = TopList.query.get_or_404(list_id)
    items = ListItem.query.filter_by(list_id=list_id).order_by(ListItem.rank).all()
    return render_template('view_list.html', list=top_list, items=items)

if __name__ == '__main__':
    app.run(debug=True)