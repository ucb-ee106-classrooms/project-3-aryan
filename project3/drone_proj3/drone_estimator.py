import matplotlib.pyplot as plt
import numpy as np
plt.rcParams['font.family'] = ['Arial']
plt.rcParams['font.size'] = 14


class Estimator:
    """A base class to represent an estimator.

    This module contains the basic elements of an estimator, on which the
    subsequent DeadReckoning, Kalman Filter, and Extended Kalman Filter classes
    will be based on. A plotting function is provided to visualize the
    estimation results in real time.

    Attributes:
    ----------
        u : list
            A list of system inputs, where, for the ith data point u[i],
            u[i][1] is the thrust of the quadrotor
            u[i][2] is right wheel rotational speed (rad/s).
        x : list
            A list of system states, where, for the ith data point x[i],
            x[i][0] is translational position in x (m),
            x[i][1] is translational position in z (m),
            x[i][2] is the bearing (rad) of the quadrotor
            x[i][3] is translational velocity in x (m/s),
            x[i][4] is translational velocity in z (m/s),
            x[i][5] is angular velocity (rad/s),
        y : list
            A list of system outputs, where, for the ith data point y[i],
            y[i][1] is distance to the landmark (m)
            y[i][2] is relative bearing (rad) w.r.t. the landmark
        x_hat : list
            A list of estimated system states. It should follow the same format
            as x.
        dt : float
            Update frequency of the estimator.
        fig : Figure
            matplotlib Figure for real-time plotting.
        axd : dict
            A dictionary of matplotlib Axis for real-time plotting.
        ln* : Line
            matplotlib Line object for ground truth states.
        ln_*_hat : Line
            matplotlib Line object for estimated states.
        canvas_title : str
            Title of the real-time plot, which is chosen to be estimator type.

    Notes
    ----------
        The landmark is positioned at (0, 5, 5).
    """
    # noinspection PyTypeChecker
    def __init__(self, is_noisy=False):
        self.u = []
        self.x = []
        self.y = []
        self.x_hat = []  # Your estimates go here!
        self.t = []
        self.fig, self.axd = plt.subplot_mosaic(
            [['xz', 'phi'],
             ['xz', 'x'],
             ['xz', 'z']], figsize=(20.0, 10.0))
        self.ln_xz, = self.axd['xz'].plot([], 'o-g', linewidth=2, label='True')
        self.ln_xz_hat, = self.axd['xz'].plot([], 'o-c', label='Estimated')
        self.ln_phi, = self.axd['phi'].plot([], 'o-g', linewidth=2, label='True')
        self.ln_phi_hat, = self.axd['phi'].plot([], 'o-c', label='Estimated')
        self.ln_x, = self.axd['x'].plot([], 'o-g', linewidth=2, label='True')
        self.ln_x_hat, = self.axd['x'].plot([], 'o-c', label='Estimated')
        self.ln_z, = self.axd['z'].plot([], 'o-g', linewidth=2, label='True')
        self.ln_z_hat, = self.axd['z'].plot([], 'o-c', label='Estimated')
        self.canvas_title = 'N/A'

        # Defined in dynamics.py for the dynamics model
        # m is the mass and J is the moment of inertia of the quadrotor 
        self.gr = 9.81 
        self.m = 0.92
        self.J = 0.0023
        # These are the X, Y, Z coordinates of the landmark
        self.landmark = (0, 5, 5)

        # This is a (N,12) where it's time, x, u, then y_obs 
        if is_noisy:
            with open('noisy_data.npy', 'rb') as f:
                self.data = np.load(f)
        else:
            with open('data.npy', 'rb') as f:
                self.data = np.load(f)

        self.dt = self.data[-1][0]/self.data.shape[0]


    def run(self):
        for i, data in enumerate(self.data):
            self.t.append(np.array(data[0]))
            self.x.append(np.array(data[1:7]))
            self.u.append(np.array(data[7:9]))
            self.y.append(np.array(data[9:12]))
            if i == 0:
                print("Initializing...")
                self.x_hat.append(self.x[-1])
            else:
                self.update(i)
        return self.x_hat

    def update(self, _):
        raise NotImplementedError

    def plot_init(self):
        self.axd['xz'].set_title(self.canvas_title)
        self.axd['xz'].set_xlabel('x (m)')
        self.axd['xz'].set_ylabel('z (m)')
        self.axd['xz'].set_aspect('equal', adjustable='box')
        self.axd['xz'].legend()
        self.axd['phi'].set_ylabel('phi (rad)')
        self.axd['phi'].set_xlabel('t (s)')
        self.axd['phi'].legend()
        self.axd['x'].set_ylabel('x (m)')
        self.axd['x'].set_xlabel('t (s)')
        self.axd['x'].legend()
        self.axd['z'].set_ylabel('z (m)')
        self.axd['z'].set_xlabel('t (s)')
        self.axd['z'].legend()
        plt.tight_layout()

    def plot_update(self, _):
        self.plot_xzline(self.ln_xz, self.x)
        self.plot_xzline(self.ln_xz_hat, self.x_hat)
        self.plot_philine(self.ln_phi, self.x)
        self.plot_philine(self.ln_phi_hat, self.x_hat)
        self.plot_xline(self.ln_x, self.x)
        self.plot_xline(self.ln_x_hat, self.x_hat)
        self.plot_zline(self.ln_z, self.x)
        self.plot_zline(self.ln_z_hat, self.x_hat)
        plt.savefig(f'{self.canvas_title}.png')

    def plot_xzline(self, ln, data):
        if len(data):
            x = [d[0] for d in data]
            z = [d[1] for d in data]
            ln.set_data(x, z)
            self.resize_lim(self.axd['xz'], x, z)

    def plot_philine(self, ln, data):
        if len(data):
            t = self.t
            phi = [d[2] for d in data]
            ln.set_data(t, phi)
            self.resize_lim(self.axd['phi'], t, phi)

    def plot_xline(self, ln, data):
        if len(data):
            t = self.t
            x = [d[0] for d in data]
            ln.set_data(t, x)
            self.resize_lim(self.axd['x'], t, x)

    def plot_zline(self, ln, data):
        if len(data):
            t = self.t
            z = [d[1] for d in data]
            ln.set_data(t, z)
            self.resize_lim(self.axd['z'], t, z)

    # noinspection PyMethodMayBeStatic
    def resize_lim(self, ax, x, y):
        xlim = ax.get_xlim()
        ax.set_xlim([min(min(x) * 1.05, xlim[0]), max(max(x) * 1.05, xlim[1])])
        ylim = ax.get_ylim()
        ax.set_ylim([min(min(y) * 1.05, ylim[0]), max(max(y) * 1.05, ylim[1])])

