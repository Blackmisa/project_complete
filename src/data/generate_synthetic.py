"""Geração de dados sintéticos para o Datathon.

Cria três artefatos a partir de uma empresa fictícia ("AmazoniaShop", e-commerce):
  - data/raw/tickets.csv         : 500 tickets de atendimento (com PII proposital)
  - data/raw/knowledge_base.json : 30 documentos de FAQ/políticas (para RAG)
  - data/golden_set/golden.json  : 25 pares (query, resposta esperada, contextos)

Os dados são determinísticos via seed para garantir reprodutibilidade
(critério de aceite da Etapa 1: "Pipeline versionado e reprodutível").
"""

from __future__ import annotations

import json
import logging
import random
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path

from faker import Faker

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Reprodutibilidade: seed fixa em todas as fontes de aleatoriedade
SEED = 42
random.seed(SEED)
fake = Faker("pt_BR")
Faker.seed(SEED)

ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = ROOT / "data" / "raw"
DATA_GOLDEN = ROOT / "data" / "golden_set"

# ---------------------------------------------------------------------------
# Domínio: AmazoniaShop, e-commerce fictício de produtos regionais
# ---------------------------------------------------------------------------

CATEGORIES = [
    "pedido_nao_chegou",
    "produto_defeito",
    "reembolso",
    "duvida_produto",
    "pagamento_falhou",
    "cancelamento",
    "troca",
    "elogio",
]

PRIORITIES = ["baixa", "media", "alta", "critica"]
PRIORITY_WEIGHTS = [0.4, 0.35, 0.2, 0.05]

CHANNELS = ["chat", "email", "telefone", "redes_sociais", "whatsapp"]
STATUSES = ["aberto", "em_andamento", "resolvido", "escalado", "cancelado"]

# Templates de mensagens por categoria — incluem PII intencional para testar Presidio
MESSAGE_TEMPLATES = {
    "pedido_nao_chegou": [
        "Meu pedido {order_id} não chegou. Já se passaram {days} dias da data prevista. Meu CPF é {cpf}.",
        "Olá, sou {name}, pedido {order_id} continua como 'a caminho' há {days} dias. Email: {email}",
        "Comprei dia {date} e nada do produto. Pedido: {order_id}. Telefone: {phone}",
    ],
    "produto_defeito": [
        "Recebi o produto do pedido {order_id} e ele veio com defeito. Quebrado na embalagem.",
        "O item chegou hoje mas não funciona. Pedido {order_id}, comprei como presente.",
        "Produto do pedido {order_id} apresentou defeito após {days} dias de uso. Quero troca.",
    ],
    "reembolso": [
        "Quero meu dinheiro de volta do pedido {order_id}. Já cancelei e nada do estorno.",
        "Solicitei reembolso há {days} dias do pedido {order_id} e nada. CPF: {cpf}",
        "Por favor processem meu reembolso. Pedido {order_id}, valor R$ {value}.",
    ],
    "duvida_produto": [
        "Vocês têm esse produto na cor azul?",
        "Qual o prazo de entrega para Manaus?",
        "Esse produto tem garantia? Por quanto tempo?",
        "Aceitam parcelamento sem juros?",
    ],
    "pagamento_falhou": [
        "Tentei pagar com cartão e deu erro. Pedido {order_id}.",
        "PIX não está sendo reconhecido no checkout. Já paguei mas não consta.",
        "Cartão de crédito recusado mas tenho limite. Pedido {order_id}, email {email}.",
    ],
    "cancelamento": [
        "Quero cancelar o pedido {order_id} antes que ele saia para entrega.",
        "Comprei errado, preciso cancelar o pedido {order_id} urgente.",
        "Cancelar pedido {order_id} por favor. Mudei de ideia.",
    ],
    "troca": [
        "Quero trocar o produto do pedido {order_id} por outro tamanho.",
        "Posso trocar o item do pedido {order_id}? Veio diferente do que pedi.",
        "Pedido {order_id} chegou certo mas quero outro modelo. Como faço a troca?",
    ],
    "elogio": [
        "Atendimento excelente! Pedido {order_id} chegou antes do prazo.",
        "Só quero parabenizar, produto de qualidade. Continuem assim!",
        "Recomendo demais. Pedido {order_id} foi tudo perfeito.",
    ],
}


