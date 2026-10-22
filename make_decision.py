import time


def decide(this_camera_frame, list_of_previous_field_states) -> str:
    '''
    from the most recent camera frame and an understanding of the field state, decide what the robot should do next.
    Then send this decision to the arduino. Only run intensive processes every n seconds or milliseconds
    '''


    return "Working on it!"





def example_time():
    # 1. Record the starting point in seconds
    start_time = time.perf_counter() 
    
    # ... your function's code runs here ...
    time.sleep(0.5) # Simulating a 500ms delay
    
    # 2. Calculate the difference and convert to milliseconds
    elapsed_ms = (time.perf_counter() - start_time) * 1000
    
    print(f"Elapsed time: {elapsed_ms:.2f} ms")

example_time()