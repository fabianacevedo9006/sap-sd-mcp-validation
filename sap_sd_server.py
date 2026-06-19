"""
╔══════════════════════════════════════════════════════════════╗
║   SAP SD Order Validation Agent — MCP Server (V1)           ║
║   Protocolo: Model Context Protocol (FastMCP / Anthropic)   ║
║                                                              ║
║   Autor  : Fabian Andrés Acevedo R.                         ║
║   Certs  : C_S4CPB_2602 · C_LCNC_2601                      ║
║   Stack  : FastMCP · SAP S/4HANA Cloud · BTP · Clean Core  ║
╚══════════════════════════════════════════════════════════════╝

ARQUITECTURA CLEAN CORE:
  Toda la lógica de validación corre en la PERIFERIA del ERP
  a través de MCP — sin modificar el estándar de SAP S/4HANA.

FLUJO O2C (Order-to-Cash) que implementa este agente:
  1. validate_material_number  → Verificación ATP básica
  2. check_pricing_conditions  → Esquema de cálculo / pricing
  3. verify_customer_credit_limit → Control de crédito
  4. create_sales_order        → Creación de orden (si todo OK)

DATOS:
  V1 usa datos mock que simulan el catálogo S/4HANA.
  V5 (roadmap) reemplaza por llamadas reales a API_SALES_ORDER_SRV
  vía Communication Arrangement + OAuth2 en BTP.
"""

from mcp.server.fastmcp import FastMCP
from pydantic import Field
from mcp.server.fastmcp.prompts import base

mcp = FastMCP("SAP_SD_Validation_Agent", log_level="ERROR")


# ──────────────────────────────────────────────────────────────
# DATOS MOCK
# Simulan el catálogo de materiales y maestro de clientes de
# un tenant S/4HANA Cloud Public Edition.
# En producción → reemplazar por httpx calls a:
#   GET /sap/opu/odata/sap/API_PRODUCT_SRV
#   GET /sap/opu/odata/sap/API_BUSINESS_PARTNER
# ──────────────────────────────────────────────────────────────

materials = {
    "MAT-1001": {
        "description": "Bomba centrífuga 5HP",
        "price_usd": 1250.00,
        "stock": 42,
        "unit": "EA",
    },
    "MAT-1002": {
        "description": "Válvula de control 2 pulgadas",
        "price_usd": 89.50,
        "stock": 310,
        "unit": "EA",
    },
    "MAT-1003": {
        "description": "Motor eléctrico trifásico",
        "price_usd": 640.00,
        "stock": 0,       # ← sin stock — caso de prueba V1
        "unit": "EA",
    },
    "MAT-1004": {
        "description": "Sensor de presión industrial",
        "price_usd": 215.75,
        "stock": 18,
        "unit": "EA",
    },
}

customers = {
    "CUST-500": {
        "name": "Industrias del Norte S.A.",
        "credit_limit_usd": 50000.00,
        "credit_used_usd": 12000.00,
    },
    "CUST-501": {
        "name": "Logística Andina Ltda.",
        "credit_limit_usd": 15000.00,
        "credit_used_usd": 14200.00,  # ← crédito casi agotado — caso de prueba V1
    },
}

sales_orders: dict = {}
_order_counter: int = 1000


# ──────────────────────────────────────────────────────────────
# TOOLS
# ──────────────────────────────────────────────────────────────

@mcp.tool(
    name="validate_material_number",
    description=(
        "Valida si un número de material existe en el catálogo SAP S/4HANA "
        "y retorna su disponibilidad de stock (verificación ATP básica)."
    ),
)
def validate_material_number(
    material_id: str = Field(description="Código de material SAP. Ej: MAT-1001"),
) -> dict:
    if material_id not in materials:
        raise ValueError(
            f"Material '{material_id}' no existe en el catálogo SAP. "
            f"Materiales disponibles: {list(materials.keys())}"
        )
    mat = materials[material_id]
    return {
        "material_id": material_id,
        "description": mat["description"],
        "unit": mat["unit"],
        "stock_disponible": mat["stock"],
        "disponible": mat["stock"] > 0,
        "mensaje": "Stock disponible ✅" if mat["stock"] > 0 else "Sin stock ❌ — no es posible crear la orden",
    }


@mcp.tool(
    name="check_pricing_conditions",
    description=(
        "Calcula el precio total de una línea de orden de venta según el "
        "esquema de cálculo (pricing conditions) del catálogo SAP."
    ),
)
def check_pricing_conditions(
    material_id: str = Field(description="Código de material SAP"),
    quantity: int = Field(description="Cantidad solicitada en la orden", gt=0),
) -> dict:
    if material_id not in materials:
        raise ValueError(f"Material '{material_id}' no existe en el catálogo SAP.")
    if quantity <= 0:
        raise ValueError("La cantidad debe ser mayor a cero.")

    unit_price = materials[material_id]["price_usd"]
    total = round(unit_price * quantity, 2)

    return {
        "material_id": material_id,
        "description": materials[material_id]["description"],
        "quantity": quantity,
        "unit_price_usd": unit_price,
        "total_price_usd": total,
        "currency": "USD",
    }


