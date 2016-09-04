#!/usr/bin/env python3

from models import User, Weibo

from response import session, error, template, redirect, response_with_header

from utils import log


def current_user(request):
    session_id = request.cookies.get('user', '')
    username = session.get(session_id, 'guest')
    return username


def route_weibo_index(request):
    headers = {
        'Content-Type': 'text/html',
    }
    header = response_with_header(headers)
    user_id = request.query.get('user_id', -1)
    user_id = int(user_id)
    user = User.find(user_id)
    if user is None:
        return error(request)
    # 找到 user 发布的所有 weibo
    weibos = Weibo.find_all(user_id=user.id)
    # 手动处理 weibos 这个 list
    # 把每个 weibo 以 <p> 的形式展现在页面
    def weibo_tag(weibo):
        return '<p>{} from {}@{} <a href="/weibo/delete?id={}">删除</a> <a href="/weibo/edit?id={}">修改</a></p>'.format(
            weibo.content,
            user.username,
            weibo.created_time,
            weibo.id,
            weibo.id,
        )
    # 用 join() 返回 str
    weibos = ''.join([weibo_tag(w) for w in weibos])
    body = template('weibo_index.html', weibos=weibos)
    r = header + '\r\n' + body
    return r.encode(encoding='utf-8')


def route_weibo_new(request):
    """
    发表新微博的页面
    在 form 里面写上微博内容
    post 的 action 则是 /weibo/add 这个路由
    """
    headers = {
        'Content-Type': 'text/html',
    }
    username = current_user(request)
    header = response_with_header(headers)
    user = User.find_by(username=username)
    body = template('weibo_new.html')
    r = header + '\r\n' + body
    return r.encode(encoding='utf-8')


def route_weibo_add(request):
    """
    这个函数相当于一个裸的 API
    它提取某个 HTML页面 的数据
    处理过后 redirect 到一个页面
    """
    headers = {
        'Content-Type': 'text/html',
    }
    username = current_user(request)
    log('发微博的用户: ', username)
    header = response_with_header(headers)
    user = User.find_by(username=username)
    # 创建一个新微博实例
    # 就是把 weibo_new.html 的数据处理
    form = request.form()
    w = Weibo(form)
    w.user_id = user.id
    w.save()
    return redirect('/weibo?user_id={}'.format(user.id))


def route_weibo_delete(request):
    headers = {
        'Content-Type': 'text/html',
    }
    username = current_user(request)
    header = response_with_header(headers)
    user = User.find_by(username=username)
    # 删除微博
    weibo_id = request.query.get('id', None)
    weibo_id = int(weibo_id)
    w = Weibo.find(weibo_id)
    w.delete()
    return redirect('/weibo?user_id={}'.format(user.id))


def route_weibo_edit(request):
    headers = {
        'Content-Type': 'text/html',
    }
    header = response_with_header(headers)
    # 这个 query.get 是在 weibo_index路由 里面放上去的
    # 用来指定要修改那一条微博
    weibo_id = request.query.get('id', -1)
    weibo_id = int(weibo_id)
    w = Weibo.find(weibo_id)
    if w is None:
        return error(request)
    # 生成一个 edit 页面
    body = template('weibo_edit.html',
                    weibo_id=w.id,
                    weibo_content=w.content)
    r = header + '\r\n' + body
    return r.encode(encoding='utf-8')


def route_weibo_update(request):
    username = current_user(request)
    user = User.find_by(username=username)
    form = request.form()
    content = form.get('content', '')
    weibo_id = int(form.get('id', -1))
    w = Weibo.find(weibo_id)
    if user.id != w.user_id:
        return error(request)
    w.content = content
    w.save()
    return redirect('/weibo?user_id={}'.format(user.id))


def login_required(route_function):
    """
    用来验证用户身份
    """
    def func(request):
        username = current_user(request)
        log('登录验证', username)
        if username == 'guest':
            return redirect('/login')
        return route_function(request)
    return func


route_dict = {
    '/weibo': route_weibo_index,
    '/weibo/new': login_required(route_weibo_new),
    '/weibo/add': login_required(route_weibo_add),
    '/weibo/delete': login_required(route_weibo_delete),
    '/weibo/edit': login_required(route_weibo_edit),
    '/weibo/update': login_required(route_weibo_update),
}