@dataclass
class Ticket:
    ticket_id: str
    created_at: str
    customer_id: str
    customer_name: str
    customer_email: str
    channel: str
    category: str
    priority: str
    status: str
    message: str
    resolved_at: str | None
    resolution_time_hours: float | None


def _random_date(start_days_ago: int = 90) -> datetime:
    """Data aleatória nos últimos N dias."""
    delta = timedelta(
        days=random.randint(0, start_days_ago),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
    )
    return datetime.now() - delta


def _generate_message(category: str) -> str:
    """Preenche template com dados sintéticos (gera PII intencional)."""
    template = random.choice(MESSAGE_TEMPLATES[category])
    return template.format(
        order_id=f"AMZ{random.randint(10000, 99999)}",
        days=random.randint(1, 30),
        date=fake.date_this_year().strftime("%d/%m/%Y"),
        name=fake.name(),
        email=fake.email(),
        phone=fake.phone_number(),
        cpf=fake.cpf(),
        value=f"{random.uniform(50, 2000):.2f}",
    )


def generate_tickets(n: int = 500) -> list[Ticket]:
    """Gera N tickets sintéticos."""
    tickets: list[Ticket] = []
    for i in range(n):
        category = random.choice(CATEGORIES)
        priority = random.choices(PRIORITIES, weights=PRIORITY_WEIGHTS, k=1)[0]
        status = random.choice(STATUSES)
        created = _random_date()

        if status == "resolvido":
            resolved = created + timedelta(hours=random.uniform(0.5, 72))
            resolution_time = (resolved - created).total_seconds() / 3600
            resolved_str = resolved.isoformat()
        else:
            resolved_str = None
            resolution_time = None

        tickets.append(
            Ticket(
                ticket_id=f"TKT-{i + 1:06d}",
                created_at=created.isoformat(),
                customer_id=f"CUST-{random.randint(1000, 9999)}",
                customer_name=fake.name(),
                customer_email=fake.email(),
                channel=random.choice(CHANNELS),
                category=category,
                priority=priority,
                status=status,
                message=_generate_message(category),
                resolved_at=resolved_str,
                resolution_time_hours=resolution_time,
            )
        )
    return tickets


# ---------------------------------------------------------------------------
# Knowledge Base (para RAG)
# ---------------------------------------------------------------------------

