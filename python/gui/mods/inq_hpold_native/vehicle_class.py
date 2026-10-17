# -*- coding: utf-8 -*-

try:
    from gui.shared.gui_items.Vehicle import getVehicleClassTag
except Exception:
    getVehicleClassTag = None


_VEHICLE_CLASSES = ('lightTank', 'mediumTank', 'heavyTank', 'AT-SPG', 'SPG')


def _normalize(value):
    if value is None:
        return ''
    try:
        value = str(value)
    except Exception:
        return ''

    lower = value.lower()
    aliases = {
        'lighttank': 'lightTank',
        'light_tank': 'lightTank',
        'mediumtank': 'mediumTank',
        'medium_tank': 'mediumTank',
        'heavytank': 'heavyTank',
        'heavy_tank': 'heavyTank',
        'at-spg': 'AT-SPG',
        'at_spg': 'AT-SPG',
        'tankdestroyer': 'AT-SPG',
        'tank_destroyer': 'AT-SPG',
        'spg': 'SPG',
        'artillery': 'SPG',
    }
    return aliases.get(lower, value if value in _VEHICLE_CLASSES else '')


def _from_tags(tags):
    if not tags:
        return ''

    if getVehicleClassTag is not None:
        try:
            result = _normalize(getVehicleClassTag(tags))
            if result:
                return result
        except Exception:
            pass

    for class_name in _VEHICLE_CLASSES:
        try:
            if class_name in tags:
                return class_name
        except Exception:
            pass
    return ''


def _read_member(value, name):
    if value is None:
        return None
    if isinstance(value, dict):
        try:
            return value.get(name)
        except Exception:
            return None
    try:
        return getattr(value, name, None)
    except Exception:
        return None


def _from_candidate(candidate):
    if candidate is None:
        return ''

    direct = _normalize(candidate)
    if direct:
        return direct

    for name in ('classTag', 'vehicleClass', 'vehicleClassTag', 'className'):
        result = _normalize(_read_member(candidate, name))
        if result:
            return result

    result = _from_tags(_read_member(candidate, 'tags'))
    if result:
        return result

    return ''


def resolve_vehicle_class(vehicle_data):
    """Resolve WoT vehicle class across old and new arena vehicle-data layouts."""
    if not vehicle_data:
        return ''

    candidates = [vehicle_data]

    for name in (
        'vehicleType',
        'vehicleTypeDescriptor',
        'vehicleTypeInfo',
        'typeDescriptor',
        'descriptor',
        'type',
    ):
        value = _read_member(vehicle_data, name)
        if value is not None:
            candidates.append(value)

    # Newer descriptors/VOs often wrap the actual type one level deeper.
    for candidate in list(candidates):
        for name in ('type', 'vehicleType', 'descriptor'):
            nested = _read_member(candidate, name)
            if nested is not None and nested not in candidates:
                candidates.append(nested)

    for candidate in candidates:
        result = _from_candidate(candidate)
        if result:
            return result

    return ''
