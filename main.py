import subprocess
import requests
import time
import yaml

def load_config():
    try:
        with open("config.yml", "r") as file:
            config = yaml.safe_load(file)
        return config
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier de configuration : {e}")
        return None

def get_current_block_height(url):
    try:
        response = requests.get(f"{url}/status")
        status = response.json()
        return status.get("result", {}).get("sync_info", {}).get("latest_block_height", -1)
    except Exception as e:
        print(f"Erreur lors de la récupération de la hauteur de bloc actuelle : {e}")
        return -1

def log(message, log_file):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    with open(log_file, "a") as log:
        log.write(f"{timestamp} - {message}\n")

def watch_block_until_height():
    config = load_config()

    if config is None:
        log("Erreur lors de la lecture du fichier de configuration.", "program_log.log")
        return

    target_height = config.get("target_height", 0)
    source_directory = config.get("source_directory", "")
    branch_name = config.get("branch_name", "")
    service_name = config.get("service_name", "")
    log_file = config.get("log_file", "program_log.log")

    url = "http://localhost:26657"  # Remplacez ceci par l'URL correcte de votre validateur RPC
    event_type = "NewBlock"

    log("Début du programme.", log_file)

    while True:
        try:
            current_block_height = get_current_block_height(url)
            log(f"Hauteur de bloc actuelle : {current_block_height}, Hauteur de bloc cible : {target_height}", log_file)

            response = requests.get(f"{url}/subscribe?query='tm.event='{event_type}")
            event = response.json()

            if "block" in event and event["block"]["header"]["height"] >= target_height:
                # Exécutez le script bash pour mettre à jour le binaire
                process = subprocess.run(["git", "-C", source_directory, "pull"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                log(f"Sortie de 'git pull':\n{process.stdout}\n", log_file)
                log(f"Erreurs de 'git pull':\n{process.stderr}\n", log_file)

                process = subprocess.run(["git", "-C", source_directory, "checkout", branch_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                log(f"Sortie de 'git checkout':\n{process.stdout}\n", log_file)
                log(f"Erreurs de 'git checkout':\n{process.stderr}\n", log_file)

                process = subprocess.run(["make", "-C", source_directory, "install"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                log(f"Sortie de 'make install':\n{process.stdout}\n", log_file)
                log(f"Erreurs de 'make install':\n{process.stderr}\n", log_file)

                # Écrivez un log indiquant que la hauteur cible a été atteinte
                log(f"Hauteur cible {target_height} atteinte à {time.strftime('%Y-%m-%d %H:%M:%S')}", log_file)

                # Redémarrez le service avec systemctl
                process = subprocess.run(["sudo", "systemctl", "restart", service_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                log(f"Sortie de 'sudo systemctl restart {service_name}':\n{process.stdout}\n", log_file)
                log(f"Erreurs de 'sudo systemctl restart {service_name}':\n{process.stderr}\n", log_file)

                log(f"Service {service_name} redémarré avec succès!", log_file)

                break  # Sortez de la boucle une fois que la hauteur cible est atteinte
        except Exception as e:
            # Écrivez les erreurs dans le fichier de logs
            log(f"Erreur non liée aux commandes subprocess : {e}", log_file)

        # Ajoutez une petite pause pour éviter une utilisation excessive des ressources
        time.sleep(1)

    log("Fin du programme.", log_file)

if __name__ == "__main__":
    watch_block_until_height()
