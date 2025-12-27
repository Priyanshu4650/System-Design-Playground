import uuid

def generate_unique_id() -> str:
    try:
        return str(uuid.uuid4())
    except Exception as e:
        raise RuntimeError(f"Error generating unique ID: {str(e)}")