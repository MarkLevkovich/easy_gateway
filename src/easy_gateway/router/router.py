class Router:
    def __init__(self) -> None:
        self.exact_routes = {}
        self.prefix_routes = {}

    def add_route(self, path: str, target: str):
        if path.endswith("/*"):
            prefix = path[:-2]

            self.prefix_routes[prefix] = (target.rstrip("/"), "prefix")
        else:
            if target.endswith("/"):
                full_url = target + path.lstrip("/")
            else:
                full_url = target.rstrip("/") + "/" + path.lstrip("/")
                
            self.exact_routes[path] = (full_url, "exact")

    def find_target(self, request_path):
        if request_path in self.exact_routes:
            target, route_type = self.exact_routes[request_path]
            return target, "", route_type

        longest_prefix = ""
        target = None
        route_type = "prefix"

        for prefix, (prefix_target, _) in self.prefix_routes.items():
            if request_path.startswith(prefix):
                if len(prefix) > len(longest_prefix):
                    longest_prefix = prefix
                    target = prefix_target
        if target:
            remaining = request_path[len(longest_prefix) :]
            return target, remaining, route_type

        return None, "", None
