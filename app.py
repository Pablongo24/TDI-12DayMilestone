from flask import Flask, render_template, request, redirect

app = Flask(__name__)

@app.route('/')
def index():
  return render_template('index.html')

@app.route('/about')
def about():
  return render_template('about.html')

# Just adding a comment to commit and rebuild in Heroku

if __name__ == '__main__':
  app.run(port=33507)
