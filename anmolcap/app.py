from flask import Flask, render_template, request, jsonify, redirect, url_for
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
import io

app = Flask(__name__)

def parse_data(file_content):
    data = []
    current_altitude = None
    current_location = None
    current_windspeed = None
    current_temperature = None
    current_time = None
    
    for line in file_content.split('\n'):
        if line.startswith('Altitude='):
            parts = line.split(';')
            current_altitude = float(parts[0].split('=')[1].split('m')[0].strip())
            current_location = parts[1].split('=')[1].strip()
            current_windspeed = float(parts[2].split('=')[1].split('km/hr')[0].strip())
            current_temperature = float(parts[3].split('=')[1].split("'C")[0].strip())
            current_time = parts[4].split('=')[1].strip()
        elif 'CO Concentration:' in line:
            parts = line.split('|')
            time = parts[0].split(':')[3].strip()
            co = float(parts[1].split(':')[1].strip().split()[0])
            h2 = float(parts[2].split(':')[1].strip().split()[0])
            dust = float(parts[3].split(':')[1].strip().split()[0])
            data.append({
                'Altitude': current_altitude,
                'Location': current_location,
                'Windspeed': current_windspeed,
                'Temperature': current_temperature,
                'Timestamp': current_time,
                'Time': time,
                'CO': co,
                'H2': h2,
                'Dust': dust
            })
    return pd.DataFrame(data)

def create_detailed_graphs(df):
    graphs = {}
    
   
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.02,
                        subplot_titles=("CO Concentration", "H2 Concentration", "Dust Concentration"))
    
    for i, metric in enumerate(['CO', 'H2', 'Dust'], 1):
        for altitude in df['Altitude'].unique():
            df_alt = df[df['Altitude'] == altitude]
            fig.add_trace(go.Scatter(x=df_alt['Time'], y=df_alt[metric], name=f'{metric} at {altitude}m',
                                     mode='lines+markers'), row=i, col=1)
    
    fig.update_layout(height=900, title_text="Air Quality Metrics Over Time at Different Altitudes",
                      showlegend=True, legend_title="Metrics and Altitudes")
    fig.update_xaxes(title_text="Time", row=3, col=1)
    fig.update_yaxes(title_text="ppm", row=1, col=1)
    fig.update_yaxes(title_text="ppm", row=2, col=1)
    fig.update_yaxes(title_text="µg/m³", row=3, col=1)
    
    graphs['time_series'] = pio.to_json(fig)
    
    
    fig_3d = go.Figure(data=[go.Scatter3d(
        x=df['CO'],
        y=df['H2'],
        z=df['Dust'],
        mode='markers',
        marker=dict(
            size=5,
            color=df['Altitude'],
            colorscale='Viridis',
            opacity=0.8
        ),
        text=[f"Altitude: {a}m<br>Time: {t}<br>CO: {c} ppm<br>H2: {h} ppm<br>Dust: {d} µg/m³" 
              for a, t, c, h, d in zip(df['Altitude'], df['Time'], df['CO'], df['H2'], df['Dust'])],
        hoverinfo='text'
    )])
    
    fig_3d.update_layout(scene=dict(
        xaxis_title='CO (ppm)',
        yaxis_title='H2 (ppm)',
        zaxis_title='Dust (µg/m³)'),
        title="3D Scatter Plot of Air Quality Metrics"
    )
    
    graphs['3d_scatter'] = pio.to_json(fig_3d)
    
    
    for metric in ['CO', 'H2', 'Dust']:
        fig_box = go.Figure()
        for altitude in sorted(df['Altitude'].unique()):
            fig_box.add_trace(go.Box(y=df[df['Altitude'] == altitude][metric], name=f'{altitude}m'))
        
        fig_box.update_layout(title_text=f"{metric} Distribution by Altitude",
                              xaxis_title="Altitude (m)",
                              yaxis_title=f"{metric} Concentration ({'µg/m³' if metric == 'Dust' else 'ppm'})")
        
        graphs[f'{metric.lower()}_box'] = pio.to_json(fig_box)
    
    return graphs

@app.route('/', methods=['GET', 'POST'])
# def index():
    # if request.method == 'POST':
        # file = request.files['file']
        # if file:
            # file_content = file.read().decode('utf-8')
            # df = parse_data(file_content)
            # graphs = create_detailed_graphs(df)
            # return jsonify(graphs)
    # return render_template('index.html')

# if __name__ == '__main__':
    # app.run(debug=True)
def upload_page():
    return render_template('index.html')
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file part", 400  
    
    file = request.files['file']
    
    if file.filename == '':
        return "No selected file", 400 
    
    # if file:
        # try:
            # Read the file and process the data
            # file_content = file.read().decode('utf-8')
            # df = parse_data(file_content)
            
            # Create graphs and store them globally
            # global graphs
            # graphs = create_detailed_graphs(df)
            
            # Redirect to the result page to display the graphs
            # return redirect(url_for('result_page'))
        
        # except Exception as e:
            # Handle any exceptions that may arise during file processing
            # return f"An error occurred while processing the file: {str(e)}", 500  # Return 500 Internal Server Error

    # If no valid file is uploaded, return a response
    if file:
        try:
            
            file_content = file.read().decode('utf-8')
            df = parse_data(file_content)
            
            global graphs
            graphs = create_detailed_graphs(df)
            
            return jsonify({'status': 'success'})
        
        except Exception as e:
            return f"An error occurred while processing the file: {str(e)}", 500

    return "Invalid file", 400
 
@app.route('/result')
def result_page():
    return render_template('result.html')

@app.route('/get_graphs')
def get_graphs():
    
    global graphs
    return jsonify(graphs)

if __name__ == '__main__':
    app.run(debug=True)