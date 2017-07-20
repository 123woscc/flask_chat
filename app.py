from flask import (Flask,render_template,url_for)
import flask
import datetime
import redis


app=Flask(__name__)

app.secret_key='hard_key'

#redis数据库
r=redis.StrictRedis(host='localhost',port=6379,db=1,decode_responses=True)


def event_stream():
    pubsub=r.pubsub()
    pubsub.subscribe('chat')
    for message in pubsub.listen():
        print(message)
        yield 'data:{}\n\n'.format(message['data'])


#首页
@app.route('/')
def index():
    if 'user' not in flask.session:
        return flask.redirect('/login')
    user=flask.session['user']
    return render_template('index.html',user=user)

#登录页面
@app.route('/login',methods=['GET','POST'])
def login():
    if 'user' in flask.session:
        return flask.redirect('/')
    if flask.request.method=='POST':
        flask.session['user']=flask.request.form['user']
        r.publish('chat', '用户{}加入了房间!'.format(flask.session['user']))
        return flask.redirect('/')
    return render_template('login.html')

#注销
@app.route('/logout')
def logout():
    user=flask.session.pop('user')
    print(user)
    r.publish('chat', '用户{}退出了房间'.format(user))
    return flask.redirect('/login')

#发送消息
@app.route('/send',methods=['POST'])
def post():
    message=flask.request.form['message']
    user=flask.session.get('user','anonymous')
    now=datetime.datetime.now().replace(microsecond=0).time()
    r.publish('chat','[{}] {} : {}'.format(now.isoformat(),user,message))


    return flask.Response(status=204)

#SSE事件流
@app.route('/stream')
def stream():
    return flask.Response(event_stream(),mimetype='text/event-stream')



if __name__ == '__main__':
    app.run(debug=True, threaded=True)