import rospy
from std_msgs.msg import Float32MultiArray
import matplotlib.pyplot as plt
import numpy as np
plt.rcParams['font.family'] = ['FreeSans', 'Helvetica', 'Arial']
plt.rcParams['font.size'] = 14


class Estimator:
    """A base class to represent an estimator.

    This module contains the basic elements of an estimator, on which the
    subsequent DeadReckoning, Kalman Filter, and Extended Kalman Filter classes
    will be based on. A plotting function is provided to visualize the
    estimation results in real time.

    Attributes:
    ----------
        d : float
            Half of the track width (m) of TurtleBot3 Burger.
        r : float
            Wheel radius (m) of the TurtleBot3 Burger.
        u : list
            A list of system inputs, where, for the ith data point u[i],
            u[i][0] is timestamp (s),
            u[i][1] is left wheel rotational speed (rad/s), and
            u[i][2] is right wheel rotational speed (rad/s).
        x : list
            A list of system states, where, for the ith data point x[i],
            x[i][0] is timestamp (s),
            x[i][1] is bearing (rad),
            x[i][2] is translational position in x (m),
            x[i][3] is translational position in y (m),
            x[i][4] is left wheel rotational position (rad), and
            x[i][5] is right wheel rotational position (rad).
        y : list
            A list of system outputs, where, for the ith data point y[i],
            y[i][0] is timestamp (s),
            y[i][1] is translational position in x (m) when freeze_bearing:=true,
            y[i][1] is distance to the landmark (m) when freeze_bearing:=false,
            y[i][2] is translational position in y (m) when freeze_bearing:=true, and
            y[i][2] is relative bearing (rad) w.r.t. the landmark when
            freeze_bearing:=false.
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
        sub_u : rospy.Subscriber
            ROS subscriber for system inputs.
        sub_x : rospy.Subscriber
            ROS subscriber for system states.
        sub_y : rospy.Subscriber
            ROS subscriber for system outputs.
        tmr_update : rospy.Timer
            ROS Timer for periodically invoking the estimator's update method.

    Notes
    ----------
        The frozen bearing is pi/4 and the landmark is positioned at (0.5, 0.5).
    """
    # noinspection PyTypeChecker
    def __init__(self):
        self.d = 0.08
        self.r = 0.033
        self.u = []
        self.x = []
        self.y = []
        self.x_hat = []  # Your estimates go here!
        self.dt = 0.1
        self.fig, self.axd = plt.subplot_mosaic(
            [['xy', 'phi'],
             ['xy', 'x'],
             ['xy', 'y'],
             ['xy', 'thl'],
             ['xy', 'thr']], figsize=(20.0, 10.0))
        self.ln_xy, = self.axd['xy'].plot([], 'o-g', linewidth=2, label='True')
        self.ln_xy_hat, = self.axd['xy'].plot([], 'o-c', label='Estimated')
        self.ln_phi, = self.axd['phi'].plot([], 'o-g', linewidth=2, label='True')
        self.ln_phi_hat, = self.axd['phi'].plot([], 'o-c', label='Estimated')
        self.ln_x, = self.axd['x'].plot([], 'o-g', linewidth=2, label='True')
        self.ln_x_hat, = self.axd['x'].plot([], 'o-c', label='Estimated')
        self.ln_y, = self.axd['y'].plot([], 'o-g', linewidth=2, label='True')
        self.ln_y_hat, = self.axd['y'].plot([], 'o-c', label='Estimated')
        self.ln_thl, = self.axd['thl'].plot([], 'o-g', linewidth=2, label='True')
        self.ln_thl_hat, = self.axd['thl'].plot([], 'o-c', label='Estimated')
        self.ln_thr, = self.axd['thr'].plot([], 'o-g', linewidth=2, label='True')
        self.ln_thr_hat, = self.axd['thr'].plot([], 'o-c', label='Estimated')
        self.canvas_title = 'N/A'
        self.sub_u = rospy.Subscriber('u', Float32MultiArray, self.callback_u)
        self.sub_x = rospy.Subscriber('x', Float32MultiArray, self.callback_x)
        self.sub_y = rospy.Subscriber('y', Float32MultiArray, self.callback_y)
        self.tmr_update = rospy.Timer(rospy.Duration(self.dt), self.update)

    def callback_u(self, msg):
        self.u.append(msg.data)

    def callback_x(self, msg):
        self.x.append(msg.data)
        if len(self.x_hat) == 0:
            self.x_hat.append(msg.data)

    def callback_y(self, msg):
        self.y.append(msg.data)

    def update(self, _):
        raise NotImplementedError

    def plot_init(self):
        self.axd['xy'].set_title(self.canvas_title)
        self.axd['xy'].set_xlabel('x (m)')
        self.axd['xy'].set_ylabel('y (m)')
        self.axd['xy'].set_aspect('equal', adjustable='box')
        self.axd['xy'].legend()
        self.axd['phi'].set_ylabel('phi (rad)')
        self.axd['phi'].legend()
        self.axd['x'].set_ylabel('x (m)')
        self.axd['x'].legend()
        self.axd['y'].set_ylabel('y (m)')
        self.axd['y'].legend()
        self.axd['thl'].set_ylabel('theta L (rad)')
        self.axd['thl'].legend()
        self.axd['thr'].set_ylabel('theta R (rad)')
        self.axd['thr'].set_xlabel('Time (s)')
        self.axd['thr'].legend()
        plt.tight_layout()

    def plot_update(self, _):
        self.plot_xyline(self.ln_xy, self.x)
        self.plot_xyline(self.ln_xy_hat, self.x_hat)
        self.plot_philine(self.ln_phi, self.x)
        self.plot_philine(self.ln_phi_hat, self.x_hat)
        self.plot_xline(self.ln_x, self.x)
        self.plot_xline(self.ln_x_hat, self.x_hat)
        self.plot_yline(self.ln_y, self.x)
        self.plot_yline(self.ln_y_hat, self.x_hat)
        self.plot_thlline(self.ln_thl, self.x)
        self.plot_thlline(self.ln_thl_hat, self.x_hat)
        self.plot_thrline(self.ln_thr, self.x)
        self.plot_thrline(self.ln_thr_hat, self.x_hat)
        plt.savefig(f'{self.canvas_title}.png')

    def plot_xyline(self, ln, data):
        if len(data):
            x = [d[2] for d in data]
            y = [d[3] for d in data]
            ln.set_data(x, y)
            self.resize_lim(self.axd['xy'], x, y)

    def plot_philine(self, ln, data):
        if len(data):
            t = [d[0] for d in data]
            phi = [d[1] for d in data]
            ln.set_data(t, phi)
            self.resize_lim(self.axd['phi'], t, phi)

    def plot_xline(self, ln, data):
        if len(data):
            t = [d[0] for d in data]
            x = [d[2] for d in data]
            ln.set_data(t, x)
            self.resize_lim(self.axd['x'], t, x)

    def plot_yline(self, ln, data):
        if len(data):
            t = [d[0] for d in data]
            y = [d[3] for d in data]
            ln.set_data(t, y)
            self.resize_lim(self.axd['y'], t, y)

    def plot_thlline(self, ln, data):
        if len(data):
            t = [d[0] for d in data]
            thl = [d[4] for d in data]
            ln.set_data(t, thl)
            self.resize_lim(self.axd['thl'], t, thl)

    def plot_thrline(self, ln, data):
        if len(data):
            t = [d[0] for d in data]
            thr = [d[5] for d in data]
            ln.set_data(t, thr)
            self.resize_lim(self.axd['thr'], t, thr)

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
        $ roslaunch proj3_pkg unicycle_bringup.launch \
            estimator_type:=oracle_observer \
            noise_injection:=true \
            freeze_bearing:=false
    """
    def __init__(self):
        super().__init__()
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
        $ roslaunch proj3_pkg unicycle_bringup.launch \
            estimator_type:=dead_reckoning \
            noise_injection:=true \
            freeze_bearing:=false
    For debugging, you can simulate a noise-free unicycle model by setting
    noise_injection:=false.
    """
    def __init__(self):
        super().__init__()
        self.canvas_title = 'Dead Reckoning'

    def model(self, x, u):
        _, phi, x, y, thl, thr = x
        _, u_L, u_R = u
        dphi = (u_R - u_L) * self.r / (2 * self.d)
        dx = (u_R + u_L) * (self.r / 2) * np.cos(phi)
        dy = (u_R + u_L) * (self.r / 2) * np.sin(phi)
        dthl = u_L
        dthr = u_R
        return [dphi, dx, dy, dthl, dthr]

    def update(self, _):
        if len(self.x_hat) > 0 and self.x_hat[-1][0] < self.x[-1][0]:
            x_hat_t = self.x_hat[-1]
            u_t = self.u[-1]
            dphi, dx, dy, dthl, dthr = self.model(x_hat_t, u_t)
            x_tp1 = [x_hat_t[0] + self.dt,
                     x_hat_t[1] + dphi * self.dt,
                     x_hat_t[2] + dx * self.dt,
                     x_hat_t[3] + dy * self.dt,
                     x_hat_t[4] + dthl * self.dt,
                     x_hat_t[5] + dthr * self.dt]
            self.x_hat.append(x_tp1)
            print(self.x_hat[-1], self.x[-1])


