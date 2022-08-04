import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

# ATTENTION!!! -> uncomment following line to generate database...
#db_drop_and_create_all()

# ROUTES
@app.route('/drinks')
def get_drinks():
    # public piece of code that just retrieves basic info
    results = Drink.query.all()
    aggregated_results = [data.short() for data in results]
    return jsonify({
        'status_code': 200,
        'success': True,
        'drinks': aggregated_results
    })

@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def get_drinks_detailed():
    # private piece of code that retrieves all drink information that should only be executed by baristas and possibly managers
    results = Drink.query.all()
    aggregated_results = [data.long() for data in results]
    return jsonify({
        'success': True,
        'drinks': aggregated_results
    })

@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drinks():
    # private piece of code that allows the creation of drinks.  It can only be accessed by managers
    request_body = request.get_json()
    new_drink = Drink(title=request_body['title'], recipe=json.dumps(request_body['recipe']))
    new_drink.insert()
    return jsonify({
        'success': True,
        'drinks': new_drink.long()
    })

@app.route('/drinks/<int:drink_id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def edit_drinks(drink_id):
    # private piece of code that allows the modification of drinks.  It can only be accessed by managers
    drink_for_edit = Drink.query.filter_by(id=drink_id).first()
    request_body = request.get_json()

    if drink_for_edit is None:
        abort(404)

    if request_body['title']:
        drink_for_edit.title = request_body['title']
    elif request_body['recipe']:
        drink_for_edit.recipe = request_body['recipe']

    drink_for_edit.update()
    
    return jsonify({
        'success': True,
        'drinks': [drink_for_edit.long()]
    })

@app.route('/drinks/<int:drink_id>', methods=["DELETE"])
@requires_auth('delete:drinks')
def delete_drinks(drink_id):
    # private piece of code that allows the removal of drinks from the menu.  It can only be accessed by managers
    drink_for_deletion = Drink.query.filter_by(id=drink_id).first()

    if drink_for_deletion is None:
        abort(404)

    drink_for_deletion.delete()
    
    return jsonify({
        'success': True,
        'drinks': drink_id
    })


# Error Handling

@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": "bad request"
    }), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "not found"
    }), 404

@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422

@app.errorhandler(AuthError)
def handle_custom_auth_error(error):
    response = jsonify({
        "error": error.status_code,
        "message": error.error
    })
    return response, error.status_code