KNOWLEDGE_BASE = [
    {
        "doc_id": "KB-001",
        "topic": "politica_devolucao",
        "title": "Política de devolução",
        "content": (
            "Você tem até 7 dias corridos após o recebimento do produto para solicitar "
            "devolução, conforme o Código de Defesa do Consumidor (Art. 49). "
            "Para produtos com defeito, o prazo se estende para 30 dias para itens não "
            "duráveis e 90 dias para itens duráveis. A devolução é gratuita: enviamos "
            "uma etiqueta dos Correios pelo email cadastrado."
        ),
    },
    {
        "doc_id": "KB-002",
        "topic": "rastreamento_pedido",
        "title": "Como rastrear meu pedido",
        "content": (
            "Acesse 'Meus Pedidos' no site, clique no pedido desejado e use o código de "
            "rastreio. Você também recebe atualizações automáticas por email a cada mudança "
            "de status. Pedidos para a região Norte podem levar de 7 a 15 dias úteis."
        ),
    },
    {
        "doc_id": "KB-003",
        "topic": "formas_pagamento",
        "title": "Formas de pagamento aceitas",
        "content": (
            "Aceitamos cartão de crédito (Visa, Mastercard, Elo, Amex) com parcelamento "
            "em até 12x sem juros para compras acima de R$ 200. PIX com 5% de desconto à "
            "vista. Boleto bancário com prazo de compensação de 1 a 3 dias úteis. "
            "Não aceitamos cheques."
        ),
    },
    {
        "doc_id": "KB-004",
        "topic": "cancelamento",
        "title": "Como cancelar um pedido",
        "content": (
            "O cancelamento gratuito é possível enquanto o pedido estiver em status "
            "'em separação'. Após despachado, você precisa aguardar a entrega e iniciar "
            "uma devolução. Acesse 'Meus Pedidos' > selecione o pedido > 'Cancelar'. "
            "O reembolso ocorre em até 7 dias úteis na forma original de pagamento."
        ),
    },
    {
        "doc_id": "KB-005",
        "topic": "prazo_entrega",
        "title": "Prazos de entrega por região",
        "content": (
            "Sudeste e Sul: 2 a 5 dias úteis. Centro-Oeste e Nordeste: 4 a 8 dias úteis. "
            "Norte: 7 a 15 dias úteis. Capitais têm prazo reduzido. O prazo começa a "
            "contar após confirmação do pagamento, não a partir da finalização da compra."
        ),
    },
    {
        "doc_id": "KB-006",
        "topic": "troca",
        "title": "Solicitação de troca",
        "content": (
            "Trocas por tamanho, cor ou modelo são aceitas em até 30 dias do recebimento, "
            "desde que o produto esteja sem uso, com etiquetas e na embalagem original. "
            "A primeira troca é gratuita; trocas adicionais têm custo de R$ 15 de frete."
        ),
    },
    {
        "doc_id": "KB-007",
        "topic": "garantia",
        "title": "Política de garantia",
        "content": (
            "Todos os produtos vendidos pela AmazoniaShop possuem garantia legal de 90 "
            "dias. Eletrônicos e eletrodomésticos têm garantia adicional do fabricante "
            "(geralmente 12 meses). Para acionar a garantia, abra um chamado em "
            "'Atendimento' anexando nota fiscal e descrição do problema."
        ),
    },
    {
        "doc_id": "KB-008",
        "topic": "reembolso",
        "title": "Prazos de reembolso",
        "content": (
            "Reembolso via PIX: até 2 dias úteis. Cartão de crédito: até 2 faturas, "
            "conforme prazo da operadora. Boleto: até 10 dias úteis para o cliente "
            "informar dados bancários. Não realizamos reembolso em outra forma de "
            "pagamento que não seja a original da compra."
        ),
    },
    {
        "doc_id": "KB-009",
        "topic": "frete_gratis",
        "title": "Frete grátis e regiões atendidas",
        "content": (
            "Frete grátis para compras acima de R$ 199 nas regiões Sul, Sudeste, "
            "Centro-Oeste e capitais do Nordeste. Para a região Norte, frete grátis a "
            "partir de R$ 299. Não atendemos zonas rurais sem CEP cadastrado nos Correios."
        ),
    },
    {
        "doc_id": "KB-010",
        "topic": "produto_defeituoso",
        "title": "Produto chegou com defeito",
        "content": (
            "Se o produto chegou com defeito, abra um chamado em até 7 dias do "
            "recebimento. Anexe fotos ou vídeo do defeito. Você pode escolher: troca "
            "pelo mesmo produto, troca por outro de valor equivalente, ou reembolso "
            "integral. O frete reverso é por nossa conta."
        ),
    },
    {
        "doc_id": "KB-011",
        "topic": "pagamento_falhou",
        "title": "Meu pagamento foi recusado",
        "content": (
            "Pagamento recusado pode ter várias causas: dados incorretos do cartão, "
            "limite insuficiente, antifraude do banco, ou problema temporário. Tente "
            "novamente em alguns minutos, verifique os dados, ou entre em contato com "
            "seu banco. Se o problema persistir, use PIX como alternativa."
        ),
    },
    {
        "doc_id": "KB-012",
        "topic": "cadastro",
        "title": "Como criar conta",
        "content": (
            "Para criar conta, clique em 'Entrar' > 'Cadastrar'. Informe nome, CPF, "
            "email e senha. Você receberá um email de confirmação. Sem conta, é possível "
            "comprar como visitante, mas você não terá acesso a histórico nem trocas online."
        ),
    },
    {
        "doc_id": "KB-013",
        "topic": "esqueci_senha",
        "title": "Esqueci minha senha",
        "content": (
            "Na tela de login, clique em 'Esqueci minha senha'. Informe o email "
            "cadastrado e você receberá um link para redefinição em até 5 minutos. "
            "O link expira em 1 hora. Verifique a pasta de spam se não receber."
        ),
    },
    {
        "doc_id": "KB-014",
        "topic": "atendimento_horario",
        "title": "Horário de atendimento",
        "content": (
            "Chat e WhatsApp: segunda a sábado, 8h às 22h. Telefone (0800-AMAZONIA): "
            "segunda a sexta, 9h às 18h. Email: 24h, com resposta em até 24 horas úteis. "
            "Domingos e feriados nacionais: apenas autoatendimento via site."
        ),
    },
    {
        "doc_id": "KB-015",
        "topic": "nota_fiscal",
        "title": "Segunda via de nota fiscal",
        "content": (
            "A nota fiscal é enviada por email logo após o despacho do pedido. Para "
            "segunda via, acesse 'Meus Pedidos' > 'Detalhes' > 'Baixar NF-e'. Notas de "
            "pedidos com mais de 5 anos não ficam disponíveis pelo site; entre em contato."
        ),
    },
    {
        "doc_id": "KB-016",
        "topic": "produto_indisponivel",
        "title": "Produto fora de estoque",
        "content": (
            "Se um produto está marcado como 'indisponível', clique em 'Avise-me quando "
            "chegar' para receber email assim que voltar ao estoque. Não fazemos reservas "
            "nem aceitamos pré-pagamento de itens fora de estoque."
        ),
    },
    {
        "doc_id": "KB-017",
        "topic": "endereco_entrega",
        "title": "Alterar endereço de entrega",
        "content": (
            "O endereço pode ser alterado enquanto o pedido estiver em status 'aguardando "
            "pagamento' ou 'em separação'. Após despachado, não é possível mudar o destino "
            "— a transportadora segue o endereço original. Em caso de erro, abra um chamado "
            "imediato para tentar interceptar."
        ),
    },
    {
        "doc_id": "KB-018",
        "topic": "cupom_desconto",
        "title": "Como usar cupom de desconto",
        "content": (
            "No checkout, antes de finalizar o pagamento, há um campo 'Cupom de desconto'. "
            "Insira o código exatamente como recebido (sensível a maiúsculas) e clique em "
            "'Aplicar'. Cupons não são acumulativos. Cupons de primeira compra exigem "
            "conta nova sem histórico de pedidos."
        ),
    },
    {
        "doc_id": "KB-019",
        "topic": "produto_diferente",
        "title": "Recebi produto diferente do pedido",
        "content": (
            "Caso tenha recebido um produto diferente do que pediu, abra um chamado em "
            "até 48 horas com fotos da etiqueta de envio e do produto recebido. "
            "Enviaremos o item correto sem custo adicional e o produto errado é coletado "
            "no mesmo dia da entrega do correto."
        ),
    },
    {
        "doc_id": "KB-020",
        "topic": "lgpd_dados",
        "title": "Como solicitar meus dados (LGPD)",
        "content": (
            "Conforme a Lei Geral de Proteção de Dados (LGPD), você pode solicitar "
            "acesso, correção, portabilidade ou exclusão dos seus dados pessoais. Envie "
            "email para dpo@amazoniashop.com.br informando CPF e o tipo de solicitação. "
            "Atendemos em até 15 dias úteis."
        ),
    },
    {
        "doc_id": "KB-021",
        "topic": "compra_atacado",
        "title": "Compras corporativas / atacado",
        "content": (
            "Para compras acima de 50 unidades do mesmo item, há condições especiais "
            "de preço e prazo. Envie email para corporativo@amazoniashop.com.br "
            "informando CNPJ, produto e quantidade. Retorno em até 2 dias úteis com "
            "proposta personalizada."
        ),
    },
    {
        "doc_id": "KB-022",
        "topic": "produto_avariado_transporte",
        "title": "Produto chegou avariado pelo transporte",
        "content": (
            "Se a embalagem chegou claramente danificada, recuse a entrega na hora. "
            "Se você só percebeu o problema após abrir, abra chamado em 7 dias com "
            "fotos da embalagem e do produto. Tratamos como defeito e você escolhe "
            "entre troca, reembolso ou crédito na loja."
        ),
    },
    {
        "doc_id": "KB-023",
        "topic": "fidelidade",
        "title": "Programa de fidelidade",
        "content": (
            "Cada R$ 1 gasto vale 1 ponto. A cada 1.000 pontos você ganha R$ 50 em "
            "crédito para próximas compras. Pontos expiram em 12 meses. Acompanhe seu "
            "saldo em 'Minha Conta' > 'Fidelidade'. Não há taxa de adesão."
        ),
    },
    {
        "doc_id": "KB-024",
        "topic": "marketplace",
        "title": "Diferença entre vendido e entregue por AmazoniaShop",
        "content": (
            "Itens 'vendidos e entregues por AmazoniaShop' têm nossa garantia de "
            "atendimento integral. Itens 'vendidos por terceiros' são de parceiros "
            "do marketplace, com política própria — exibida na página do produto. "
            "Trocas e devoluções de marketplace passam pelo lojista parceiro."
        ),
    },
    {
        "doc_id": "KB-025",
        "topic": "compra_internacional",
        "title": "Compras internacionais e impostos",
        "content": (
            "Não vendemos para fora do Brasil. Para itens importados disponíveis no "
            "site, todos os impostos já estão inclusos no preço final exibido — você "
            "não paga taxa adicional na entrega. Itens importados podem ter prazo "
            "estendido em 5 a 10 dias."
        ),
    },
    {
        "doc_id": "KB-026",
        "topic": "comprovante_pagamento",
        "title": "Onde acho o comprovante de pagamento",
        "content": (
            "Comprovantes de pagamento ficam em 'Meus Pedidos' > selecione o pedido > "
            "'Pagamento' > 'Baixar comprovante'. Para PIX, é gerado automaticamente após "
            "a compensação. Para cartão, exibimos o número de autorização da operadora."
        ),
    },
    {
        "doc_id": "KB-027",
        "topic": "loja_fisica",
        "title": "Endereços de lojas físicas",
        "content": (
            "Não temos lojas físicas. Somos uma operação 100% online, com centros de "
            "distribuição em São Paulo (SP), Manaus (AM) e Recife (PE). Não é possível "
            "retirar pedidos pessoalmente nesses centros."
        ),
    },
    {
        "doc_id": "KB-028",
        "topic": "denuncia_fraude",
        "title": "Suspeita de fraude ou cobrança indevida",
        "content": (
            "Em caso de cobrança não reconhecida, entre em contato imediatamente pelo "
            "telefone 0800-AMAZONIA. Bloqueamos o acesso da conta enquanto investigamos. "
            "Se houve uso indevido do seu cartão, contate seu banco também — eles "
            "iniciam o processo de chargeback."
        ),
    },
    {
        "doc_id": "KB-029",
        "topic": "produto_descontinuado",
        "title": "Produto descontinuado",
        "content": (
            "Produtos descontinuados não voltam ao estoque. Se você possui um item "
            "descontinuado e precisa de reposição de peça ou acessório, sugerimos "
            "buscar diretamente com o fabricante. Nosso atendimento pode indicar "
            "produtos similares ainda disponíveis."
        ),
    },
    {
        "doc_id": "KB-030",
        "topic": "embalagem_presente",
        "title": "Embalagem para presente",
        "content": (
            "Oferecemos embalagem para presente por R$ 9,90 por item, com opção de "
            "incluir cartão personalizado de até 200 caracteres. O preço do produto "
            "não aparece em nenhum documento dentro da embalagem. Selecione a opção "
            "no checkout antes de finalizar a compra."
        ),
    },
]


