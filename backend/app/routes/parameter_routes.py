from flask import Blueprint, request, jsonify
from app.controllers.parameter_controller import ParameterController
from app.middleware.auth_middleware import token_required

parameter_bp = Blueprint('parameters', __name__, url_prefix='/api/parameters')

@parameter_bp.route('', methods=['GET'])
@token_required
def get_parameters():
    """
    Get all parameters
    ---
    tags:
      - Parameters
    security:
      - Bearer: []
    parameters:
      - in: query
        name: search
        type: string
        description: Search by parameter name
      - in: query
        name: sort_by
        type: string
        description: Sort by field (id, name, value)
        default: id
      - in: query
        name: order
        type: string
        enum: [asc, desc]
        default: asc
      - in: query
        name: page
        type: integer
        default: 1
      - in: query
        name: per_page
        type: integer
        default: 10
    responses:
      200:
        description: List of parameters
        schema:
          type: object
          properties:
            parameters:
              type: array
              items:
                type: object
            total:
              type: integer
            pages:
              type: integer
            current_page:
              type: integer
      401:
        description: Unauthorized
    """
    result, status = ParameterController.get_all_parameters()
    return jsonify(result), status

@parameter_bp.route('', methods=['POST'])
@token_required
def create_parameter():
    """
    Create a new parameter
    ---
    tags:
      - Parameters
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - name
            - value
          properties:
            name:
              type: string
              example: temperature
            value:
              type: string
              example: 25.5
            unit:
              type: string
              example: celsius
            description:
              type: string
              example: Room temperature sensor
    responses:
      201:
        description: Parameter created successfully
      400:
        description: Invalid input
      401:
        description: Unauthorized
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    result, status = ParameterController.create_parameter(data)
    return jsonify(result), status

@parameter_bp.route('/<int:param_id>', methods=['GET'])
@token_required
def get_parameter(param_id):
    """
    Get a specific parameter by ID
    ---
    tags:
      - Parameters
    security:
      - Bearer: []
    parameters:
      - in: path
        name: param_id
        type: integer
        required: true
        description: Parameter ID
    responses:
      200:
        description: Parameter details
        schema:
          type: object
          properties:
            id:
              type: integer
            name:
              type: string
            value:
              type: string
            unit:
              type: string
            description:
              type: string
      404:
        description: Parameter not found
      401:
        description: Unauthorized
    """
    result, status = ParameterController.get_parameter_by_id(param_id)
    return jsonify(result), status

@parameter_bp.route('/<int:param_id>', methods=['PUT'])
@token_required
def update_parameter(param_id):
    """
    Update a parameter
    ---
    tags:
      - Parameters
    security:
      - Bearer: []
    parameters:
      - in: path
        name: param_id
        type: integer
        required: true
        description: Parameter ID
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
            value:
              type: string
            unit:
              type: string
            description:
              type: string
    responses:
      200:
        description: Parameter updated successfully
      400:
        description: Invalid input
      404:
        description: Parameter not found
      401:
        description: Unauthorized
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    result, status = ParameterController.update_parameter(param_id, data)
    return jsonify(result), status

@parameter_bp.route('/<int:param_id>', methods=['DELETE'])
@token_required
def delete_parameter(param_id):
    """
    Delete a parameter
    ---
    tags:
      - Parameters
    security:
      - Bearer: []
    parameters:
      - in: path
        name: param_id
        type: integer
        required: true
        description: Parameter ID
    responses:
      200:
        description: Parameter deleted successfully
      404:
        description: Parameter not found
      401:
        description: Unauthorized
    """
    result, status = ParameterController.delete_parameter(param_id)
    return jsonify(result), status
