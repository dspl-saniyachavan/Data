# Swagger Documentation Templates

Quick copy-paste templates for common API patterns.

## GET - List with Pagination

```python
@bp.route('', methods=['GET'])
@token_required
def get_items():
    """
    Get all items
    ---
    tags:
      - Items
    security:
      - Bearer: []
    parameters:
      - in: query
        name: search
        type: string
        description: Search term
      - in: query
        name: sort_by
        type: string
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
        description: List of items
        schema:
          type: object
          properties:
            items:
              type: array
            total:
              type: integer
            pages:
              type: integer
            current_page:
              type: integer
      401:
        description: Unauthorized
    """
    pass
```

## GET - Single Item by ID

```python
@bp.route('/<int:item_id>', methods=['GET'])
@token_required
def get_item(item_id):
    """
    Get item by ID
    ---
    tags:
      - Items
    security:
      - Bearer: []
    parameters:
      - in: path
        name: item_id
        type: integer
        required: true
        description: Item ID
    responses:
      200:
        description: Item details
        schema:
          type: object
          properties:
            id:
              type: integer
            name:
              type: string
            created_at:
              type: string
              format: date-time
      404:
        description: Item not found
      401:
        description: Unauthorized
    """
    pass
```

## POST - Create Item

```python
@bp.route('', methods=['POST'])
@token_required
def create_item():
    """
    Create new item
    ---
    tags:
      - Items
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
          properties:
            name:
              type: string
              example: Item Name
            description:
              type: string
              example: Item description
            value:
              type: number
              example: 42.5
    responses:
      201:
        description: Item created successfully
        schema:
          type: object
          properties:
            id:
              type: integer
            name:
              type: string
            message:
              type: string
      400:
        description: Invalid input
      401:
        description: Unauthorized
    """
    pass
```

## PUT - Update Item

```python
@bp.route('/<int:item_id>', methods=['PUT'])
@token_required
def update_item(item_id):
    """
    Update item
    ---
    tags:
      - Items
    security:
      - Bearer: []
    parameters:
      - in: path
        name: item_id
        type: integer
        required: true
        description: Item ID
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
            description:
              type: string
            value:
              type: number
    responses:
      200:
        description: Item updated successfully
      400:
        description: Invalid input
      404:
        description: Item not found
      401:
        description: Unauthorized
    """
    pass
```

## DELETE - Delete Item

```python
@bp.route('/<int:item_id>', methods=['DELETE'])
@token_required
def delete_item(item_id):
    """
    Delete item
    ---
    tags:
      - Items
    security:
      - Bearer: []
    parameters:
      - in: path
        name: item_id
        type: integer
        required: true
        description: Item ID
    responses:
      200:
        description: Item deleted successfully
        schema:
          type: object
          properties:
            message:
              type: string
      404:
        description: Item not found
      401:
        description: Unauthorized
    """
    pass
```

## POST - Login (No Auth Required)

```python
@bp.route('/login', methods=['POST'])
def login():
    """
    User login
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - email
            - password
          properties:
            email:
              type: string
              format: email
              example: user@example.com
            password:
              type: string
              format: password
              example: password123
    responses:
      200:
        description: Login successful
        schema:
          type: object
          properties:
            token:
              type: string
            user:
              type: object
              properties:
                id:
                  type: integer
                email:
                  type: string
                name:
                  type: string
                role:
                  type: string
      400:
        description: Invalid credentials
      401:
        description: Unauthorized
    """
    pass
```

## Common Data Types

### String
```yaml
type: string
example: "Sample text"
```

### Integer
```yaml
type: integer
example: 42
```

### Number (Float)
```yaml
type: number
example: 42.5
```

### Boolean
```yaml
type: boolean
example: true
```

### Date/Time
```yaml
type: string
format: date-time
example: "2024-01-15T10:30:00Z"
```

### Email
```yaml
type: string
format: email
example: user@example.com
```

### Array
```yaml
type: array
items:
  type: string
example: ["item1", "item2"]
```

### Object
```yaml
type: object
properties:
  field1:
    type: string
  field2:
    type: integer
```

## Common Tags

Use these tags to organize your API:

- `Authentication` - Login, register, logout
- `Users` - User management
- `Parameters` - Parameter CRUD
- `Telemetry` - Telemetry data
- `Configuration` - System configuration
- `Reports` - Report generation
- `MQTT` - MQTT operations
- `Sync` - Data synchronization

## Tips

1. **Always include tags** - Groups endpoints in Swagger UI
2. **Use security for protected routes** - Add `security: - Bearer: []`
3. **Provide examples** - Makes testing easier
4. **Document all responses** - Including error cases
5. **Keep descriptions clear** - Help other developers understand the API
