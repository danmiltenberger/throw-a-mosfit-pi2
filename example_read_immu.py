import time
from tam_immu import read_immu, update_pose, reset_pose

def run_pose_demo(rate_hz=100, print_hz=5):
    """Read the IMU, update the pose, and print it to the terminal. Ctrl+C to stop."""
    period = 1.0 / rate_hz
    print_period = 1.0 / print_hz
    next_tick = time.monotonic()
    last_print = 0.0
    print("Keep the IMU still for 2 seconds...")
    try:
        while True:
            pose = update_pose(read_immu())
            now = time.monotonic()
            if now - last_print >= print_period:
                last_print = now
                n, e, u = pose["pos_in"]
                status = "moving" if not pose["stationary"] else "still"
                print(f"N={n:+8.1f} in  E={e:+8.1f} in  Up={u:+8.1f} in | "
                      f"bearing={pose['bearing_deg']:6.1f}° | "
                      f"{'calibrating' if not pose['ready'] else status}")
            next_tick += period
            time.sleep(max(0.0, next_tick - time.monotonic()))
    except KeyboardInterrupt:
        print("\nStopped.")

if __name__ == "__main__":
    run_pose_demo()