# 🤖 SAP SD Order Validation Agent — MCP Protocol

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/fabianacevedo9006/sap-sd-mcp-validation/blob/main/SAP_SD_MCP_Agent_Fabian_Acevedo.ipynb)
![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![MCP](https://img.shields.io/badge/Protocol-MCP%20%7C%20Anthropic-orange)
![SAP](https://img.shields.io/badge/SAP-S%2F4HANA%20Cloud-blue?logo=sap)
![Clean Core](https://img.shields.io/badge/Strategy-Clean%20Core-green)

> **Autor:** Fabian Andrés Acevedo R. | Bogotá, Colombia
> **Certificaciones:** C_S4CPB_2602 · C_LCNC_2601
> **LinkedIn:** [fabian-acevedo-sap-cloud-data](https://linkedin.com/in/fabian-acevedo-sap-cloud-data)

---

## 🎯 ¿Qué hace este proyecto?

Un agente de inteligencia artificial que valida órdenes de venta SAP SD (Order-to-Cash) **antes de impactar el ERP**, utilizando el **Model Context Protocol (MCP)** de Anthropic como capa de comunicación entre Claude/Joule y SAP S/4HANA Cloud Public Edition.

### El problema que resuelve

En SAP SD, los errores de pricing, crédito y disponibilidad de material generan correcciones manuales costosas:

| Métrica | Sin agente | Con agente MCP |
|---|---|---|
| Error rate en órdenes | ~3-5% | < 0.5% |
| Tiempo de corrección/error | 30-45 min | 0 min |
| Costo estimado/error | ~$400 USD | $0 |
| Ahorro mensual (500 órdenes) | — | **~$5,400 USD** |

---

## 🏗️ Arquitectura Clean Core

```
Usuario / Comprador
        ↓
   MCP Client
(Our Server / App)
        ↓
  SAP SD MCP Server         ← Este repositorio
  (sap_sd_server.py)
        ↓                         ↓
  Claude / Joule         S/4HANA Cloud API
     Agent               (API_SALES_ORDER_SRV)
```

**Principio Clean Core:** Toda la lógica de validación corre en la **periferia del ERP** a través de MCP. El core de SAP S/4HANA no es modificado — extensibilidad 100% vía BTP.

---

## 🛠️ Tools expuestas al agente

| Tool | Descripción | Equivalente SAP |
|---|---|---|
| `validate_material_number` | Verifica existencia y stock | Verificación ATP |
| `check_pricing_conditions` | Calcula precio total de la orden | Esquema de cálculo |
| `verify_customer_credit_limit` | Valida cupo financiero del cliente | Control de crédito FI |
| `create_sales_order` | Crea la orden si todo es válido | VA01 / API_SALES_ORDER_SRV |

### Resources disponibles
- `sap://materials` — Catálogo de materiales
- `sap://customers` — Maestro de clientes
- `sap://orders` — Órdenes creadas en sesión

### Prompt pre-configurado
- `validate_full_order` — Orquesta el flujo completo O2C con auditoría

---

## 🚀 Cómo probarlo

### Opción A — Google Colab (recomendado, sin instalación)

1. Haz clic en el badge **Open In Colab** al inicio de este README
2. Ve al panel izquierdo → ícono 🔑 Secrets → agrega `ANTHROPIC_API_KEY`
3. Menú → **Ejecutar todo**

### Opción B — Local

```bash
# Clonar repositorio
git clone https://github.com/TU_USUARIO/sap-sd-mcp-validation.git
cd sap-sd-mcp-validation

# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar API key
echo "ANTHROPIC_API_KEY=sk-ant-tu-key" > .env

# Correr el servidor MCP directamente
python sap_sd_server.py
```

---

## 🧪 Casos de prueba incluidos

| Escenario | Cliente | Material | Cantidad | Resultado |
|---|---|---|---|---|
| ✅ Happy path | CUST-500 | MAT-1001 | 5 | Orden SO-1001 creada |
| ❌ Sin stock | CUST-500 | MAT-1003 | 1 | Falla: stock = 0 |
| ❌ Crédito insuficiente | CUST-501 | MAT-1001 | 10 | Escala a Build Process Automation |
| ❌ Material inválido | CUST-500 | MAT-9999 | 1 | Falla: material no existe |

---

## 📋 Audit Log integrado

Cada llamada del agente queda registrada con trazabilidad completa:

```
[1] 2026-06-18T10:30:01
    Evento : TOOL_CALL
    Tool   : validate_material_number
    Input  : {"material_id": "MAT-1001"}
    Output : {"stock_disponible": 42, "disponible": true}

[2] 2026-06-18T10:30:02
    Evento : TOOL_CALL
    Tool   : check_pricing_conditions
    Input  : {"material_id": "MAT-1001", "quantity": 5}
    Output : {"total_price_usd": 6250.0}
```

---

## 🗺️ Roadmap

| Versión | Feature | Stack adicional |
|---|---|---|
| **V1 ✅** | Material · Pricing · Crédito · Creación | FastMCP + Mock data |
| V2 | `check_atp()` — Available-to-Promise con fechas de entrega | Scheduling logic |
| V3 | `propose_delivery_split()` — Propuesta de entrega parcial | Supply Chain logic |
| V4 | `trigger_credit_approval()` — Escalación vía workflow | SAP Build Process Automation |
| V5 | APIs reales S/4HANA Cloud via Communication Arrangement | httpx + OAuth2 + BTP Destination |

---

## 🔗 Alineación con SAP Roadmap oficial

Este proyecto anticipa funcionalidades del **SAP S/4HANA Cloud release 2608 (Q3 2026)**:
- *AI-assisted sales order creation from unstructured data* — SAP Road Map Explorer
- *Autonomous Enterprise agents for O2C processes* — SAP Sapphire 2026

---

## 📁 Estructura del repositorio

```
sap-sd-mcp-validation/
│
├── .gitignore                          # Excluye .env, __pycache__, .venv
├── requirements.txt                    # Dependencias Python
├── sap_sd_server.py                    # Servidor MCP SAP SD (FastMCP)
├── SAP_SD_MCP_Agent_Fabian_Acevedo.ipynb  # Notebook Colab interactivo
└── README.md                           # Este archivo
```

---

## 🤝 Sobre el autor

SAP Certified Implementation Consultant (C_S4CPB_2602) y SAP Certified Build Developer (C_LCNC_2601). Especializado en SAP BTP, Clean Core extensibility, y automatización de procesos O2C con IA.

**Open to remote SAP consulting roles — LATAM / Global (EST/CST)**

