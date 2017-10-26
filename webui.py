from flask import Flask, render_template
import plotly
app = Flask(__name__)
app.debug = True

class TermoUI:
    sensors = []
    def __init__(self, sensors):

        self.sensors = sensors

    @app.route("/")
    def hello(self):
        return self.sensors[0].name
