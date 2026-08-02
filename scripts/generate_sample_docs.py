from pathlib import Path

DOCS = {
    "politica_reembolso.md": """# Política de Reembolso

Clientes têm até 30 dias corridos após a compra para solicitar reembolso.
Produtos usados fora das condições de uso normal não são elegíveis.
""",
    "sla_suporte.md": """# SLA de Suporte

O tempo máximo de primeira resposta é de 24 horas úteis.
Chamados críticos (sistema fora do ar) têm SLA de 2 horas.
""",
    "onboarding.md": """# Onboarding de Novos Clientes

O processo de onboarding leva em média 5 dias úteis.
Inclui: configuração de conta, treinamento inicial e checklist de segurança.
""",
}

def main():
    out_dir = Path("data/documents")
    out_dir.mkdir(parents=True, exist_ok=True)
    for filename, content in DOCS.items():
        (out_dir / filename).write_text(content, encoding="utf-8")
        print(f"criado: {filename}")

if __name__ == "__main__":
    main()