@mcp.tool(
    name="verify_customer_credit_limit",
    description=(
        "Verifica si un cliente SAP tiene crédito disponible suficiente "
        "para cubrir el valor total de la orden. Si el crédito es insuficiente, "
        "el agente debe escalar a SAP Build Process Automation (V4 roadmap)."
    ),
)
def verify_customer_credit_limit(
    customer_id: str = Field(description="Código de cliente SAP. Ej: CUST-500"),
    order_amount_usd: float = Field(description="Monto total de la orden en USD"),
) -> dict:
    if customer_id not in customers:
        raise ValueError(
            f"Cliente '{customer_id}' no existe en el maestro de clientes. "
            f"Clientes disponibles: {list(customers.keys())}"
        )

    cust = customers[customer_id]
    available_credit = round(cust["credit_limit_usd"] - cust["credit_used_usd"], 2)
    approved = order_amount_usd <= available_credit

    return {
        "customer_id": customer_id,
        "customer_name": cust["name"],
        "credit_limit_usd": cust["credit_limit_usd"],
        "credit_used_usd": cust["credit_used_usd"],
        "credit_available_usd": available_credit,
        "order_amount_usd": order_amount_usd,
        "approved": approved,
        "action": (
            "✅ Proceder con la creación de la orden"
            if approved else
            "❌ Crédito insuficiente — escalar a SAP Build Process Automation para aprobación manual (V4)"
        ),
    }


@mcp.tool(
    name="create_sales_order",
    description=(
        "Crea una orden de venta SAP SD (Sales Order) una vez que las "
        "validaciones de material, pricing y crédito han sido exitosas. "
        "Retorna el número de orden generado con estado CREATED."
    ),
)
def create_sales_order(
    customer_id: str = Field(description="Código de cliente SAP"),
    material_id: str = Field(description="Código de material SAP"),
    quantity: int = Field(description="Cantidad a ordenar", gt=0),
) -> dict:
    global _order_counter

    # Validaciones de seguridad (guardas finales antes de escribir)
    if customer_id not in customers:
        raise ValueError(f"Cliente '{customer_id}' no existe.")
    if material_id not in materials:
        raise ValueError(f"Material '{material_id}' no existe.")
    if materials[material_id]["stock"] < quantity:
        raise ValueError(
            f"Stock insuficiente para '{material_id}'. "
            f"Solicitado: {quantity} | Disponible: {materials[material_id]['stock']}"
        )

    _order_counter += 1
    order_id = f"SO-{_order_counter}"
    total = round(materials[material_id]["price_usd"] * quantity, 2)

    sales_orders[order_id] = {
        "customer_id": customer_id,
        "customer_name": customers[customer_id]["name"],
        "material_id": material_id,
        "description": materials[material_id]["description"],
        "quantity": quantity,
        "total_usd": total,
        "status": "CREATED",
    }

    # Descuenta stock (simula actualización en S/4HANA)
    materials[material_id]["stock"] -= quantity

    return {
        "order_id": order_id,
        "status": "CREATED ✅",
        "customer_id": customer_id,
        "customer_name": customers[customer_id]["name"],
        "material_id": material_id,
        "quantity": quantity,
        "total_usd": total,
        "currency": "USD",
        "mensaje": f"Orden {order_id} creada exitosamente en SAP SD.",
    }


# ──────────────────────────────────────────────────────────────
# RESOURCES
# Exponen datos de referencia SAP al agente como contexto
# ──────────────────────────────────────────────────────────────

@mcp.resource("sap://materials", mime_type="application/json")
def list_materials() -> list:
    """Catálogo completo de materiales SAP disponibles."""
    return list(materials.keys())


@mcp.resource("sap://materials/{material_id}", mime_type="application/json")
def fetch_material(material_id: str) -> dict:
    """Detalle completo de un material SAP específico."""
    if material_id not in materials:
        raise ValueError(f"Material '{material_id}' no encontrado.")
    return materials[material_id]


@mcp.resource("sap://customers", mime_type="application/json")
def list_customers() -> list:
    """Lista de clientes SAP disponibles en el maestro."""
    return list(customers.keys())


@mcp.resource("sap://orders", mime_type="application/json")
def list_orders() -> dict:
    """Órdenes de venta creadas en la sesión actual."""
    return sales_orders


# ──────────────────────────────────────────────────────────────
# PROMPTS
# Instrucciones pre-configuradas para el agente
# ──────────────────────────────────────────────────────────────

@mcp.prompt(
    name="validate_full_order",
    description=(
        "Ejecuta el flujo completo de validación de una orden SAP SD: "
        "material → pricing → crédito → creación. "
        "Si alguna validación falla, documenta la excepción y no crea la orden."
    ),
)
def validate_full_order(
    customer_id: str = Field(description="Código de cliente SAP"),
    material_id: str = Field(description="Código de material SAP"),
    quantity: int = Field(description="Cantidad solicitada"),
) -> list[base.Message]:
    prompt = f"""
    Eres un agente SAP SD especializado en validación Order-to-Cash bajo estrategia Clean Core.

    Procesa esta solicitud de orden de venta:
    - Cliente  : {customer_id}
    - Material : {material_id}
    - Cantidad : {quantity}

    Flujo obligatorio (en este orden exacto):
    1. validate_material_number({material_id})  → confirmar existencia y stock
    2. check_pricing_conditions({material_id}, {quantity})  → calcular total
    3. verify_customer_credit_limit({customer_id}, <total calculado en paso 2>)
    4a. Si los 3 pasos son exitosos → create_sales_order({customer_id}, {material_id}, {quantity})
    4b. Si algún paso falla → NO crear la orden. Documentar qué falló, por qué,
        y qué acción se recomienda (ej: escalar a SAP Build Process Automation).

    Presenta el resultado de cada paso claramente, como un consultor SAP SD documentando
    una excepción de proceso en SAP Cloud ALM.
    """
    return [base.UserMessage(prompt)]


if __name__ == "__main__":
    mcp.run(transport="stdio")
