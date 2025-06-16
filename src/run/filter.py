import jmespath
import jmespath.exceptions


class FilterError(Exception):
    def __init__(self, *args, mes: str | None = None):
        super().__init__(*args)
        self.message = f"Invalid Filter: {mes}" if mes else "Invalid Filter"

    def __str__(self):
        return self.message


class Filter:
    def __init__(self, query: str):
        try:
            self.exp = jmespath.compile(query)
        except jmespath.exceptions.JMESPathError:
            self.exp = None
        return

    def matches(self, data: dict) -> bool:
        if self.exp is None:
            return True
        val = self.exp.search(data)
        return bool(val)

    def update_query(self, query: str):
        query = query.strip()
        if query == "":
            self.exp = None
            return
        try:
            self.exp = jmespath.compile(query)
        except jmespath.exceptions.JMESPathError as e:
            self.exp = None
            raise FilterError(e)
