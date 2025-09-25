import logging
from decimal import Decimal, ROUND_HALF_UP

logger = logging.getLogger(__name__)

# Define a named tuple or dataclass for pricing result for clarity
from collections import namedtuple
PricingDetails = namedtuple('PricingDetails', ['price_usd', 'estimated_lead_time_days', 'calculation_details', 'errors'])


def calculate_quote_price(design, manufacturer):
    """
    Calculates a price quote for a given design from a specific manufacturer.

    Args:
        design (designs.models.Design): The design object with geometric_data and material.
        manufacturer (accounts.models.Manufacturer): The manufacturer object with pricing factors.

    Returns:
        PricingDetails: A named tuple containing price_usd, estimated_lead_time_days,
                        calculation_details (dict for transparency), and errors (list of strings).
    """
    errors = []
    calculation_details = {}

    # 1. Validate inputs
    if not design.geometric_data:
        errors.append("Design geometric data is missing or incomplete.")
        return PricingDetails(None, None, calculation_details, errors)

    volume_cm3 = Decimal(str(design.geometric_data.get("volume_cm3", 0)))
    complexity_score = Decimal(str(design.geometric_data.get("complexity_score", 0)))
    design_material_name = design.material # e.g., "Al-6061"

    if volume_cm3 <= 0:
        errors.append("Design volume must be a positive value.")
    # complexity_score can be 0 or positive.

    capabilities = manufacturer.capabilities or {}
    pricing_factors = capabilities.get("pricing_factors", {})
    material_properties_map = pricing_factors.get("material_properties", {})
    machining_factors = pricing_factors.get("machining", {})

    manufacturer_markup = manufacturer.markup_factor # This is a Decimal

    # 2. Calculate Material Cost
    material_cost = Decimal("0.00")
    if design_material_name in material_properties_map:
        props = material_properties_map[design_material_name]
        density_g_cm3 = Decimal(str(props.get("density_g_cm3", 0)))
        cost_usd_kg = Decimal(str(props.get("cost_usd_kg", 0)))

        if density_g_cm3 <= 0:
            errors.append(f"Density for material '{design_material_name}' must be positive.")
        if cost_usd_kg < 0: # Cost can be 0 for some scenarios, but not negative
            errors.append(f"Cost per kg for material '{design_material_name}' must be non-negative.")

        if not errors: # Proceed if no material property errors
            # MaterialCost = volume_cm3 * density_g_cm3 * (cost_usd_kg / 1000)
            # (cost_usd_kg / 1000) is cost_usd_g
            cost_usd_g = cost_usd_kg / Decimal("1000.0")
            material_cost = volume_cm3 * density_g_cm3 * cost_usd_g
            calculation_details["material_volume_cm3"] = float(volume_cm3)
            calculation_details["material_density_g_cm3"] = float(density_g_cm3)
            calculation_details["material_cost_usd_kg"] = float(cost_usd_kg)
            calculation_details["calculated_material_cost_usd"] = float(material_cost.quantize(Decimal("0.01"), ROUND_HALF_UP))
    else:
        errors.append(f"Manufacturer does not have pricing information for material: {design_material_name}")

    # 3. Calculate Machine Time Cost
    # MachineTimeCost = base_time + (geometric_data.complexity_score * time_multiplier)
    # These are assumed to be in cost units or a generic unit that markup applies to.
    base_time_cost_unit = Decimal(str(machining_factors.get("base_time_cost_unit", 0))) # e.g. direct cost or hours to be multiplied by a rate
    time_multiplier_complexity_cost_unit = Decimal(str(machining_factors.get("time_multiplier_complexity_cost_unit", 0)))

    # For a simpler model, if base_time and time_multiplier are direct cost components:
    if base_time_cost_unit < 0: errors.append("Base time cost unit cannot be negative.")
    if time_multiplier_complexity_cost_unit < 0: errors.append("Time multiplier cost unit cannot be negative.")

    machine_time_cost = Decimal("0.00")
    if not errors: # Proceed if no errors so far with base values
        machine_time_cost = base_time_cost_unit + (complexity_score * time_multiplier_complexity_cost_unit)
        calculation_details["machining_base_time_cost_unit"] = float(base_time_cost_unit)
        calculation_details["design_complexity_score"] = float(complexity_score)
        calculation_details["machining_time_multiplier_cost_unit"] = float(time_multiplier_complexity_cost_unit)
        calculation_details["calculated_machine_time_cost_units"] = float(machine_time_cost.quantize(Decimal("0.01"), ROUND_HALF_UP))


    # 4. Calculate Total Price
    total_price_before_markup = material_cost + machine_time_cost
    calculation_details["total_price_before_markup_usd"] = float(total_price_before_markup.quantize(Decimal("0.01"), ROUND_HALF_UP))

    if manufacturer_markup <= 0: # Should be caught by serializer validation too
        errors.append("Manufacturer markup factor must be positive.")

    total_price = Decimal("0.00")
    if not errors:
        total_price = total_price_before_markup * manufacturer_markup
        calculation_details["manufacturer_markup_factor"] = float(manufacturer_markup)
        final_price_usd = total_price.quantize(Decimal("0.01"), ROUND_HALF_UP) # Standard currency rounding
        calculation_details["final_total_price_usd"] = float(final_price_usd)
    else:
        final_price_usd = None # Cannot calculate price if there are errors

    # 5. Determine Estimated Lead Time
    # For now, take from manufacturer profile or use a default.
    # Could also be calculated based on complexity, quantity etc. in a more advanced model.
    estimated_lead_time_days = pricing_factors.get("estimated_lead_time_base_days", 7) # Default to 7 days if not specified
    if not isinstance(estimated_lead_time_days, int) or estimated_lead_time_days < 0:
        logger.warning(f"Invalid estimated_lead_time_base_days for manufacturer {manufacturer.user.email}: {estimated_lead_time_days}. Defaulting to 7.")
        estimated_lead_time_days = 7 # Fallback default
    calculation_details["estimated_lead_time_days"] = estimated_lead_time_days

    if errors:
        logger.warning(f"Pricing calculation failed for Design {design.id} by Manufacturer {manufacturer.user.email}. Errors: {errors}")
        return PricingDetails(price_usd=None, estimated_lead_time_days=None, calculation_details=calculation_details, errors=errors)

    logger.info(f"Pricing calculation successful for Design {design.id} by Manufacturer {manufacturer.user.email}. Price: {final_price_usd}, Lead Time: {estimated_lead_time_days} days.")
    return PricingDetails(price_usd=final_price_usd, estimated_lead_time_days=estimated_lead_time_days, calculation_details=calculation_details, errors=[])
