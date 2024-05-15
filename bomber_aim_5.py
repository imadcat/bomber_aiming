import os
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import numpy as np
from scipy.optimize import fsolve
import plotly.graph_objs as go
from scipy.integrate import solve_ivp
import scipy.integrate as integrate
from numpy import interp

def bullet_position_function(t, v0 = 890):
    ## This differential equation can be solved numerically to obtain the velocity as a function of time
    # Constants  # initial velocity in m/s
    m = 0.045  # mass in kg
    Cd = 0.295  # drag coefficient
    A = 0.000071  # cross-sectional area in m^2
    rho = 1.225  # air density in kg/m^3

    # Differential equation for velocity reduction
    def velocity_reduction(t, v):
        return - (0.5 * rho * v**2 * Cd * A) / m

    # Time span (0 to 10 seconds)
    t_span = (0, t)
    # Initial condition
    v_init = [v0]

    # Solving the differential equation
    sol = solve_ivp(velocity_reduction, t_span, v_init, t_eval=np.linspace(0, t, 500))

    def bullet_velocity_function(t):
        # global t_span, sol
        # if t_span is None or sol is None:
        #     raise ValueError("Solution values have not been computed yet.")    
        # Create an interpolation function using the solution values
        # Evaluate the interpolation function at the given time t
        return interp(t, np.linspace(0, t, 500), sol.y[0])

    result, error = integrate.quad(bullet_velocity_function, 0, t)
    return result

app = dash.Dash(__name__)

# App layout
app.layout = html.Div([
    html.H1("Aiming Angle Calculation for Bomber Turret Gunner to Hit the Fighter"),
    dcc.Graph(id='trajectory-plot'),
    html.Label("Horizontal Distance (m)"),
    dcc.Slider(id='d', min=100, max=2000, step=100, value=500,
               marks={i: str(i) for i in range(100, 2000, 500)}),
    html.Label("Initial Fighter Y (m)"),
    dcc.Slider(id='initial_fighter_y', min=100, max=2000, step=50, value=500,
               marks={i: str(i) for i in range(100, 2001, 200)}),
    html.Label("Bullet Velocity (m/s)"),
    dcc.Slider(id='v_bullet', min=500, max=1000, step=10, value=890,
               marks={i: str(i) for i in range(500, 1501, 100)}),
    html.Label("Bomber Velocity (m/s)"),
    dcc.Slider(id='v_bomber', min=50, max=300, step=10, value=100,
               marks={i: str(i) for i in range(50, 301, 50)}),
    html.Label("Fighter Velocity (m/s)"),
    dcc.Slider(id='v_fighter', min=50, max=500, step=10, value=150,
               marks={i: str(i) for i in range(50, 501, 50)})
])

@app.callback(
    [Output('trajectory-plot', 'figure'),
     Output('trajectory-plot', 'style')],
    [Input('d', 'value'),
     Input('initial_fighter_y', 'value'),
     Input('v_bullet', 'value'),
     Input('v_bomber', 'value'),
     Input('v_fighter', 'value')]
)
def update_plot(d, initial_fighter_y, v_bullet, v_bomber, v_fighter):
    # Function to calculate the aiming angle and plot the trajectories
    def calculate_trajectory(v_bullet, v_bomber, v_fighter, d, initial_fighter_y):
        # Define the equations to solve for the time t and angle phi
        def equations(vars):
            t, phi = vars
            v0_bullet_x = v_bomber + v_bullet * np.cos(phi)
            v0_bullet_y = v_bullet * np.sin(phi)
            v0_bullet_norm = (v0_bullet_x**2 + v0_bullet_y**2)**0.5
            bullet_postion_norm = bullet_position_function(t, v0_bullet_norm)
            x_bullet = bullet_postion_norm * v0_bullet_x / v0_bullet_norm
            y_bullet = bullet_postion_norm * v0_bullet_y / v0_bullet_norm
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
    bomber_path = go.Scatter(x=[0, v_bomber * t_solution], y=[0, 0], 
                             mode='lines', name='Bomber Path', line=dict(color='blue', width=3))
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

    impact_fighter_y = initial_fighter_y - v_fighter * t_solution
    impact_fighter_point = go.Scatter(
        x=[d], y=[impact_fighter_y],
        mode='markers', name='Impact Fighter Position',
        marker=dict(color='green', size=10, symbol='x')
    )

    # Create the plot layout with larger plot area
    layout = go.Layout(
        title=f'Aiming Angle: {theta_degrees:.2f} degrees',
        xaxis=dict(title='Horizontal Distance (m)', showgrid=True, range=[-10, d * 1.1],
                   scaleanchor='y'),  # Ensure the x-axis is scaled to the y-axis),
        yaxis=dict(title='Vertical Distance (m)', showgrid=True, range=[min(impact_fighter_y* 1.2, -100), initial_fighter_y * 1.2],
                #    scaleratio=1
                ),      # Same ratio for the y-axis to maintain equal scaling),
        showlegend=True,
        legend=dict(
            orientation="h",  # Horizontal orientation
            x=0,            # Center horizontally
            y=-0.3,           # Position below the plot area
            xanchor='left', # Anchor the x position at the center
            yanchor='top'
        ),
        dragmode=False
    )

    # Calculate the new height based on the "d" value
    max_x = d * 1.1 + 10
    max_y = initial_fighter_y * 1.2 - min(impact_fighter_y, -100)
    # Example scaling: adjust the divisor as needed
    new_width = f"{100}vw" 
    new_height = f"{max(min(max_y / max_x * 100, 100), 50)}vh"
    # Update the style with the new height
    new_style = {
        'width': new_width,
        'height': new_height
    }

    # Create the figure
    figure = go.Figure(data=[bomber_path, fighter_path, bullet_trajectory, aiming_direction,
                        initial_bomber_point, impact_bomber_point,
                        initial_fighter_point, impact_fighter_point])

    figure.update_layout(layout,
                        uirevision=True)

    return figure, new_style

# Run the app
if __name__ == "__main__":
    app.run_server(host='0.0.0.0', port=int(os.environ.get("PORT", 8050)), debug=True)