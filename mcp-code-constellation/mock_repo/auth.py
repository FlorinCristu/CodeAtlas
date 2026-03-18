
def hash_password(pw):
    return pw + "hash"
    
def query_db(user):
    return user
    
def login(user, pw):
    print("starting login")
    u = query_db(user)
    h = hash_password(pw)
    return True
