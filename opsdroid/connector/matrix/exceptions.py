class MatrixException(Exception):
    """Wrap a matrix-nio Error in an Exception so it can raised."""

    def __init__(self, nio_error):
        self.nio_error = nio_error

    def __repr__(self):
        return super().__repr__ + "\n" + str(self.nio_error)

    def __str__(self):
        return super().__str__ + "\n" + str(self.nio_error)
