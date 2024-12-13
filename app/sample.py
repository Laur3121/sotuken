from utils import get_local_temperature, get_remote_temperature

temperature = get_remote_temperature("192.168.0.17", "ubuntu", "ubuntu")
print(temperature)