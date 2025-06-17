import ollama
import time
import datetime


# Definir o prompt padrão para os testes
PROMPT = "Qual é a capital da França?"

# Nome do arquivo de relatório
REPORT_FILE = f"relatorio_benchmark_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"


def listar_modelos():
    """
    Lista todos os modelos disponíveis no Ollama local.
    """
    modelos = ollama.list().get("models", [])
    return [m["model"] for m in modelos]


def testar_modelo(modelo, prompt):
    """
    Executa o prompt no modelo e retorna o tempo e resposta.
    """
    try:
        inicio = time.time()

        resposta = ollama.chat(
            model=modelo,
            messages=[{"role": "user", "content": prompt}],
            stream=False
        )

        fim = time.time()
        tempo = round(fim - inicio, 2)
        return {
            "modelo": modelo,
            "tempo": tempo,
            "resposta": resposta["message"]["content"],
            "status": "Sucesso"
        }

    except Exception as e:
        return {
            "modelo": modelo,
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
        f.write(f"Data: {datetime.datetime.now()}\n\n")

        for r in resultados:
            f.write(f"Modelo: {r['modelo']}\n")
            f.write(f"Status: {r['status']}\n")
            if r["tempo"]:
                f.write(f"Tempo de resposta: {r['tempo']} segundos\n")
            if r["resposta"]:
                f.write(f"Resposta: {r['resposta']}\n")
            f.write("-" * 50 + "\n")

    print(f"✅ Relatório salvo em: {arquivo}")


def main():
    print("🚀 Iniciando benchmark de modelos no Ollama...")
    modelos = listar_modelos()

    print(f"🔍 Modelos encontrados: {modelos}")
    resultados = []

    for modelo in modelos:
        print(f"\n▶️ Testando modelo: {modelo}")
        resultado = testar_modelo(modelo, PROMPT)
        if resultado["status"] == "Sucesso":
            print(f"✔️ {modelo} respondeu em {resultado['tempo']} segundos")
        else:
            print(f"❌ {modelo} falhou: {resultado['status']}")
        resultados.append(resultado)

    gerar_relatorio(resultados, REPORT_FILE)


if __name__ == "__main__":
    main()