# ---------------------------------------------------------------------------
# Golden Set — pares (query, resposta esperada, contextos relevantes)
# Usado por RAGAS na Etapa 3
# ---------------------------------------------------------------------------

GOLDEN_SET = [
    {
        "query": "Qual o prazo para devolver um produto?",
        "expected_answer": (
            "7 dias corridos após o recebimento, conforme o Art. 49 do CDC. "
            "Para produtos com defeito, 30 dias (não duráveis) ou 90 dias (duráveis)."
        ),
        "expected_doc_ids": ["KB-001"],
    },
    {
        "query": "Como faço para rastrear meu pedido?",
        "expected_answer": (
            "Acesse 'Meus Pedidos' no site e use o código de rastreio. Atualizações "
            "também são enviadas automaticamente por email."
        ),
        "expected_doc_ids": ["KB-002"],
    },
    {
        "query": "Vocês aceitam PIX?",
        "expected_answer": "Sim, aceitamos PIX com 5% de desconto à vista.",
        "expected_doc_ids": ["KB-003"],
    },
    {
        "query": "Posso parcelar minha compra?",
        "expected_answer": (
            "Sim, em até 12x sem juros para compras acima de R$ 200, no cartão de crédito."
        ),
        "expected_doc_ids": ["KB-003"],
    },
    {
        "query": "Como cancelo um pedido?",
        "expected_answer": (
            "Em 'Meus Pedidos', selecione o pedido e clique em 'Cancelar'. "
            "Cancelamento gratuito só enquanto o pedido estiver em separação."
        ),
        "expected_doc_ids": ["KB-004"],
    },
    {
        "query": "Quanto tempo demora pra entregar em Manaus?",
        "expected_answer": "Para a região Norte, o prazo é de 7 a 15 dias úteis.",
        "expected_doc_ids": ["KB-005"],
    },
    {
        "query": "Posso trocar por outro tamanho?",
        "expected_answer": (
            "Sim, em até 30 dias do recebimento, com produto sem uso e na embalagem "
            "original. A primeira troca é gratuita."
        ),
        "expected_doc_ids": ["KB-006"],
    },
    {
        "query": "Qual a garantia dos produtos?",
        "expected_answer": (
            "Garantia legal de 90 dias para todos os produtos, mais a garantia adicional "
            "do fabricante (geralmente 12 meses para eletrônicos)."
        ),
        "expected_doc_ids": ["KB-007"],
    },
    {
        "query": "Quanto tempo leva o reembolso?",
        "expected_answer": (
            "PIX: até 2 dias úteis. Cartão de crédito: até 2 faturas. Boleto: até 10 "
            "dias úteis após informar dados bancários."
        ),
        "expected_doc_ids": ["KB-008"],
    },
    {
        "query": "A partir de quanto tem frete grátis?",
        "expected_answer": (
            "R$ 199 para Sul, Sudeste, Centro-Oeste e capitais do Nordeste. "
            "R$ 299 para a região Norte."
        ),
        "expected_doc_ids": ["KB-009"],
    },
    {
        "query": "Recebi um produto com defeito, o que fazer?",
        "expected_answer": (
            "Abra um chamado em até 7 dias com fotos. Você pode escolher entre troca, "
            "produto equivalente ou reembolso integral. O frete reverso é grátis."
        ),
        "expected_doc_ids": ["KB-010"],
    },
    {
        "query": "Meu cartão foi recusado, e agora?",
        "expected_answer": (
            "Verifique os dados, tente novamente ou contate seu banco. Você também pode "
            "usar PIX como alternativa."
        ),
        "expected_doc_ids": ["KB-011"],
    },
    {
        "query": "Esqueci minha senha, como recupero?",
        "expected_answer": (
            "Na tela de login, clique em 'Esqueci minha senha' e informe o email. "
            "Você receberá um link em até 5 minutos (verifique também o spam)."
        ),
        "expected_doc_ids": ["KB-013"],
    },
    {
        "query": "Qual o horário de atendimento?",
        "expected_answer": (
            "Chat e WhatsApp: seg-sáb 8h-22h. Telefone: seg-sex 9h-18h. Email: 24h "
            "com resposta em até 24 horas úteis."
        ),
        "expected_doc_ids": ["KB-014"],
    },
    {
        "query": "Como pego a segunda via da nota fiscal?",
        "expected_answer": "Em 'Meus Pedidos' > 'Detalhes' > 'Baixar NF-e'.",
        "expected_doc_ids": ["KB-015"],
    },
    {
        "query": "Posso mudar o endereço de entrega depois de comprar?",
        "expected_answer": (
            "Sim, enquanto o pedido estiver em 'aguardando pagamento' ou 'em separação'. "
            "Após despachado, não é possível alterar."
        ),
        "expected_doc_ids": ["KB-017"],
    },
    {
        "query": "Como faço para usar um cupom de desconto?",
        "expected_answer": (
            "No checkout, no campo 'Cupom de desconto', insira o código e clique em "
            "'Aplicar'. Cupons não são acumulativos."
        ),
        "expected_doc_ids": ["KB-018"],
    },
    {
        "query": "Recebi um produto diferente do que pedi.",
        "expected_answer": (
            "Abra um chamado em até 48 horas com fotos da etiqueta e do produto. "
            "Enviamos o correto sem custo e coletamos o errado no mesmo dia."
        ),
        "expected_doc_ids": ["KB-019"],
    },
    {
        "query": "Como solicito acesso aos meus dados pessoais?",
        "expected_answer": (
            "Envie email para dpo@amazoniashop.com.br com seu CPF e o tipo de "
            "solicitação. Atendemos em até 15 dias úteis (LGPD)."
        ),
        "expected_doc_ids": ["KB-020"],
    },
    {
        "query": "Vocês fazem venda para empresas?",
        "expected_answer": (
            "Sim, para compras acima de 50 unidades do mesmo item. Envie email para "
            "corporativo@amazoniashop.com.br com CNPJ, produto e quantidade."
        ),
        "expected_doc_ids": ["KB-021"],
    },
    {
        "query": "Como funciona o programa de fidelidade?",
        "expected_answer": (
            "Cada R$ 1 vale 1 ponto. A cada 1.000 pontos você ganha R$ 50 em crédito. "
            "Pontos expiram em 12 meses."
        ),
        "expected_doc_ids": ["KB-023"],
    },
    {
        "query": "Posso comprar do exterior?",
        "expected_answer": "Não vendemos para fora do Brasil.",
        "expected_doc_ids": ["KB-025"],
    },
    {
        "query": "Vocês têm loja física?",
        "expected_answer": (
            "Não, somos 100% online. Temos centros de distribuição em SP, AM e PE, mas "
            "não é possível retirar pedidos pessoalmente."
        ),
        "expected_doc_ids": ["KB-027"],
    },
    {
        "query": "Não reconheço uma cobrança no meu cartão, o que fazer?",
        "expected_answer": (
            "Ligue imediatamente para 0800-AMAZONIA. Bloqueamos a conta enquanto "
            "investigamos. Contate também seu banco para iniciar o chargeback."
        ),
        "expected_doc_ids": ["KB-028"],
    },
    {
        "query": "Quanto custa para embalar como presente?",
        "expected_answer": (
            "R$ 9,90 por item, com opção de cartão personalizado. Selecione no checkout."
        ),
        "expected_doc_ids": ["KB-030"],
    },
]


