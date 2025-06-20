import requests
import time


# ---------------------------------------------------------------------------
# API do Digital Twin e Lógica de Sequência (Tudo Num Só Script)
# ---------------------------------------------------------------------------
class DigitalTwinController:
    def __init__(self, host="localhost", port=8088):
        self.base_url = f"http://{host}:{port}"
        self.default_timeout = 5  # segundos para as requisições

        print(f"Tentando conectar ao Digital Twin em {self.base_url}...")
        if not self._ping():
            raise ConnectionError(
                f"Não foi possível conectar ao Digital Twin em {self.base_url}. Verifique se o Unity está rodando e o servidor HTTP está ativo.")
        print("Controlador do Digital Twin conectado e pronto.")

    # --- Métodos de Comunicação de Baixo Nível (Internos) ---
    def _request(self, endpoint, params=None):
        """Método privado para realizar requisições HTTP GET."""
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.get(url, params=params, timeout=self.default_timeout)
            response.raise_for_status()  # Levanta uma exceção para erros HTTP (4xx ou 5xx)
            return response.text.strip()
        except requests.exceptions.Timeout:
            print(f"ERRO (HTTP): Timeout na requisição para {url}")
            return None
        except requests.exceptions.ConnectionError:
            # Este erro é mais provável de ser capturado pelo _ping inicial
            print(f"ERRO (HTTP): Falha de conexão com {url}.")
            raise  # Re-lança para ser capturado no construtor ou pelo chamador
        except requests.exceptions.HTTPError as e:
            print(f"ERRO (HTTP): {e} ao acessar {url}")  # Nota: 'acessar' é pt-BR, pt-PT seria 'aceder'
            return None
        except requests.exceptions.RequestException as e:
            print(f"ERRO (HTTP) na requisição para {url}: {e}")
            return None

    def _set_actuator(self, name, value):
        """Comando de baixo nível para definir um atuador."""  # 'setar' é pt-BR, pt-PT seria 'definir' ou 'configurar'
        val_param = "1" if value else "0"
        params = {"name": name, "value": val_param}
        response_text = self._request("/set_actuator", params=params)
        if response_text and response_text.startswith("OK:"):
            return True
        print(f"FALHA (set_actuator): {name} para {value} -> Resposta: {response_text}")
        return False

    def _get_bit(self, name):
        """Comando de baixo nível para ler um bit (atuador ou sensor)."""
        params = {"name": name}
        endpoint_path = "/get_sensor"
        response_text = self._request(endpoint_path, params=params)
        if response_text and response_text.startswith("VALUE:"):
            try:
                val = int(response_text.split(":")[1])
                return val == 1
            except (IndexError, ValueError):
                print(
                    f"FALHA (get_bit): Erro de parse para {name} em {endpoint_path} -> Resposta: {response_text}")  # 'Parse' é inglês, poderia ser 'análise sintática'
                return None
        print(f"FALHA (get_bit): {name} em {endpoint_path} -> Resposta: {response_text}")
        return None

    def _ping(self):
        """Verifica a conexão com o servidor Unity."""
        response_text = self._request("/ping")
        return response_text == "PONG"

    # --- Comandos de Alto Nível para Atuadores ---
    def move_conveyor_left(self):
        """Inicia o movimento do conveyor para a esquerda (atuador Q1_7)."""
        return self._set_actuator("Q1_7", True)

    def wait_seconds(self, duration_seconds):
        """Espera 'duration_seconds' segundos."""
        time.sleep(duration_seconds)

# ---------------------------------------------------------------------------
# Lógica da Sequência do Utilizador / ALTERAR ESTE CÓDIGO!
# ---------------------------------------------------------------------------
def run_example_sequence(dtc):
    while True:
        # Conveyor para a Esquerda
        dtc.move_conveyor_left()
        dtc.wait_seconds(1)


# ---------------------------------------------------------------------------
# Ponto de Entrada Principal do Script
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("======================================================")
    print("   Controlador Digital Twin Workshop STR (Python)   ")
    print("======================================================")

    # Configurações
    UNITY_HOST = "localhost"
    UNITY_PORT = 8088  # Deve ser a mesma porta do PythonInterfaceServer.cs no Unity

    controller_instance = None  # Para garantir que podemos tentar parar em caso de erro

    try:
        # Cria e liga o controlador
        controller_instance = DigitalTwinController(host=UNITY_HOST, port=UNITY_PORT)

        # Executa a sequência de exemplo
        sequence_success = run_example_sequence(controller_instance)

        if sequence_success:  # Esta parte do código só será alcançada se a função run_example_sequence retornar
            print("\nPrograma principal: Sequência de exemplo executada com sucesso.")
        else:
            print("\nPrograma principal: Sequência de exemplo executada com falhas ou interrupções.")

    except ConnectionError as e:
        print(f"\nERRO CRÍTICO DE CONEXÃO: {e}")
        print(
            f"Por favor, verifique se o Unity está em Play Mode e o servidor HTTP (PythonInterfaceServer.cs) está ativo em {UNITY_HOST}:{UNITY_PORT}.")
    except Exception as e:  # Captura outras exceções
        print(f"\nERRO INESPERADO NO PROGRAMA PRINCIPAL: {e}")
        import traceback

        traceback.print_exc()  # Imprime o rastreio da pilha completo para depuração
    finally:
        # Tenta parar todos os atuadores ao finalizar, especialmente em caso de erro
        if controller_instance:
            print("\nFinalizando: Enviando comandos para parar todos os atuadores...")
            controller_instance.stop_punch()
            controller_instance.stop_conveyor()
            print("Comandos de parada enviados.")

        print("\nPrograma Python encerrado.")
