class FunctionException(Exception):
    """Raise when the function is executed unsuccessfully

Variables:

func_name: name of the failed function
err: the raised error"""

    def __init__(self, func_name, err):
        self.message = f'Function "{func_name}" failed: "{str(err)}"'
        super().__init__(self.message)
