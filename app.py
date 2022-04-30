from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

# create app object
app = Flask(__name__)

# render template


@app.route('/')
def index():
    return render_template('index.html')


# run app
if __name__ == '__main__':
    app.debug = True

    app.run(debug=True)