# ---------------------------------------------------------------------------
# Pipeline principal
# ---------------------------------------------------------------------------

def main() -> None:
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    DATA_GOLDEN.mkdir(parents=True, exist_ok=True)

    # Tickets
    logger.info("Gerando tickets sintéticos…")
    tickets = generate_tickets(n=500)
    import csv

    tickets_path = DATA_RAW / "tickets.csv"
    fieldnames = list(asdict(tickets[0]).keys())
    with tickets_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for t in tickets:
            writer.writerow(asdict(t))
    logger.info("Tickets salvos em %s (%d registros)", tickets_path, len(tickets))

    # Knowledge base
    kb_path = DATA_RAW / "knowledge_base.json"
    with kb_path.open("w", encoding="utf-8") as f:
        json.dump(KNOWLEDGE_BASE, f, ensure_ascii=False, indent=2)
    logger.info("KB salva em %s (%d documentos)", kb_path, len(KNOWLEDGE_BASE))

    # Golden set
    golden_path = DATA_GOLDEN / "golden.json"
    with golden_path.open("w", encoding="utf-8") as f:
        json.dump(GOLDEN_SET, f, ensure_ascii=False, indent=2)
    logger.info("Golden set salvo em %s (%d pares)", golden_path, len(GOLDEN_SET))

    # Resumo
    print("\n=== Resumo da geração ===")
    print(f"Tickets:     {len(tickets):>4}  -> {tickets_path.relative_to(ROOT)}")
    print(f"KB docs:     {len(KNOWLEDGE_BASE):>4}  -> {kb_path.relative_to(ROOT)}")
    print(f"Golden set:  {len(GOLDEN_SET):>4}  -> {golden_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
