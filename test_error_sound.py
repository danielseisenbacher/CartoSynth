import sys
import time

def on_crash_beep(exc_type, exc_value, exc_traceback):
    # Print the normal traceback first
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

    # Ring terminal bell 3 times
    print("\n\033[91m[FAILED] Test error triggered! Ringing alert...\033[0m", file=sys.stderr)
    for _ in range(3):
        sys.stderr.write('\a')
        sys.stderr.flush()
        time.sleep(0.4)

sys.excepthook = on_crash_beep

if __name__ == "__main__":
    print("Testing terminal bell hook... raising an error in 1 second.")
    time.sleep(1)
    raise RuntimeError("This is a simulated failure to test the error noise!")

