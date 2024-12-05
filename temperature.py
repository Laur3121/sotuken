# temperature.py
import paramiko

def get_temperature_via_ssh(worker_ip, username="ubuntu", password="ubuntu"):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(worker_ip, username=username, password=password)
    
    stdin, stdout, stderr = ssh.exec_command("vcgencmd measure_temp")
    temp_output = stdout.read().decode().strip()
    
    ssh.close()
    
    temperature = float(temp_output.replace("temp=", "").replace("'C", ""))
    return temperature
