
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import json
import urllib.parse

# create app object
app = Flask(__name__)

# render template


@app.route('/', methods=['GET', 'POST'])
# make function with post request
def index():
    if request.method == 'POST':
        # get request data
        data = request.get_data()
        # decode data
        # data = json.loads(data)
        decoded = urllib.parse.unquote(data)

        print(data)
        print(decoded)
        # turn decoded data into json

        decoded = decoded.split('&')
        print(decoded)
        # create dictionary
        decoded = {i.split('=')[0]: i.split('=')[1] for i in decoded}
        print(decoded)
        # decoded = decoded.replace('=', ':')
        # # add curly braces
        # decoded = '{' + decoded + '}'
        # convert to json
        # decoded = json.loads(decoded)

        return decoded

    return render_template('index.html')


# run app
if __name__ == '__main__':
    app.debug = True

    app.run(debug=True)
