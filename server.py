import redis
from flask import Flask, Response

app = Flask(__name__)
r = redis.StrictRedis(host='localhost', port=6379, db=0)


@app.route("/rules")
def rules():
    resp = Response(r.get("rules"))
    resp.headers['Content-Type'] = 'application/json'
    return resp


app.run()
