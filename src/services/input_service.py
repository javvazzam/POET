import random
from typing import Union, List

from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlmodel import select

from core.models import models
from core.models.database import engine_async
from core.schemas import schemas
from services import template_service

from itertools import chain


async def generate_input(n):
    try:
        async with AsyncSession(engine_async) as session:
            templates = cast_templates(await template_service.get_all_templates())

            num_templates = len(templates)
            if num_templates == 0:
                raise ValueError("No templates available to generate input.")

            distribution = [random.randint(1, max(1, n // num_templates)) for _ in range(num_templates)]
            remaining = n - sum(distribution)
            while remaining > 0:
                for i in range(len(distribution)):
                    if remaining <= 0:
                        break
                    distribution[i] += 1
                    remaining -= 1

            distribution = [min(d, n) for d in distribution]

            result = []
            for template, num_inputs in zip(templates, distribution):
                generated = template.build(num_inputs, mode="random")
                result.extend(cast_input(generated))

            random.shuffle(result)

            return result[:n]
    except Exception as e:
        raise RuntimeError(e)


async def generate_with_template_id(template_id, n, mode):
    template = await template_service.get_template_by_id(template_id)
    result = cast_templates(template)
    result = result[0].build(n, mode)
    return cast_input(result)


# async def generate_with_template(template:schemas.TemplateCreateMarker, n: int, mode: str):
#     template = schemas.Template(**template.__dict__)
#     result = template.build(n, mode)
#     return cast_input(result)

async def generate_with_template(template_marker: schemas.TemplateCreateMarker, n: int, mode: str):
    # Convierte PlaceholderBase a Placeholder (simplificado, asegúrate de ajustar según tu modelo exacto)
    placeholders = [schemas.Placeholder(**pb.dict()) for pb in template_marker.placeholders]

    # Crea una instancia de Template usando el TemplateCreateMarker y los Placeholders convertidos
    template = schemas.Template(
        base=template_marker.base,
        description=template_marker.description,
        expected_result=template_marker.expected_result,
        placeholders=placeholders,
        id=None  # Asegúrate de gestionar el ID como necesario
    )



    # Construye las combinaciones y las devuelve
    result = template.build(n, mode)
    return cast_input(result)


# async def generate_with_template(template: Union[List[schemas.TemplateCreateMarker], schemas.TemplateCreateMarker],
#                                  n: int, save):
#     if save and isinstance(template, List):
#         return await _generate_with_templates(template, n)
#     elif save and not isinstance(template, List):
#         return await _generate_with_template(template, n)
#     elif not save and isinstance(template, List):
#         return await _generate_with_templates_whithout_save(template, n)
#     elif not save and not isinstance(template, List):
#         print("1", template, n)
#         return await _generate_with_template_whithout_save(template, n)


async def _generate_with_template(template: schemas.TemplateCreateMarker, n):
    template = await template_service.create_template(template)
    template = schemas.Template(**template.__dict__)
    result = template.build(n)
    return cast_input(result)


async def _generate_with_templates(templates: List[schemas.TemplateCreateMarker], n):
    result = []
    print(templates)
    for template in templates:
        result.extend(await _generate_with_template(template, n))
    return result


async def _generate_with_template_whithout_save(template: schemas.TemplateCreateMarker, n):
    template = schemas.Template(**template.__dict__)
    return cast_input(template.build(n))


async def _generate_with_templates_whithout_save(templates: List[schemas.TemplateCreateMarker], n):
    result = []
    for template in templates:
        result.extend(await _generate_with_template_whithout_save(template, n))
    return result


def cast_templates(templates):
    return [schemas.Template(**template.__dict__) for template in templates]


def cast_input(inputs):
    return [schemas.Input(query=input, type=inputs[2] if inputs[2] else "bias", expected_result=inputs[1]) for input in inputs[0]]

