# data/class_labels.py

class_labels = {
    "forehead": ["wrinkle", "pigmentation"],
    "glabellus": ["wrinkle"],
    "l_perocular": ["wrinkle"],
    "r_perocular": ["wrinkle"],
    "l_cheek": ["pigmentation", "pore"],
    "r_cheek": ["pigmentation", "pore"],
    "lip": ["dryness"],
    "chin": ["sagging"],
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
