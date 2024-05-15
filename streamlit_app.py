import streamlit as st
import numpy as np
from scipy.optimize import fsolve
import plotly.graph_objs as go
from scipy.integrate import solve_ivp
import scipy.integrate as integrate
from numpy import interp

def bullet_velocity_function(t, v0=890):
    # Define the bullet velocity function
    g = 9.81  # Acceleration due to gravity (m/s^2)
    rho = 1.225  # Air density (kg/m^3)
    cd = 0.5  # Drag coefficient
    r = 0.08  # Radius of the bullet (m)
    m = 1.0  # Mass of the bullet (kg)
    A = np.pi * r**2  # Cross-sectional area of the bullet (m^2)
    k = 0.5 * rho * cd * A  # Drag factor
    return v0 * np.exp(-k * t / m)

def bullet_position_function(t, v0=890):
    # Calculate the bullet position as a function of time
    result, error = integrate.quad(bullet_velocity_function, 0, t, args=(v0,))
    return result

# Streamlit app
def main():
    st.title("Bomber Turret Aiming Caculator")

    # Sliders
    d = st.slider("Horizontal Distance (m)", min_value=100, max_value=2000, step=100, value=500)
    initial_fighter_y = st.slider("Initial Fighter Y (m)", min_value=100, max_value=2000, step=50, value=500)
    with st.expander("More Parameters"):
        st.write('''
            You can also adjust the bullet velocity, bomber velocity, and fighter velocity using the sliders below.
        ''')
        v_bullet = st.slider("Bullet Velocity (m/s)", min_value=500, max_value=1000, step=10, value=890)
        v_bomber = st.slider("Bomber Velocity (m/s)", min_value=50, max_value=300, step=10, value=100)
        v_fighter = st.slider("Fighter Velocity (m/s)", min_value=50, max_value=500, step=10, value=150)

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
        aiming_line_length = d * 2  # Extend the aiming line for better visualization
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
        mode='markers+text', name='✈️ Initial Bomber Position',
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
        mode='markers+text', name='🛩️ Initial Fighter Position',
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
        yaxis=dict(title='Vertical Distance (m)', showgrid=True, range=[min(impact_fighter_y* 1.2, -100), initial_fighter_y * 1.2]),
        showlegend=True,
        legend=dict(
            orientation="h",  # Horizontal orientation
            x=0,            # Center horizontally
            y=-0.3,           # Position below the plot area
            xanchor='left', # Anchor the x
            yanchor='top',
            ncol=2
        ),
        dragmode=False,
        autosize=True,  # Automatically adjust the plot size
        width=None,  # Set the width to None to make it responsive
        height=600
    )

    # Create the figure
    figure = go.Figure(data=[bomber_path, fighter_path, bullet_trajectory, aiming_direction,
                        initial_bomber_point, impact_bomber_point,
                        initial_fighter_point, impact_fighter_point])

    figure.update_layout(layout)

    # Display the plot using Streamlit
    st.plotly_chart(figure, use_container_width=True)

if __name__ == "__main__":
    main()