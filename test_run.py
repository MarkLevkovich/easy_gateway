from gateway.core import EasyGateway

if __name__ == "__main__":
    gateway = EasyGateway(config_path="config.yaml")
    print(f"Middleware count: {len(gateway.middlewares)}")
    gateway.run()
