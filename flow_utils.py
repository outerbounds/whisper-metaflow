from functools import wraps
import os

def remote_compute_config(remote_dec, flag):

    @wraps(remote_dec)
    def decorator(function):

        if flag:

            if os.getenv('IS_GPU', '0') == '1':
                _remote_config = remote_dec(
                    gpu = 1, cpu = 4,
                    memory = int(os.getenv('MEMORY_REQUIRED', '10000')), 
                    image = os.getenv('GPU_IMAGE', 'eddieob/whisper-gpu:latest'),
                    queue = os.getenv('BATCH_QUEUE_GPU')
                )
            else:
                _remote_config = remote_dec(
                    cpu = 4, 
                    memory = int(os.getenv('MEMORY_REQUIRED', '10000')),
                    image = os.getenv('CPU_IMAGE', 'eddieob/whisper:latest'),
                    queue = os.getenv('BATCH_QUEUE_CPU')
                )

            return _remote_config(function)
        return function
    return decorator