import jwt
import datetime
import hashlib
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for
from pymongo import MongoClient
from bs4 import BeautifulSoup
import requests

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['UPLOAD_FOLDER'] = "./static/profile_pics"

SECRET_KEY = 'CLOUD'

client = MongoClient('3.34.112.104', 27017, username="jiwoon", password="cloudthecat")
db = client.norandp


@app.route('/')
def main():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        # DB에서 저장된 단어 찾아서 HTML에 나타내기
        msg = request.args.get("msg")
        words = list(db.words.find({}, {"_id": False}))
        return render_template("index.html", words=words, user_info=user_info, msg=msg)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))


# todo 단어 뜻과 예문 구분해서 나오게
# todo method exact로 받아오기(국립국어원 문제)
# todo footer 추가하기
# todo https://krdict.korean.go.kr/regist/commentSuggestView 처럼 챕터 나누기
# 가나다(역순 가능하게), 최신순(역순 가능하게), 디자인팀, 작업팀, 사무팀, 경영부

@app.route('/timeline')
def home():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        # status = (username == payload["id"])  # 내 프로필이면 True, 다른 사람 프로필 페이지면 False

        return render_template('timeline.html', user_info=user_info)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))


@app.route('/login')
def login():
    msg = request.args.get("msg")
    return render_template('login.html', msg=msg)


@app.route('/user/<username>')
def user(username):
    # 각 사용자의 프로필과 글을 모아볼 수 있는 공간
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        status = (username == payload["id"])  # 내 프로필이면 True, 다른 사람 프로필 페이지면 False
        my_username = payload["id"]

        user_info = db.users.find_one({"username": username}, {"_id": False})
        return render_template('user.html', user_info=user_info, status=status, logged_one=my_username)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


@app.route('/sign_in', methods=['POST'])
def sign_in():
    # 로그인
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']

    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    result = db.users.find_one({'username': username_receive, 'password': pw_hash})

    if result is not None:
        payload = {
            'id': username_receive,
            'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)  # 로그인 24시간 유지
        }
        # token = jwt.encode(payload, SECRET_KEY, algorithm='HS256').decode('utf-8')
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})


@app.route('/sign_up/save', methods=['POST'])
def sign_up():
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    doc = {
        "username": username_receive,
        "password": password_hash,
        "profile_name": username_receive,
        "profile_pic": "",
        "profile_pic_real": "profile_pics/profile_placeholder.png",
        "profile_info": ""
    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})


@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    username_receive = request.form['username_give']
    exists = bool(db.users.find_one({"username": username_receive}))
    # print(value_receive, type_receive, exists)
    return jsonify({'result': 'success', 'exists': exists})


