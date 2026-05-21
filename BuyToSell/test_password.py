from app.utils.security import hash_password
print("testpass length:", len("testpass"))
print("testpass bytes length:", len("testpass".encode("utf-8")))
try:
    hash_password("testpass")
    print("Success!")
except Exception as e:
    print("Error:", e)
