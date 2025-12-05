Caracteres súper/especiales
===========================



Substitucion / a substituir

Las secuencias de escape a substituir deben ser respetadas.

substitutions = {
    "⩵": "==", 
    "＝": "=", 
    ";": ";", 
    "＃": "#",
    "｛": "{",
    "｝": "}",
    " ": " ", 
    "↵": "\n",
    "    ": "\t",
    "＞": ">",
    "＜": "<", 
    "［": "[", 
    "］": "]",
    " " : " ",
    "（" : "(",
    "）" : ")",
    "＊" : "*",
    "＂" : """,
    "：" : ":",
    "＆" " "&",
}

# Mapeo de HTML entities comunes a caracteres fullwidth
Para reemplazar dentro de las secciones CDATA
entities_to_fullwidth = {
    "&lt;": "＜",
    "&gt;": "＞",
    "&amp;": "＆",
    "&quot;": "＂",
    "&apos;": "＇",
    "&#39;": "＇",
    "&#34;": "＂",
    "&#60;": "＜",
    "&#62;": "＞",
    "&#38;": "＆",
    "&nbsp;": "　",
}
