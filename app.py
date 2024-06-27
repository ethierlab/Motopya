from flask import Flask, render_template, request, jsonify
import matplotlib.pyplot as plt
import numpy as np
import os

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    data = request.get_json()
    rat_id = data['rat_id']
    save_location = data['save_location']
    calibration_file = data['calibration_file']
    return jsonify(status='success', rat_id=rat_id, save_location=save_location, calibration_file=calibration_file)

@app.route('/plot')
def plot():
    t = np.linspace(0, 1, 100)
    angle = np.sin(2 * np.pi * t)
    
    fig, ax = plt.subplots()
    ax.plot(t, angle)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Angle (deg)')
    ax.set_title('Knob Rotation Angle')
    
    plot_path = os.path.join('static', 'plot.png')
    plt.savefig(plot_path)
    plt.close(fig)
    
    return jsonify(status='success', plot_url=plot_path)

if __name__ == "__main__":
    app.run(debug=True)
