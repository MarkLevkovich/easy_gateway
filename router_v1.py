

class Router:
    def __init__(self) -> None:
        self.routes = {}
    
    def add_route(self, path: str, target: str):
        self.routes[path] = target
    
    def find_target(self, request_path):
        return self.routes.get(request_path)
        

if __name__ == "__main__":
    router = Router()
    router.add_route("/test", "http://localhost:8001")
    
    assert router.find_target("/test") == "http://localhost:8001"
    assert router.find_target("/unknown") is None
    
    print("✅ Все тесты прошли!")