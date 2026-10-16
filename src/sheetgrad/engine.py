import math
class Value:
    def __init__(self, data, children=(), op=""):
        self.data = data
        self.grad = 0.0
        self._children = children
        self._op = op
        self._backward = lambda: None

    def __repr__(self):
        return f"Value(data={self.data}, grad={self.grad})"

    def __add__(self, other):
        other = other if isinstance(other, Value) else Value(other)
        out = Value(self.data + other.data, (self, other), "+")

        def _backward():
            self.grad += 1 * out.grad
            other.grad += 1 * out.grad

        out._backward = _backward
        return out

    def __mul__(self, other):
        other = other if isinstance(other, Value) else Value(other)
        out = Value(self.data * other.data, (self, other), "*")

        def _backward():
            self.grad += other.data * out.grad
            other.grad += self.data * out.grad

        out._backward = _backward
        return out

    def __pow__(self, other):
        if isinstance(other, Value):
            out = Value(self.data ** other.data, (self, other), "**")

            def _backward():
                self.grad += other.data * self.data ** (other.data - 1) * out.grad
                if self.data > 0:
                    other.grad += out.data * math.log(self.data) * out.grad
                else:
                    other.grad = math.nan

            out._backward = _backward
            return out

        out = Value(self.data ** other, (self,), f"**{other}")

        def _backward():
            self.grad += other * self.data ** (other - 1) * out.grad

        out._backward = _backward
        return out

    def exp(self):
        out = Value(math.exp(self.data), (self,), "exp")

        def _backward():
            self.grad += out.data * out.grad

        out._backward = _backward
        return out

    def log(self):
        out = Value(math.log(self.data), (self,), "log")

        def _backward():
            self.grad += (1 / self.data) * out.grad

        out._backward = _backward
        return out

    def backward(self):
        order = []
        visited = set()

        def build(node):
            if node not in visited:
                visited.add(node)
                for child in node._children:
                    build(child)
                order.append(node)

        build(self)

        self.grad = 1.0
        for node in reversed(order):
            node._backward()

    def __neg__(self):
        return self * -1

    def __sub__(self, other):
        return self + (-other)

    def __truediv__(self, other):
        return self * other ** -1

    def __radd__(self, other):
        return self + other

    def __rmul__(self, other):
        return self * other

    def __rsub__(self, other):
        return other + (-self)

    def __rtruediv__(self, other):
        return other * self ** -1

    def __rpow__(self, other):
        return Value(other) ** self