class KalmanFilter(Estimator):
    """Kalman filter estimator.

    Your task is to implement the update method of this class using the u
    attribute, y attribute, and x0. You will need to build a model of the
    linear unicycle model at the default bearing of pi/4. After building the
    model, use the provided inputs and outputs to estimate system state over
    time via the recursive Kalman filter update rule.

    Attributes:
    ----------
        phid : float
            Default bearing of the turtlebot fixed at pi / 4.

    Example
    ----------
    To run the Kalman filter:
        $ roslaunch proj3_pkg unicycle_bringup.launch \
            estimator_type:=kalman_filter \
            noise_injection:=true \
            freeze_bearing:=true
    """
    def __init__(self):
        super().__init__()
        self.canvas_title = 'Kalman Filter'
        self.phid = np.pi / 4
        self.A = np.eye(4)
        self.B = np.array([[(self.r/2) * np.cos(self.phid), (self.r/2) * np.cos(self.phid)],
                           [(self.r/2) * np.sin(self.phid), (self.r/2) * np.sin(self.phid)],
                           [1, 0],
                           [0, 1]]) * self.dt
        self.C = np.array([[1, 0, 0, 0],
                           [0, 1, 0, 0]])
        self.Q = np.eye(4) * 100.0
        self.R = np.eye(2)
        self.P = np.eye(4)

    # noinspection DuplicatedCode
    # noinspection PyPep8Naming
    def update(self, _):
        if len(self.x_hat) > 0 and self.x_hat[-1][0] < self.x[-1][0]:
            x_t = self.x_hat[-1]
            u_t = self.u[-1]
            y_t = self.y[-1]
            
            x_hat_tp1_t = np.dot(self.A, x_t[2:]) + np.dot(self.B, u_t[1:])
            P_tp1_t = self.A @ self.P @ self.A.T + self.Q
            K = P_tp1_t @ self.C.T @ np.linalg.inv(self.C @ P_tp1_t @ self.C.T + self.R)
            x_hat_tp1 = x_hat_tp1_t + K @ (np.array(y_t[1:]) - self.C @ x_hat_tp1_t)
            self.P = (np.eye(4) - K @ self.C) @ P_tp1_t
            x_hat_tp1 = [self.x_hat[-1][0] + self.dt, self.phid, x_hat_tp1[0], x_hat_tp1[1], x_hat_tp1[2], x_hat_tp1[3]]
            self.x_hat.append(x_hat_tp1)
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

    Example
    ----------
    To run the extended Kalman filter:
        $ roslaunch proj3_pkg unicycle_bringup.launch \
            estimator_type:=extended_kalman_filter \
            noise_injection:=true \
            freeze_bearing:=false
    """
    def __init__(self):
        super().__init__()
        self.canvas_title = 'Extended Kalman Filter'
        self.A = None
        self.B = None
        self.C = np.array([[0, 1, 0, 0, 0],
                           [0, 0, 1, 0, 0]])
        self.Q = np.diag([0.01, 0.25, 0.25, 0.01, 0.01])
        self.R = np.eye(2) * 100.0
        self.P = np.diag([1.0, 0.25, 0.25, 100.0, 100.0])

    # noinspection DuplicatedCode
    def update(self, _):
        if len(self.x_hat) > 0 and self.x_hat[-1][0] < self.x[-1][0]:
            x_hat_t = self.x_hat[-1][1:]
            u_t = self.u[-1][1:]
            y_t = self.y[-1][1:]
            
            x_hat_tp1_t = self.g(x_hat_t, u_t)
            A = self.approx_A(x_hat_t, u_t)
            P_tp1_t = A @ self.P @ A.T + self.Q
            C = self.approx_C(x_hat_tp1_t)
            K = P_tp1_t @ C.T @ np.linalg.inv(C @ P_tp1_t @ C.T + self.R)
            x_hat_tp1 = x_hat_tp1_t + K @ (y_t - self.h(x_hat_tp1_t, y_t))
            self.P = (np.eye(5) - K @ C) @ P_tp1_t
            x_hat_tp1 = x_hat_tp1.tolist()
            x_hat_tp1 = [self.x_hat[-1][0] + self.dt] + x_hat_tp1
            self.x_hat.append(x_hat_tp1)
            print(self.x_hat[-1], self.x[-1], self.y[-1])
            
    def f(self, x, u):
        phi, x, y, thl, thr = x
        u1, u2 = u
        dphi = (u2 - u1) * self.r / (2 * self.d)
        dx = (u2 + u1) * (self.r / 2) * np.cos(phi)
        dy = (u2 + u1) * (self.r / 2) * np.sin(phi)
        dthl = u1
        dthr = u2
        return [dphi, dx, dy, dthl, dthr]

    def g(self, x, u):
        dphi, dx, dy, dthl, dthr = self.f(x, u)
        phi, x, y, thl, thr = x
        u1, u2 = u
        return [phi + dphi * self.dt,
                x   + dx   * self.dt,
                y   + dy   * self.dt,
                thl + dthl * self.dt,
                thr + dthr * self.dt]

    def h(self, x, y_obs):
        return self.C @ x

    def approx_A(self, x, u):
        """
        dg/dx evaluated at (x, u)
        g = x + f(x, u) * dt
        dg/dx = I + df/dx * dt
        """
        phi, x, y, thl, thr = x
        u1, u2 = u
        df_dx = np.zeros((5, 5))
        df_dx[1, 0] = -(u1 + u2) * (self.r / 2) * np.sin(phi)
        df_dx[2, 0] = +(u1 + u2) * (self.r / 2) * np.cos(phi)
        dg_dx = np.eye(5) + df_dx * self.dt
        return dg_dx
    
    def approx_C(self, x):
        """
        dh/dx evaluated at (x)
        h = Cx
        dh/dx = C
        """
        return self.C