@app.route('/update_profile', methods=['POST'])
def save_img():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        username = payload["id"]
        name_receive = request.form["name_give"]
        about_receive = request.form["about_give"]
        new_doc = {
            "profile_name": name_receive,
            "profile_info": about_receive
        }
        if 'file_give' in request.files:
            file = request.files["file_give"]
            filename = secure_filename(file.filename)
            extension = filename.split(".")[-1]
            file_path = f"profile_pics/{username}.{extension}"
            file.save("./static/" + file_path)
            new_doc["profile_pic"] = filename
            new_doc["profile_pic_real"] = file_path
        db.users.update_one({'username': payload['id']}, {'$set': new_doc})
        return jsonify({"result": "success", 'msg': '프로필을 업데이트했습니다.'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


@app.route('/posting', methods=['POST'])
def posting():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        # 포스팅하기
        user_info = db.users.find_one({"username": payload["id"]})
        comment_receive = request.form["comment_give"]
        date_receive = request.form["date_give"]
        print(type(date_receive))
        doc = {
            "username": user_info["username"],
            "profile_name": user_info["profile_name"],
            "profile_pic_real": user_info["profile_pic_real"],
            "comment": comment_receive,
            "date": date_receive
        }
        db.posts.insert_one(doc)
        return jsonify({"result": "success", 'msg': '포스팅 성공'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


@app.route("/get_posts", methods=['GET'])
def get_posts():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        my_username = payload["id"]
        username_receive = request.args.get("username_give")
        if username_receive == "":
            posts = list(db.posts.find({}).sort("date", -1).limit(20))
        else:
            posts = list(db.posts.find({"username": username_receive}).sort("date", -1).limit(20))

        for post in posts:
            post["_id"] = str(post["_id"])

            post["count_heart"] = db.likes.count_documents({"post_id": post["_id"], "type": "heart"})
            post["heart_by_me"] = bool(
                db.likes.find_one({"post_id": post["_id"], "type": "heart", "username": my_username}))

            post["count_star"] = db.likes.count_documents({"post_id": post["_id"], "type": "star"})
            post["star_by_me"] = bool(
                db.likes.find_one({"post_id": post["_id"], "type": "star", "username": my_username}))

            post["count_like"] = db.likes.count_documents({"post_id": post["_id"], "type": "like"})
            post["like_by_me"] = bool(
                db.likes.find_one({"post_id": post["_id"], "type": "like", "username": my_username}))

        return jsonify({"result": "success", "msg": "포스팅을 가져왔습니다.", "posts": posts, "logged_one": my_username})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


@app.route('/update_like', methods=['POST'])
def update_like():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        # 좋아요 수 변경
        user_info = db.users.find_one({"username": payload["id"]})
        post_id_receive = request.form["post_id_give"]
        type_receive = request.form["type_give"]
        action_receive = request.form["action_give"]
        doc = {
            "post_id": post_id_receive,
            "username": user_info["username"],
            "type": type_receive
        }
        if action_receive == "like":
            db.likes.insert_one(doc)
        else:
            db.likes.delete_one(doc)
        count = db.likes.count_documents({"post_id": post_id_receive, "type": type_receive})
        print(count)
        return jsonify({"result": "success", 'msg': 'updated', "count": count})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


# @app.route('/')
# def main():
#     token_receive = request.cookies.get('mytoken')
#     try:
#         payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
#         user_info = db.users.find_one({"username": payload["id"]})
#         # DB에서 저장된 단어 찾아서 HTML에 나타내기
#         words = list(db.words.find({}, {"_id": False}))
#         return render_template("dic_index.html", words=words, user_info=user_info)
#     except jwt.ExpiredSignatureError:
#         return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
#     except jwt.exceptions.DecodeError:
#         return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))


# @app.route('/detail/<keyword>')
# def detail(keyword):
#     status_receive = request.args.get("status_give")
#     # API에서 단어 뜻 찾아서 결과 보내기
#     r = requests.get(f"https://owlbot.info/api/v4/dictionary/{keyword}",
#                      headers={"Authorization": "Token 124f0fea89b8903847bfd1e154a7b4243e7de32e"})
#     if r.status_code != 200:
#         return redirect(url_for("main", msg="단어가 이상해요."))
#     result = r.json()
#     print(result)
#     return render_template("dic_detail.html", word=keyword, result=result, status=status_receive)

@app.route('/detail/<keyword>')
def detail(keyword):
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        # API에서 단어 뜻 찾아서 결과 보내기
        status_receive = request.args.get("status_give")
        info_url = f'https://krdict.korean.go.kr/api/search?certkey_no=2996&key=4EAEC6FF14FC700B8191E35AE2DA82EA&type_search=search&method=WORD_INFO&part=word&q={keyword}&sort=popular&method=exact'
        response = requests.get(info_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        if not soup.find_all('item'):
            return redirect(url_for("main", msg="단어가 이상해요."))
        result = soup.find_all('item')
        exam_url = f'https://krdict.korean.go.kr/api/search?certkey_no=2996&key=4EAEC6FF14FC700B8191E35AE2DA82EA&type_search=search&method=WORD_INFO&part=exam&q={keyword}&sort=popular&method=exact'
        response = requests.get(exam_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        exams = soup.find_all('item')
        sign_url = f'http://api.kcisa.kr/openapi/service/rest/meta13/getCTE01703?serviceKey=6fd81bfb-2933-4a7c-b375-073797a57610'
        response = requests.get(sign_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        signs = soup.find_all('items')
        print(signs)
        return render_template("detail.html", word=keyword, result=result, status=status_receive, exams=exams,
                               signs=signs, user_info=user_info)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))


@app.route('/api/save_word', methods=['POST'])
def save_word():
    # 단어 저장하기
    word_receive = request.form["word_give"]
    definition_receive = request.form["definition_give"]
    doc = {"word": word_receive, "definition": definition_receive}
    db.words.insert_one(doc)
    return jsonify({'result': 'success', 'msg': f'단어 {word_receive} 저장'})


@app.route('/api/delete_word', methods=['POST'])
def delete_word():
    # 단어 삭제하기
    word_receive = request.form["word_give"]
    db.words.delete_one({"word": word_receive})
    # db.examples.delete_many({"word": word_receive})
    return jsonify({'result': 'success', 'msg': f"단어 '{word_receive}' 삭제"})


@app.route('/api/get_examples', methods=['GET'])
def get_exs():
    # 예문 가져오기
    word_receive = request.args.get("word_give")
    sentences = list(db.examples.find({"word": word_receive}, {'_id': False}))
    definitions = list(db.definitions.find({"word": word_receive}, {'_id': False}))
    print(sentences)
    print(definitions)
    return jsonify({'result': 'success', 'all_sentence': sentences, 'all_definition': definitions})


@app.route('/api/save_ex', methods=['POST'])
def save_ex():
    # 예문 저장하기
    word_receive = request.form["word_give"]
    example_receive = request.form["example_give"]
    author_receive = request.form["author_give"]
    doc = {"word": word_receive, "sentence": example_receive, "author": author_receive}
    db.examples.insert_one(doc)
    return jsonify({'result': 'success'})


@app.route('/api/save_definition', methods=['POST'])
def save_definition():
    # 설명문 저장하기
    word_receive = request.form["word_give"]
    example_receive = request.form["example_give"]
    author_receive = request.form["author_give"]
    class_receive = request.form["class_give"]
    doc = {"word": word_receive, "sentence": example_receive, "author": author_receive, "word_class": class_receive}
    db.definitions.insert_one(doc)
    return jsonify({'result': 'success'})


@app.route('/api/delete_ex', methods=['POST'])
def delete_ex():
    # 예문 삭제하기
    word_receive = request.form["word_give"]
    number_receive = int(request.form["number_give"])
    example = list(db.examples.find({"word": word_receive}))[number_receive]["sentence"]
    db.examples.delete_one({"word": word_receive, "sentence": example})
    return jsonify({'result': 'success'})


@app.route('/api/delete_def', methods=['POST'])
def delete_def():
    # 예문 삭제하기
    word_receive = request.form["word_give"]
    number_receive = int(request.form["number_give"])
    definition = list(db.definitions.find({"word": word_receive}))[number_receive]["sentence"]
    db.definitions.delete_one({"word": word_receive, "sentence": definition})
    return jsonify({'result': 'success'})


@app.route('/api/delete_post', methods=['POST'])
def delete_post():
    post_receive = request.form['post_give']
    time_receive = request.form['time_give']
    db.posts.delete_one({'comment': post_receive, "date": time_receive})
    return jsonify({'msg': '게시글이 삭제되었습니다.'})


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)