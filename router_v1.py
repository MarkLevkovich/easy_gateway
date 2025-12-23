


class Router:
    def __init__(self) -> None:
        self.exact_routes = {}
        self.prefix_routes = {}

    
    def add_route(self, path: str, target: str):
        if path.endswith("/*"):
            prefix = path[:-2]
            self.prefix_routes[prefix] = target
        else:
            self.exact_routes[path] = target
    
    def find_target(self, request_path):
        if request_path in self.exact_routes:
            return self.exact_routes.get(request_path), ""
        
        longest_prefix = ""
        target = None
        
        for prefix, prefix_target in self.prefix_routes.items():
            if request_path.startswith(prefix):
                if len(prefix) > len(longest_prefix):
                    longest_prefix = prefix
                    target = prefix_target
        if target:
            remaining = request_path[len(longest_prefix):]
            return target, remaining
        
        return None, ""
        

if __name__ == "__main__":
    router = Router()
    router.add_route("/api/*", "http://localhost:8000")
    router.add_route("/api/users", "http://localhost:8001")
    
    # Точное совпадение
    target, remaining = router.find_target("/api/users")
    assert target == "http://localhost:8001"
    assert remaining == ""
    
    # Префиксный маршрут
    target, remaining = router.find_target("/api/products/123")
    assert target == "http://localhost:8000"
    assert remaining == "/products/123"
    
    # Не найден
    target, remaining = router.find_target("/unknown")
    assert target is None
    
    print("✅ Все тесты прошли!")