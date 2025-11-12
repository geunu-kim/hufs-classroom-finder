from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def home():
    # 기본 주소에 접속했을 때 login 페이지를 보여줌
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == '1234':
            return "Login successful"
        else:
            return "Login failed"
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)
