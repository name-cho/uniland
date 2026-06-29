class UniLandError(Exception):
    def __init__(self, message, line=None, column=None):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(self.__str__())

    def __str__(self):
        if self.line is not None:
            return f"Error at line {self.line}: {self.message}"
        return self.message