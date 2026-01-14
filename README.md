1. import cors_middleware:

in server.py import cors and link with app

```py
from cors_middleware import cors_middleware
# ....
# rest of the code
# ....

# replace this line
# app = web.Application()

# with below line
app = web.Application(middlewares=[cors_middleware])
# .... rest code.....
```
