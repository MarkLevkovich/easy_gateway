from router_v1 import Router


router = Router()


router.add_route("/headers", "https://httpbin.org")

target, remaining = router.find_target("/headers")

print("TARGET:", target)
print("REMAINING", remaining)