# data/class_labels.py

class_labels = {
    "forehead": [
        "Wrinkle Level 0",
        "Wrinkle Level 1",
        "Wrinkle Level 2",
        "Wrinkle Level 3",
        "Wrinkle Level 4",
        "Wrinkle Level 5",
        "Wrinkle Level 6",
        "Pigmentation Level 0",
        "Pigmentation Level 1",
        "Pigmentation Level 2",
        "Pigmentation Level 3",
        "Pigmentation Level 4",
        "Pigmentation Level 5",
        "Pigmentation Level 6",
        "Pigmentation Level 7"
    ],
    "glabellus": [
        "Wrinkle Level 0",
        "Wrinkle Level 1",
        "Wrinkle Level 2",
        "Wrinkle Level 3",
        "Wrinkle Level 4",
        "Wrinkle Level 5",
        "Wrinkle Level 6"
    ],
    "l_perocular": [
        "Wrinkle Level 0",
        "Wrinkle Level 1",
        "Wrinkle Level 2",
        "Wrinkle Level 3",
        "Wrinkle Level 4",
        "Wrinkle Level 5",
        "Wrinkle Level 6"
    ],
    "r_perocular": [
        "Wrinkle Level 0",
        "Wrinkle Level 1",
        "Wrinkle Level 2",
        "Wrinkle Level 3",
        "Wrinkle Level 4",
        "Wrinkle Level 5",
        "Wrinkle Level 6"
    ],
    "l_cheek": [
        "Pigmentation Level 0",
        "Pigmentation Level 1",
        "Pigmentation Level 2",
        "Pigmentation Level 3",
        "Pigmentation Level 4",
        "Pore Level 0",
        "Pore Level 1",
        "Pore Level 2",
        "Pore Level 3",
        "Pore Level 4"
    ],
    "r_cheek": [
        "Pigmentation Level 0",
        "Pigmentation Level 1",
        "Pigmentation Level 2",
        "Pigmentation Level 3",
        "Pigmentation Level 4",
        "Pore Level 0",
        "Pore Level 1",
        "Pore Level 2",
        "Pore Level 3",
        "Pore Level 4"
    ],
    "lip": [
        "Dryness Level 0",
        "Dryness Level 1",
        "Dryness Level 2",
        "Dryness Level 3",
        "Dryness Level 4"
    ],
    "chin": [
        "Sagging Level 0",
        "Sagging Level 1",
        "Sagging Level 2",
        "Sagging Level 3",
        "Sagging Level 4",
        "Sagging Level 5",
        "Sagging Level 6"
    ],
}

regression_labels = {
    "full_face": ["pigmentation"],
    "forehead": ["moisture", "elasticity"],
    "l_perocular": ["wrinkle"],
    "r_perocular": ["wrinkle"],
    "l_cheek": ["moisture", "elasticity", "pore"],
    "r_cheek": ["moisture", "elasticity", "pore"],
    "chin": ["moisture", "elasticity"],
}
