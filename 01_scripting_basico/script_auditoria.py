import json
import requests
from requests.auth import HTTPBasicAuth

# Deshabilitar advertencias por certificado SSL autofirmado del laboratorio
requests.packages.urllib3.disable_warnings()

# 1. Parámetros de conexión al router Cisco DevNet Sandbox
HOST = "devnetsandboxiosxec8k.cisco.com"
URL = f"https://{HOST}/restconf/data/ietf-interfaces:interfaces"

HEADERS = {
    "Accept": "application/yang-data+json",
    "Content-Type": "application/yang-data+json"
}
AUTH = HTTPBasicAuth("jonathan", "W_QyrZ19%Ox_piw2")


def auditar_interfaces():
    print(f"Conectando al dispositivo {HOST}...")

    try:
        # 2. Petición GET hacia la API RESTCONF con tiempo límite (timeout)
        response = requests.get(
            URL,
            headers=HEADERS,
            auth=AUTH,
            verify=False,
            timeout=15
        )
        response.raise_for_status()

        datos = response.json()
        interfaces = datos.get("ietf-interfaces:interfaces", {}).get("interface", [])

        # 3. Filtrar únicamente interfaces activas (enabled=True) con IP asignada
        interfaces_activas = []

        for iface in interfaces:
            habilitada = iface.get("enabled", False)
            direcciones_ipv4 = iface.get("ietf-ip:ipv4", {}).get("address", [])

            if habilitada and len(direcciones_ipv4) > 0:
                for addr in direcciones_ipv4:
                    interfaces_activas.append({
                        "nombre": iface.get("name", "N/A"),
                        "tipo": iface.get("type", "N/A"),
                        "habilitada": habilitada,
                        "ip": addr.get("ip", "N/A"),
                        "mascara": addr.get("netmask", "N/A")
                    })

        # 4. Guardar resultado estructurado en inventario_interfaces.json
        resultado_json = {
            "dispositivo": HOST,
            "total_interfaces_activas": len(interfaces_activas),
            "interfaces": interfaces_activas
        }

        with open("inventario_interfaces.json", "w", encoding="utf-8") as archivo_json:
            json.dump(resultado_json, archivo_json, indent=4, ensure_ascii=False)

        print(f"Auditoría completada. Se encontraron {len(interfaces_activas)} interfaces activas con IP.")
        print("Inventario guardado en: inventario_interfaces.json")

    # 5. Manejo de excepciones si el dispositivo no responde o falla la petición
    except requests.exceptions.ConnectTimeout:
        print(f"[ERROR] Tiempo de espera agotado: el dispositivo {HOST} no respondió.")
    except requests.exceptions.ConnectionError:
        print(f"[ERROR] No fue posible establecer conexión con {HOST}. Verifica tu red o la disponibilidad del laboratorio.")
    except requests.exceptions.HTTPError as err_http:
        print(f"[ERROR HTTP] El dispositivo rechazó la solicitud: {err_http}")
    except requests.exceptions.RequestException as err_req:
        print(f"[ERROR DE RED] Ocurrió un fallo inesperado en la petición: {err_req}")
    except Exception as err:
        print(f"[ERROR] Fallo al procesar los datos: {err}")


if __name__ == "__main__":
    auditar_interfaces()