from flask import Flask, request, render_template_string
import re
import ply.lex as lex

app = Flask(__name__)

# Actualización de tokens para el analizador léxico
tokens = {
    'PR': r'\b(Inicio|cadena|proceso|si|ver|Fin)\b',
    'ID': r'\b[a-zA-Z_][a-zA-Z_0-9]*\b',
    'NUM': r'\b\d+\b',
    'SYM': r'[;{}()\[\]=<>!+-/*]',
    'ERR': r'.'
}

def t_error(t):
    print(f"Carácter ilegal '{t.value[0]}'")
    t.lexer.skip(1)

# Plantilla HTML para mostrar resultados
html_template = '''
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
  <style>
    body {
      font-family: 'Arial', sans-serif; /* Cambio de la fuente a Arial */
      background-color: #f0f0f0;
      margin: 0;
      padding: 20px;
      color: #555;
    }
    h1, h2 {
      text-align: center;
      color: #00897b;
      margin-bottom: 20px;
    }
    form {
      background-color: #fff;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
      max-width: 800px;
      margin: 0 auto 20px auto;
    }
    textarea {
      width: 100%;
      padding: 10px;
      border: 1px solid #ccc;
      border-radius: 4px;
      font-family: 'Arial', sans-serif; /* Cambio de la fuente a Arial */
      font-size: 16px;
    }
    input[type="submit"] {
      background-color: #00897b;
      color: white;
      padding: 14px 20px;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      transition: background-color 0.3s ease;
      font-size: 16px;
    }
    input[type="submit"]:hover {
      background-color: #00695c;
    }
    .container {
      display: flex;
      flex-direction: column;
      align-items: center;
      max-width: 1000px;
      margin: 0 auto;
    }
    .content {
      display: flex;
      justify-content: space-between;
      width: 100%;
      margin-top: 20px;
    }
    .results {
      flex: 1;
      background-color: #fff;
      border-radius: 8px;
      box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
      padding: 20px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-bottom: 20px;
    }
    table, th, td {
      border: 1px solid #ddd;
    }
    th, td {
      padding: 12px;
      text-align: left;
    }
    th {
      background-color: #00897b;
      color: white;
    }
    tr:nth-child(even) {
      background-color: #f2f2f2;
    }
    tr:hover {
      background-color: #e0e0e0;
    }
  </style>
  <title>Analizador</title>
</head>
<body>
  <div class="container">
    <h1>Analizador</h1>
    <form method="post">
      <textarea name="code" rows="10" cols="50">{{ code }}</textarea><br>
      <input type="submit" value="Analizar">
    </form>
    <div class="content">
      <div class="results">
        <h2>Resultados del Análisis</h2>
        <div style="overflow-x:auto;">
          <table>
            <tr>
              <th>Tipo de Token</th>
              <th>P. Reservadas</th>
              <th>Identificadores</th>
              <th>Números</th>
              <th>Símbolos</th>
              <th>Errores</th>
            </tr>
            {% for row in lexical %}
            <tr>
              <td>{{ row[0] }}</td>
              <td>{{ row[1] }}</td>
              <td>{{ row[2] }}</td>
              <td>{{ row[3] }}</td>
              <td>{{ row[4] }}</td>
              <td>{{ row[5] }}</td>
            </tr>
            {% endfor %}
            <tr>
              <td><strong>Total</strong></td>
              <td>{{ total['PR'] }}</td>
              <td>{{ total['ID'] }}</td>
              <td>{{ total['NUM'] }}</td>
              <td>{{ total['SYM'] }}</td>
              <td>{{ total['ERR'] }}</td>
            </tr>
          </table>
        </div>
      </div>
      <div class="results" style="margin-left: 20px;">
        <h2>Detalles del Análisis</h2>
        <div style="background-color: #f2f2f2; padding: 15px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);">
          <h3>Análisis Sintáctico y Semántico</h3>
          <p><strong>Sintáctico:</strong> {{ syntactic }}</p>
          <p><strong>Semántico:</strong> {{ semantic }}</p>
        </div>
      </div>
    </div>
  </div>
</body>
</html>
'''

def analyze_lexical(code):
    results = {'PR': 0, 'ID': 0, 'NUM': 0, 'SYM': 0, 'ERR': 0}
    rows = []
    declared_variables = set()  # Conjunto para almacenar variables declaradas

    for line in code.split('\n'):
        row = [''] * 6
        for token_name, token_pattern in tokens.items():
            for match in re.findall(token_pattern, line):
                if token_name == 'ID':  # Si es un identificador (variable)
                    declared_variables.add(match)  # Agregar al conjunto de variables declaradas
                results[token_name] += 1
                row[list(tokens.keys()).index(token_name)] = 'x'
        rows.append(row)
    
    return rows, results, declared_variables  # Devolver también el conjunto de variables declaradas

