import uuid



class SageError(Exception):
    """Base class for all Sage exceptions.

    Attributes:
        status_code (int): HTTP status code associated with the error.
        default_detail (str): Default error message.
        default_code (str): Default error code.
        section_code (str): Section code for categorizing errors.
        detail (str): Specific error message.
        code (str): Specific error code.
        section_code (str): Section code for the specific error.
        error_id (str): Unique identifier for the error instance.

    Methods:
        __init__(detail=None, code=None, section_code=None): Initializes the error with specific details.
        __str__(): Returns a formatted string representation of the error.
    """

    status_code = 500
    default_detail = "A server error occurred."
    default_code = "E5000"
    section_code = "SAGE"

    def __init__(self, detail=None, code=None, section_code=None):
        if detail is None:
            detail = self.default_detail
        if code is None:
            code = self.default_code
        if section_code is None:
            section_code = self.section_code
        self.detail = detail
        self.code = code
        self.section_code = section_code
        self.error_id = str(uuid.uuid4())

    def __str__(self):
        return f"Error {self.section_code}{self.code} - {self.detail} (Error ID: {self.error_id})"
    