class OracleObserver(Estimator):
    """Oracle observer which has access to the true state.

    This class is intended as a bare minimum example for you to understand how
    to work with the code.

    Example
    ----------
    To run the oracle observer:
        $ python drone_estimator_node.py --estimator oracle_observer
    """
    def __init__(self, is_noisy=False):
        super().__init__(is_noisy)
        self.canvas_title = 'Oracle Observer'

    def update(self, _):
        self.x_hat.append(self.x[-1])


class DeadReckoning(Estimator):
    """Dead reckoning estimator.

    Your task is to implement the update method of this class using only the
    u attribute and x0. You will need to build a model of the unicycle model
    with the parameters provided to you in the lab doc. After building the
    model, use the provided inputs to estimate system state over time.

    The method should closely predict the state evolution if the system is
    free of noise. You may use this knowledge to verify your implementation.

    Example
    ----------
    To run dead reckoning:
        $ python drone_estimator_node.py --estimator dead_reckoning
    """
    def __init__(self, is_noisy=False):
        super().__init__(is_noisy)
        self.canvas_title = 'Dead Reckoning'
        
    def model(self, x, u):
        x, z, phi, vx, vz, vphi = x
        u1, u2 = u
        dx = vx
        dz = vz
        dphi = vphi
        dvx = -(u1 / self.m) * np.sin(phi)
        dvz = (u1 / self.m) * np.cos(phi) - self.gr
        dvphi = (u2 / self.J)
        return [dx, dz, dphi, dvx, dvz, dvphi]

    def update(self, _):
        if len(self.x_hat) > 0:
            # TODO: Your implementation goes here!
            # You may ONLY use self.u and self.x[0] for estimation
            
            x_hat_t = self.x_hat[-1]
            u_t = self.u[-1]
            x_hat, z_hat, phi_hat, vx_hat, vz_hat, vphi_hat = x_hat_t
            dx, dz, dphi, dvx, dvz, dvphi = self.model(x_hat_t, u_t)
            x_hat_t1 = [x_hat + dx * self.dt,
                        z_hat + dz * self.dt,
                        phi_hat + dphi * self.dt,
                        vx_hat + dvx * self.dt,
                        vz_hat + dvz * self.dt,
                        vphi_hat + dvphi * self.dt]
            self.x_hat.append(x_hat_t1)
            print(self.x_hat[-1], self.x[-1])
            

