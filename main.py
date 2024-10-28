from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    name = "PyCharm"
    return f'Hi, {name}!'

if __name__ == '__main__':
    app.run(debug=True)
