import jmespath
import jmespath.exceptions


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
        try:
            self.exp = jmespath.compile(query)
        except jmespath.exceptions.JMESPathError:
            self.exp = None
