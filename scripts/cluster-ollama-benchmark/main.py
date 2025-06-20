import ollama
import time
import datetime
import yaml
import os


# 🗂️ Carregar configuração do arquivo YAML
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

MEMORY_LIMIT_MB = config.get('memory_threshold_mb', 3500)
PROMPT = config.get('task_prompt', 'Qual é a capital da França?')
CPU_INTERVAL = config.get('cpu_sample_interval', 0.2)
OUTPUT_FOLDER = config.get('output_folder', 'reports')

# 📂 Criar a pasta de saída se não existir
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# 📄 Nome do arquivo de relatório
REPORT_FILE = os.path.join(
    OUTPUT_FOLDER,
    f"relatorio_benchmark_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
)


def listar_modelos():
    """
    Lista todos os modelos disponíveis no Ollama local.
    """
    modelos = ollama.list().models
    return modelos


def testar_modelo(modelo, prompt):
    """
    Executa o prompt no modelo e retorna o tempo e resposta.
    """
    try:
        inicio = time.time()

        resposta = ollama.chat(
            model=modelo.model,
            messages=[{"role": "user", "content": prompt}],
            stream=False
        )

        fim = time.time()
        tempo = round(fim - inicio, 2)

        return {
            "modelo": modelo.model,
            "tempo": tempo,
            "resposta": resposta["message"]["content"],
            "status": "Sucesso"
        }

    except Exception as e:
        return {
            "modelo": modelo.model,
            "tempo": None,
            "resposta": None,
            "status": f"Erro: {str(e)}"
        }


def gerar_relatorio(resultados, arquivo):
    """
    Gera um relatório TXT com os resultados.
    """
    with open(arquivo, "w") as f:
        f.write("=== Relatório de Benchmark Ollama ===\n")
        f.write(f"Data: {datetime.datetime.now()}\n")
        f.write(f"Prompt usado: {PROMPT}\n")
        f.write(f"Limite de Memória: {MEMORY_LIMIT_MB} MB\n")
        f.write(f"Intervalo de Amostragem CPU: {CPU_INTERVAL} segundos\n\n")

        for r in resultados:
            f.write(f"Modelo: {r['modelo']}\n")
            f.write(f"Status: {r['status']}\n")
            if r["tempo"]:
                f.write(f"Tempo de resposta: {r['tempo']} segundos\n")
            if r["resposta"]:
                f.write(f"Resposta: {r['resposta']}\n")
            f.write("-" * 60 + "\n")

    print(f"✅ Relatório salvo em: {arquivo}")


def main():
    print(f"🚀 Iniciando benchmark com limite de memória {MEMORY_LIMIT_MB} MB")
    print(f"🧠 Prompt usado: {PROMPT}")
    print(f"📂 Relatórios serão salvos em: {OUTPUT_FOLDER}")

    modelos = listar_modelos()

    resultados = []

    for modelo in modelos:
        tamanho_mb = modelo.size / (1024 * 1024)
        if tamanho_mb > MEMORY_LIMIT_MB:
            print(f"⚠️ Pulando {modelo.model} - {round(tamanho_mb, 2)} MB (excede limite)")
            continue

        print(f"\n▶️ Testando modelo: {modelo.model} ({round(tamanho_mb, 2)} MB)")
        resultado = testar_modelo(modelo, PROMPT)

        if resultado["status"] == "Sucesso":
            print(f"✔️ {modelo.model} respondeu em {resultado['tempo']} segundos")
        else:
            print(f"❌ {modelo.model} falhou: {resultado['status']}")

        resultados.append(resultado)

    gerar_relatorio(resultados, REPORT_FILE)


if __name__ == "__main__":
    main()