def analyze_syntactic(code):
    corrected_code = code
    errors = []

    # Verificar la estructura de "Inicio" y "Fin"
    if not code.startswith("Inicio;"):
        errors.append("El código debe comenzar con 'Inicio;'.")
    if not code.endswith("Fin;"):
        errors.append("El código debe terminar con 'Fin;'.")

    # Verificar la estructura de bloques y sentencias
    if "proceso;" not in code:
        errors.append("Falta la declaración de 'proceso;'.")
    if "si (" in code and not re.search(r"si\s*\(.+\)\s*\{", code):
        errors.append("Estructura incorrecta de 'si'. Debe ser 'si (condición) {'.")
    if "{" in code and "}" not in code:
        errors.append("Falta cerrar un bloque con '}'.")
    if "}" in code and "{" not in code:
        errors.append("Falta abrir un bloque con '{'.")
    
    # Dividir el código en líneas y verificar el punto y coma
    lines = code.split('\n')
    for i, line in enumerate(lines):
        # Ignorar líneas que no requieren punto y coma
        if line.strip() and not line.strip().endswith(';') and not line.strip().endswith('{') and not line.strip().endswith('}') and "si (" not in line and "Inicio;" not in line and "Fin;" not in line:
            errors.append(f"Falta punto y coma al final de la línea {i + 1}.")

    if not errors:
        return "Sintaxis correcta", corrected_code
    else:
        return " ".join(errors), corrected_code


def analyze_semantic(code):
    errors = []
    corrected_code = code
    variable_types = {}
    declared_variables = set()

    # Palabras reservadas y funciones conocidas que no deben ser tratadas como variables
    reserved_words = {'Inicio', 'Fin', 'proceso', 'si', 'ver'}
    functions = {'Inicio', 'Fin', 'si', 'ver'}

    # Identificar y almacenar los tipos de las variables
    for var_declaration in re.findall(r"\b(cadena|entero)\s+(\w+)\s*=", code):
        var_type, var_name = var_declaration
        if var_name not in reserved_words and var_name not in functions:
            variable_types[var_name] = var_type
            declared_variables.add(var_name)  # Agregar al conjunto de variables declaradas

    # Verificar la asignación correcta de valores a variables
    assignments = re.findall(r"\bentero\s+\w+\s*=\s*\w+;", code)
    for assignment in assignments:
        if not re.match(r"\bentero\s+\w+\s*=\s*\d+;", assignment):
            variable_name = re.search(r"\bentero\s+(\w+)\s*=", assignment).group(1)
            if variable_name not in reserved_words and variable_name not in functions:
                errors.append(f"Error semántico en la asignación de '{variable_name}'. Debe ser un número entero.")

    # Verificar comparaciones lógicas
    logical_checks = re.findall(r"si\s*\((.+)\)", code)
    for check in logical_checks:
        match = re.search(r"(\w+)\s*(==|!=|>|<|>=|<=)\s*(\w+|\".*\")", check)
        if match:
            left_var, _, right_var = match.groups()
            left_type = variable_types.get(left_var, None)
            right_type = 'cadena' if right_var.startswith('"') else variable_types.get(right_var, None)
            if left_type and right_type and left_type != right_type:
                errors.append(f"Error semántico en la condición 'si ({check})'. Las variables deben ser del mismo tipo.")
            if left_var not in declared_variables and left_var not in reserved_words and left_var not in functions:
                errors.append(f"Variable '{left_var}' utilizada pero no declarada en la condición 'si ({check})'.")
            if right_var not in declared_variables and right_var not in reserved_words and right_var not in functions and not right_var.startswith('"'):
                errors.append(f"Variable '{right_var}' utilizada pero no declarada en la condición 'si ({check})'.")
                    
        else:
            errors.append(f"Error semántico en la condición 'si ({check})'. Formato incorrecto de comparación.")

    # Filtrar errores para eliminar palabras reservadas y funciones conocidas
    filtered_errors = [error for error in errors if not any(word in error.split() for word in reserved_words.union(functions))]

    if not filtered_errors:
        return "Uso correcto de las estructuras semánticas", corrected_code
    else:
        return " ".join(filtered_errors), corrected_code




@app.route('/', methods=['GET', 'POST'])
def index():
    code = ''
    lexical_results = []
    total_results = {'PR': 0, 'ID': 0, 'NUM': 0, 'SYM': 0, 'ERR': 0}
    syntactic_result = ''
    semantic_result = ''
    corrected_code = ''
    declared_variables = set()  # Conjunto para almacenar variables declaradas

    if request.method == 'POST':
        code = request.form['code']
        lexical_results, total_results, declared_variables = analyze_lexical(code)
        syntactic_result, corrected_code = analyze_syntactic(code)
        semantic_result, corrected_code = analyze_semantic(corrected_code)
    
    return render_template_string(html_template, code=code, lexical=lexical_results, total=total_results, syntactic=syntactic_result, semantic=semantic_result, corrected_code=corrected_code)

if __name__ == '__main__':
    app.run(debug=True)

