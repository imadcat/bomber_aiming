import os
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import numpy as np
from scipy.optimize import fsolve
import plotly.graph_objs as go

app = dash.Dash(__name__)

# App layout
app.layout = html.Div([
    html.H1("Aiming Angle Calculation for Bomber and Fighter"),
    dcc.Graph(id='trajectory-plot'),
    html.Label("Bullet Velocity (m/s)"),
    dcc.Slider(id='v_bullet', min=500, max=1500, step=10, value=890,
               marks={i: str(i) for i in range(500, 1501, 100)}),
    html.Label("Bomber Velocity (m/s)"),
    dcc.Slider(id='v_bomber', min=50, max=300, step=10, value=100,
               marks={i: str(i) for i in range(50, 301, 50)}),
    html.Label("Fighter Velocity (m/s)"),
    dcc.Slider(id='v_fighter', min=50, max=500, step=10, value=150,
               marks={i: str(i) for i in range(50, 501, 50)}),
    html.Label("Horizontal Distance (m)"),
    dcc.Slider(id='d', min=500, max=5000, step=100, value=1000,
               marks={i: str(i) for i in range(500, 5001, 500)}),
    html.Label("Initial Fighter Y (m)"),
    dcc.Slider(id='initial_fighter_y', min=100, max=2000, step=50, value=500,
               marks={i: str(i) for i in range(100, 2001, 200)})
])

@app.callback(
    Output('trajectory-plot', 'figure'),
    [Input('v_bullet', 'value'),
     Input('v_bomber', 'value'),
     Input('v_fighter', 'value'),
     Input('d', 'value'),
     Input('initial_fighter_y', 'value')]
)
def update_plot(v_bullet, v_bomber, v_fighter, d, initial_fighter_y):
    # Function to calculate the aiming angle and plot the trajectories
    def calculate_trajectory(v_bullet, v_bomber, v_fighter, d, initial_fighter_y):
        # Define the equations to solve for the time t and angle phi
        def equations(vars):
            t, phi = vars
            x_bullet = v_bomber * t + v_bullet * np.cos(phi) * t
            y_bullet = v_bullet * np.sin(phi) * t
            x_fighter = d
            y_fighter = initial_fighter_y - v_fighter * t
            return [x_bullet - x_fighter, y_bullet - y_fighter]

        # Initial guess for t and phi
        initial_guess = [1.0, np.arctan(initial_fighter_y / d)]

        # Solve the equations
        solution = fsolve(equations, initial_guess)
        t_solution, phi_solution = solution

        # Convert the angle to degrees
        theta_degrees = np.degrees(phi_solution)

        # Generate time points for plotting the bullet trajectory
        t_total = np.linspace(0, t_solution, 100)
        x_bullet_trajectory = v_bomber * t_total + v_bullet * np.cos(phi_solution) * t_total
        y_bullet_trajectory = v_bullet * np.sin(phi_solution) * t_total

        # Calculate the aiming direction line based on phi_solution
        aiming_line_length = d * 1.5  # Extend the aiming line for better visualization
        aiming_line_x = [0, aiming_line_length * np.cos(phi_solution) * 10]
        aiming_line_y = [0, aiming_line_length * np.sin(phi_solution) * 10]

        return t_solution, phi_solution, x_bullet_trajectory, y_bullet_trajectory, theta_degrees, aiming_line_x, aiming_line_y

    # Get the plot data and aiming angle
    t_solution, phi_solution, x_bullet_trajectory, y_bullet_trajectory, theta_degrees, aiming_line_x, aiming_line_y = calculate_trajectory(
        v_bullet, v_bomber, v_fighter, d, initial_fighter_y
    )

    # Plotting data
    bomber_path = go.Scatter(x=[0, v_bomber * t_solution], y=[0, 0], mode='lines', name='Bomber Path', line=dict(color='blue', width=3))
    fighter_path = go.Scatter(x=[d, d], y=[initial_fighter_y, initial_fighter_y - v_fighter * t_solution], mode='lines', name='Fighter Path', line=dict(color='green', width=3))

    bullet_trajectory = go.Scatter(
        x=x_bullet_trajectory, y=y_bullet_trajectory, mode='lines', name='Bullet Trajectory', line=dict(color='red')
    )

    aiming_direction = go.Scatter(
        x=aiming_line_x, y=aiming_line_y, mode='lines', name='Aiming Direction',
        line=dict(dash='dot', color='orange')
    )

    # Points for initial and impact positions
    # Unicode airplane symbols
    airplane_symbols = ['✈️', '🛩️', '🛫', '🛬', '✈️']

    # # Scatter plot with airplane symbols as text
    # scatter_airplanes = go.Scatter(
    #     x=x, y=y,
    #     mode='markers+text',
    #     marker=dict(size=10),
    #     text=airplane_symbols,
    #     textfont=dict(size=20),  # Adjust the font size of the airplane symbols
    #     textposition='top center',  # Position the text above the markers
    #     name='Airplane Symbols'
    # )

    initial_bomber_point = go.Scatter(
        x=[0], y=[0],
        mode='markers+text', name='✈️Initial Bomber Position', 
        text='✈️', textfont=dict(size=20), textposition='middle center', 
        marker=dict(color='blue', size=10, symbol='circle')
    )

    impact_bomber_point = go.Scatter(
        x=[v_bomber * t_solution], y=[0],
        mode='markers', name='Impact Bomber Position',
        marker=dict(color='blue', size=10, symbol='x')
    )

    initial_fighter_point = go.Scatter(
        x=[d], y=[initial_fighter_y],
        mode='markers+text', name='🛩️Initial Fighter Position', 
        text='🛩️', textfont=dict(size=20), textposition='middle center', 
        marker=dict(color='green', size=10, symbol='square')
    )

    impact_fighter_point = go.Scatter(
        x=[d], y=[initial_fighter_y - v_fighter * t_solution],
        mode='markers', name='Impact Fighter Position',
        marker=dict(color='green', size=10, symbol='x')
    )

    # Create the plot layout with larger plot area
    layout = go.Layout(
        title=f'Aiming Angle: {theta_degrees:.2f} degrees',
        xaxis=dict(title='Horizontal Distance (m)', showgrid=True, range=[-100, d * 1.1]),
        yaxis=dict(title='Vertical Distance (m)', showgrid=True, range=[initial_fighter_y * -1.1, initial_fighter_y * 1.1]),
        showlegend=True,
        legend=dict(
            x=1,  # Position the legend outside the plot on the right
            y=1,
            xanchor='left',  # Anchor the legend's x position to the left
            yanchor='top',   # Anchor the legend's y position to the top
            bordercolor="Black",
            borderwidth=1
        )
    )

    # Create the figure
    figure = go.Figure(data=[bomber_path, fighter_path, bullet_trajectory, aiming_direction,
                            initial_bomber_point, impact_bomber_point,
                            initial_fighter_point, impact_fighter_point], layout=layout)

    return figure

# Run the app
if __name__ == "__main__":
    app.run_server(host='0.0.0.0', port=int(os.environ.get("PORT", 8050)))