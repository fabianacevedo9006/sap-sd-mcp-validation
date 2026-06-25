# 🤖 SAP SD MCP Validation Agent
**SAP Clean Core AI Agent — Order-to-Cash Automation via MCP Protocol**

[![SAP S/4HANA Cloud](https://img.shields.io/badge/SAP%20S%2F4HANA-Cloud%20Public%20Edition-blue)](https://www.sap.com/products/erp/s4hana.html)
[![MCP Protocol](https://img.shields.io/badge/Protocol-MCP%20(Anthropic)-orange)](https://modelcontextprotocol.io)
[![SAP BTP](https://img.shields.io/badge/SAP%20BTP-Process%20Automation-green)](https://www.sap.com/products/technology-platform.html)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Autor:** Fabian Andrés Acevedo R. | Bogotá, Colombia  
> **Certificaciones:** C_S4CPB_2602 · C_LCNC_2601  
> **LinkedIn:** [linkedin.com/in/fabian-acevedo-sap-cloud-data](https://linkedin.com/in/fabian-acevedo-sap-cloud-data)

---

## 🎯 El Problema

En entornos SAP SD, la **validación manual de pedidos de venta** introduce fricciones críticas:

- Consultores SD deben verificar manualmente stock, pricing y crédito del cliente antes de crear cada orden.
- Pedidos rechazados en etapas tardías del proceso generan reprocesos costosos.
- La escalación de crédito a aprobadores depende de flujos manuales o correo electrónico.

**Resultado:** ciclos Order-to-Cash lentos, errores humanos y carga administrativa en el equipo de ventas.

---

## ✅ La Solución

Un **agente de IA conversacional** que, vía **Model Context Protocol (MCP)**, conecta a Claude con las reglas de negocio SAP SD — validando materiales, precios y crédito de cliente **en tiempo real**, antes de crear el pedido, y escalando automáticamente a **SAP Build Process Automation** cuando se detecta crédito insuficiente.

```
Usuario (lenguaje natural)
        ↓
   MCP Client (Claude claude-sonnet-4-6)
        ↓
   SAP SD MCP Server (FastMCP)
   ├── validate_material_number()    → Catálogo S/4HANA
   ├── check_pricing_conditions()    → Pricing SD
   ├── verify_customer_credit_limit()→ Credit Management
   └── create_sales_order()          → Pedido de venta
        ↓
   SAP Build Process Automation      → Escalación de crédito (XSUAA / OAuth2)
        ↓
   S/4HANA Core  ←  Clean Core ✅ (sin modificaciones al núcleo)
```

**Filosofía:** Este agente opera en la **periferia** del ecosistema SAP — nunca modifica el núcleo ERP. Respeta el principio **Clean Core** usando únicamente APIs estándar (`API_SALES_ORDER_SRV`) y servicios BTP.

---

## 🏗️ Arquitectura

| Capa | Componente | Rol |
|---|---|---|
| **Periferia** | FastMCP Server (`sap_sd_server.py`) | Expone herramientas SAP SD al agente IA |
| **Agente** | Claude claude-sonnet-4-6 vía Anthropic API | Razonamiento, orquestación y respuesta en lenguaje natural |
| **Integración** | SAP Build Process Automation API | Flujo de aprobación de crédito |
| **Autenticación** | XSUAA / OAuth2 (SAP BTP) | Seguridad enterprise sin hardcoding de secrets |
| **Core ERP** | SAP S/4HANA Cloud Public Edition | Fuente de verdad (en producción vía `A_SalesOrder` OData) |

---

## ⚡ Demo — Casos de prueba validados

| # | Escenario | Input | Resultado |
|---|---|---|---|
| ✅ 1 | Happy path | CUST-500 · MAT-1001 · 5u | Orden `SO-1001` creada |
| ❌ 2 | Crédito insuficiente | CUST-501 · MAT-1001 · 10u | Rechazada → escalada a SAP Build |
| ❌ 3 | Sin stock | CUST-500 · MAT-1003 · 2u | Rechazada: stock = 0 |
| ❌ 4 | Material inexistente | CUST-500 · MAT-9999 · 1u | Rechazada: no existe en catálogo |

---

## 🚀 Instalación y uso

### Prerrequisitos
- Python 3.10+
- Cuenta en [Anthropic Console](https://console.anthropic.com) con API Key

### Configuración

```bash
# 1. Clonar el repositorio
git clone https://github.com/fabianacevedo9006/sap-sd-mcp-validation.git
cd sap-sd-mcp-validation

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno (ver .env.example)
cp .env.example .env
# Editar .env con tus credenciales
```

`.env.example`:
```
ANTHROPIC_API_KEY=
BTP_TOKEN_URL=
BTP_API_BASE_URL=
BTP_CLIENT_ID=
BTP_CLIENT_SECRET=
```

### Ejecución (Google Colab)

Abre `SAP_SD_MCP_Agent_Colab.ipynb` en Google Colab y ejecuta las celdas en orden. El notebook guía el proceso completo en ~3 minutos.

---

## 📈 Valor de negocio

- **Reducción de carga administrativa** en el departamento de ventas — el agente valida en segundos lo que antes requería múltiples consultas manuales en SAP GUI.
- **Trazabilidad completa:** cada tool call queda registrada en el `audit_log` con timestamp, input y output — cumpliendo estándares de auditoría SAP.
- **Escalación automática:** pedidos con crédito insuficiente disparan un workflow en SAP Build Process Automation sin intervención manual.
- **Clean Core garantizado:** cero modificaciones al núcleo ERP — arquitectura certificable bajo SAP Clean Core Assessment.

---

## 🗺️ Roadmap

| Versión | Feature | Stack |
|---|---|---|
| **V1 ✅** | Material · Precio · Crédito · Pedido + SAP Build escalación | FastMCP · Mock data · BTP OAuth2 |
| **V2** | `check_atp()` — Available-to-Promise con fechas de entrega | Scheduling logic |
| **V3** | `propose_delivery_split()` — Entrega parcial automática | Supply Chain logic |
| **V4** | `trigger_credit_approval()` — Workflow parametrizable | SAP Build Process Automation API |
| **V5** | APIs reales S/4HANA Cloud vía Communication Arrangement | httpx · OAuth2 · `A_SalesOrder` OData |

---

## 🔗 Contexto SAP Discovery Mission

Este proyecto forma parte de la misión SAP Discovery Center:  
**"Soporte fundamental para iniciar la automatización de procesos a través de SAP Build"**

Demuestra la fase **Adopt** de SAP Activate: configuración de SAP Build Process Automation integrada con un agente IA de periferia, respetando el modelo Clean Core de SAP S/4HANA Cloud Public Edition.

---

## 📄 Licencia

MIT — ver [LICENSE](LICENSE)

---

*Tags: `sap-btp` · `gen-ai` · `mcp-protocol` · `s4hana-cloud` · `clean-core` · `order-to-cash` · `sap-build` · `process-automation`*
