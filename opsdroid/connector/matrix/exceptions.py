class MatrixException(Exception):
    """Wrap a matrix-nio Error in an Exception so it can raised."""

    def __init__(self, nio_error):
        self.nio_error = nio_error
