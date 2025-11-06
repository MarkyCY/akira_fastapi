
from database.mongo import get_db
from models.group_stats import StatsDaily

from PIL import Image
from io import BytesIO
import base64
import os
    
def resize_and_convert_to_base64(image_bytes, user_id, output_size=(200, 200)):
    # Abrir la imagen desde los bytes
    img = Image.open(BytesIO(image_bytes))
    
    # Redimensionar la imagen (aquí puedes personalizar el tamaño)
    img = img.resize(output_size, Image.LANCZOS)
    
    # Crear la carpeta si no existe
    os.makedirs("users/photo", exist_ok=True)
    
    # Guardar la imagen en formato JPEG en la ruta /users/photo
    image_filename = f"{user_id}.jpg"
    image_full_path = os.path.join("users/photo", image_filename)
    img.save(image_full_path, format="JPEG")
    
    # Convertir la imagen a formato base64
    buffered = BytesIO()
    img.save(buffered, format="JPEG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
    
    return img_base64

async def get_stats_daily():
    db = await get_db()
    Stats = db.stats

    pipeline = [
        {"$match": {"_id": "status_daily"}},

        # 1) crear lista de ids como strings
        {
            "$addFields": {
                "all_ids": {
                    "$concatArrays": [
                        { "$map": { "input": { "$ifNull": ["$top_admins", []] }, "as": "a", "in": { "$toString": "$$a.user_id" } } },
                        { "$map": { "input": { "$ifNull": ["$top_users", []] }, "as": "u", "in": { "$toString": "$$u.user_id" } } }
                    ]
                }
            }
        },

        # 2) traer docs de users
        {
            "$lookup": {
                "from": "users",
                "let": { "ids": "$all_ids" },
                "pipeline": [
                    { "$match": { "$expr": { "$in": [ { "$toString": "$user_id" }, "$$ids" ] } } },
                    { "$project": { "_id": 0, "user_id": 1, "avatar": 1 } }
                ],
                "as": "user_docs"
            }
        },

        # 3) mapear top_admins y top_users agregando avatar
        {
            "$addFields": {
                "top_admins": {
                    "$map": {
                        "input": { "$ifNull": ["$top_admins", []] },
                        "as": "a",
                        "in": {
                            "$mergeObjects": [
                                "$$a",
                                {
                                    "avatar": {
                                        "$let": {
                                            "vars": {
                                                "f": {
                                                    "$arrayElemAt": [
                                                        {
                                                            "$filter": {
                                                                "input": "$user_docs",
                                                                "as": "d",
                                                                "cond": { "$eq": [ { "$toString": "$$d.user_id" }, { "$toString": "$$a.user_id" } ] }
                                                            }
                                                        },
                                                        0
                                                    ]
                                                }
                                            },
                                            "in": {
                                                "$cond": [
                                                    { "$or": [ { "$eq": ["$$f", None] }, { "$eq": ["$$f.avatar", ""] } ] },
                                                    None,
                                                    "$$f.avatar"
                                                ]
                                            }
                                        }
                                    }
                                }
                            ]
                        }
                    }
                },
                "top_users": {
                    "$map": {
                        "input": { "$ifNull": ["$top_users", []] },
                        "as": "u",
                        "in": {
                            "$mergeObjects": [
                                "$$u",
                                {
                                    "avatar": {
                                        "$let": {
                                            "vars": {
                                                "f": {
                                                    "$arrayElemAt": [
                                                        {
                                                            "$filter": {
                                                                "input": "$user_docs",
                                                                "as": "d",
                                                                "cond": { "$eq": [ { "$toString": "$$d.user_id" }, { "$toString": "$$u.user_id" } ] }
                                                            }
                                                        },
                                                        0
                                                    ]
                                                }
                                            },
                                            "in": {
                                                "$cond": [
                                                    { "$or": [ { "$eq": ["$$f", None] }, { "$eq": ["$$f.avatar", ""] } ] },
                                                    None,
                                                    "$$f.avatar"
                                                ]
                                            }
                                        }
                                    }
                                }
                            ]
                        }
                    }
                }
            }
        },

        # 4) limpiar temporales
        { "$project": { "all_ids": 0, "user_docs": 0 } }
    ]

    cursor = Stats.aggregate(pipeline)
    result = await cursor.to_list(length=1)

    if not result:
        return None

    stats = result[0]
    return StatsDaily(**stats)