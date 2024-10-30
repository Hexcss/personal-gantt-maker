import json
import plotly.express as px
from datetime import datetime, timedelta
import plotly.io as pio
from dash import Dash, dcc, html, Output, Input, State
import dash 
import os
import base64


# Define a function to read the JSON file and prepare the Gantt chart data
def prepare_gantt_data(json_file):
    with open(json_file, 'r') as file:
        data = json.load(file)
    chart_name = data.get("chart_name", "Project Gantt Chart")  # Get chart name from JSON
    tasks = []
    for section in data.get("sections", []):
        section_name = section['section_name']
        for task in section['tasks']:
            task_name = task['task_name']
            start_date = datetime.strptime(task['start_date'], '%Y-%m-%d')
            duration_days = task['duration_days']
            end_date = start_date + timedelta(days=duration_days)
            is_critical = task.get('is_critical', False)
            tasks.append({
                "Task": f"{task_name}",
                "Start": start_date,
                "Finish": end_date,
                "Critical Path": "Critical" if is_critical else "Non-Critical",
                "Section": section_name
            })
    return tasks, chart_name

# Define a function to create the Gantt chart figure
def create_gantt_figure(tasks, chart_title):
    color_map = {"Critical": "#C81D25", "Non-Critical": "#3C4E66"}
    fig = px.timeline(
        tasks, 
        x_start="Start", 
        x_end="Finish", 
        y="Task", 
        color="Critical Path",
        color_discrete_map=color_map,
        title=chart_title
    )
    fig.update_layout(
        plot_bgcolor="#F4F4F9",
        paper_bgcolor="#F4F4F9",
        xaxis_title="Timeline",
        yaxis_title="Tasks",
        title_x=0.5,
        xaxis=dict(tickformat="%Y-%m"),
        height=600,
        font=dict(family="Arial", color="#3C4E66"),
        title_font=dict(size=24, family="Arial Black", color="#3C4E66")
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=False, categoryorder="total ascending")
    return fig

# Initialize Dash app
app = Dash(__name__)

# Helper function to load JSON files in the folder
def load_json_files():
    json_files = [
        {"file": os.path.join("json", f), "name": json.load(open(os.path.join("json", f))).get("chart_name", f)} 
        for f in os.listdir("json") if f.endswith('.json')
    ]
    return json_files

# Get initial JSON files list
json_files = load_json_files()

# Define layout with improved styling and upload functionality
app.layout = html.Div([
    # Sidebar
    html.Div(
        [
            html.H2("Select Chart", style={"color": "#3C4E66", "textAlign": "center", "marginBottom": "20px"}),
            dcc.Dropdown(
                id="json-selector",
                options=[{"label": item["name"], "value": item["file"]} for item in json_files],
                value=json_files[0]["file"] if json_files else None,  # Default selection if available
                clearable=False,
                style={
                    "padding": "0px",
                    "borderRadius": "8px",
                    "fontFamily": "Arial",
                    "fontSize": "16px",
                    "backgroundColor": "#FFFFFF"
                }
            ),
            dcc.Upload(
                id="upload-json",
                children=html.Button("Upload JSON", style={
                    "width": "100%",
                    "padding": "10px",
                    "backgroundColor": "#3C4E66",
                    "color": "white",
                    "border": "none",
                    "borderRadius": "5px",
                    "marginTop": "20px",
                    "fontFamily": "Arial"
                }),
                style={"textAlign": "center"},
                multiple=False  # Only allow one file at a time
            ),
            html.Button("Export to PNG", id="export-button", style={
                "marginTop": "20px",
                "width": "100%",
                "padding": "10px",
                "backgroundColor": "#3C4E66",
                "color": "white",
                "border": "none",
                "borderRadius": "5px",
                "fontFamily": "Arial"
            }),
            html.Div(id="export-message", style={"marginTop": "10px", "color": "#3C4E66", "textAlign": "center"})
        ],
        style={
            "width": "20%", 
            "padding": "20px", 
            "backgroundColor": "#EFEFEF", 
            "boxShadow": "2px 2px 10px rgba(0, 0, 0, 0.1)",
            "height": "100vh",
            "overflowY": "auto"
        }
    ),
    # Main Content
    html.Div(
        [
            html.H1("Booze & Bites Project Gantt Chart", style={"textAlign": "center", "color": "#3C4E66", "marginBottom": "20px"}),
            dcc.Graph(id="gantt-chart")
        ],
        style={
            "width": "75%", 
            "padding": "20px",
            "backgroundColor": "#FFFFFF", 
            "boxShadow": "2px 2px 10px rgba(0, 0, 0, 0.1)"
        }
    )
], style={"display": "flex", "flexDirection": "row", "border": "0"})

# Callback to update the Gantt chart based on the selected JSON file
@app.callback(
    Output("gantt-chart", "figure"),
    Input("json-selector", "value")
)
def update_gantt_chart(json_file):
    tasks, chart_name = prepare_gantt_data(json_file)
    return create_gantt_figure(tasks, chart_name)

# Callback to export the Gantt chart as a PNG
@app.callback(
    Output("export-message", "children"),
    Input("export-button", "n_clicks"),
    State("json-selector", "value")
)
def export_chart(n_clicks, json_file):
    if n_clicks:
        tasks, chart_name = prepare_gantt_data(json_file)
        fig = create_gantt_figure(tasks, chart_name)
        output_filename = os.path.basename(json_file).replace('.json', '_gantt_chart.png')
        pio.write_image(fig, output_filename)
        return f"Gantt chart exported as '{output_filename}'"
    return ""

# Callback to handle JSON file upload and update the dropdown options
@app.callback(
    Output("json-selector", "options"),
    Output("json-selector", "value"),
    Input("upload-json", "contents"),
    State("upload-json", "filename")
)
def upload_json(contents, filename):
    if contents is not None:
        # Decode and save the uploaded file
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string).decode("utf-8")
        
        file_path = os.path.join("json", filename)
        with open(file_path, "w") as file:
            file.write(decoded)
        
        # Reload JSON files after upload
        json_files = load_json_files()
        
        # Update the dropdown with new options and set the newly uploaded file as selected
        options = [{"label": item["name"], "value": item["file"]} for item in json_files]
        return options, file_path
    return dash.no_update, dash.no_update

# Run the Dash app
if __name__ == "__main__":
    app.run_server(debug=True)