# noinspection PyPep8Naming
class ExtendedKalmanFilter(Estimator):
    """Extended Kalman filter estimator.

    Your task is to implement the update method of this class using the u
    attribute, y attribute, and x0. You will need to build a model of the
    unicycle model and linearize it at every operating point. After building the
    model, use the provided inputs and outputs to estimate system state over
    time via the recursive extended Kalman filter update rule.

    Hint: You may want to reuse your code from DeadReckoning class and
    KalmanFilter class.

    Attributes:
    ----------
        landmark : tuple
            A tuple of the coordinates of the landmark.
            landmark[0] is the x coordinate.
            landmark[1] is the y coordinate.
            landmark[2] is the z coordinate.

    Example
    ----------
    To run the extended Kalman filter:
        $ python drone_estimator_node.py --estimator extended_kalman_filter
    """
    def __init__(self, is_noisy=False):
        super().__init__(is_noisy)
        self.canvas_title = 'Extended Kalman Filter'
        self.A = None
        self.B = None
        self.C = None
        self.Q = np.eye(6) * 0.01
        self.R = np.eye(2) * 10.0
        self.P = np.eye(6) * 0.1

    # noinspection DuplicatedCode
    def update(self, i):
        if len(self.x_hat) > 0: # and self.x_hat[-1][0] < self.x[-1][0]:
            x_hat_t = self.x_hat[-1]
            u_t = self.u[-1]
            y_t = self.y[-1]
            
            x_hat_tp1_t = self.g(x_hat_t, u_t)
            A = self.approx_A(x_hat_t, u_t)
            P_tp1_t = A @ self.P @ A.T + self.Q
            C = self.approx_C(x_hat_tp1_t)
            K = P_tp1_t @ C.T @ np.linalg.inv(C @ P_tp1_t @ C.T + self.R)
            x_hat_tp1 = x_hat_tp1_t + K @ (y_t - self.h(x_hat_tp1_t, y_t))
            self.P = (np.eye(6) - K @ C) @ P_tp1_t
            x_hat_tp1 = x_hat_tp1.tolist()
            self.x_hat.append(x_hat_tp1)
            print(self.x_hat[-1], self.x[-1])
            

    def f(self, x, u):
        x, z, phi, vx, vz, vphi = x
        u1, u2 = u
        dx = vx
        dz = vz
        dphi = vphi
        dvx = -(u1 / self.m) * np.sin(phi)
        dvz = +(u1 / self.m) * np.cos(phi) - self.gr
        dvphi = (u2 / self.J)
        return [dx, dz, dphi, dvx, dvz, dvphi]

    def g(self, x, u):
        dx, dz, dphi, dvx, dvz, dvphi = self.f(x, u)
        x, z, phi, vx, vz, vphi = x
        u1, u2 = u
        return [x    + dx    * self.dt,
                z    + dz    * self.dt,
                phi  + dphi  * self.dt,
                vx   + dvx   * self.dt,
                vz   + dvz   * self.dt,
                vphi + dvphi * self.dt]

    def h(self, x, y_obs):
        x, z, phi, vx, vz, vphi = x
        landmark_x, landmark_y, landmark_z = self.landmark
        distance = np.sqrt((landmark_x - x) ** 2 + (landmark_y - 0) ** 2 + (landmark_z - z) ** 2)
        bearing = phi
        return [distance, bearing]

    def approx_A(self, x, u):
        """
        dg/dx evaluated at (x, u)
        g = x + f(x, u) * dt
        dg/dx = I + df/dx * dt
        """
        x, z, phi, vx, vz, vphi = x
        u1, u2 = u
        df_dx = np.zeros((6, 6))
        df_dx[0, 3] = 1
        df_dx[1, 4] = 1
        df_dx[2, 5] = 1
        df_dx[3, 2] = -(u1 / self.m) * np.cos(phi)
        df_dx[4, 2] = -(u1 / self.m) * np.sin(phi)
        dg_dx = np.eye(6) + df_dx * self.dt
        return dg_dx
    
    def approx_C(self, x):
        """
        dh/dx evaluated at (x)
        """
        x, z, phi, vx, vz, vphi = x
        landmark_x, landmark_y, landmark_z = self.landmark
        dh_dx = np.zeros((2, 6))
        distance = np.sqrt((landmark_x - x) ** 2 + (landmark_y - 0) ** 2 + (landmark_z - z) ** 2)
        dh_dx[0, 0] = (x - landmark_x) / distance
        dh_dx[0, 1] = (z - landmark_z) / distance
        dh_dx[1, 2] = 1
        return dh_dx
