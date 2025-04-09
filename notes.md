### Estrategia General (MordecaiBot)

El agente implementado dispone de un límite de tiempo (`time_limit`) para realizar sus movimientos. Este parámetro asegura que la inteligencia artificial no consuma tiempo excesivo explorando el espacio de búsqueda, permitiendo un balance entre rendimiento y eficiencia. Durante este intervalo, el agente emplea el algoritmo Minimax con poda alfa-beta para determinar la mejor jugada posible. En caso de que el tiempo límite expire sin encontrar una solución óptima y existan movimientos disponibles en el tablero, el agente seleccionará un movimiento prometedor, priorizando aquellos con mayor potencial estratégico.

#### Movimientos Prometedores

Los movimientos prometedores son identificados como aquellas posiciones en el tablero que presentan una mayor posibilidad de generar un resultado favorable, basándose en su proximidad a posiciones ya ocupadas. Este enfoque permite calcular movimientos de manera eficiente, especialmente en las fases iniciales de la partida, donde el tablero se encuentra más abierto y el espacio de búsqueda es considerablemente amplio. 

En este contexto, los movimientos prometedores corresponden a las posiciones adyacentes a las ya ocupadas, ordenadas según su distancia al centro del tablero. Este criterio de ordenación busca maximizar la conectividad y el control estratégico del tablero.

#### Selección de Movimientos en Caso de Ausencia de Prometedores

Si no se identifican movimientos prometedores, el agente recurre al conjunto de posiciones libres del tablero, obtenidas mediante el método `get_possible_moves`. En este caso, se selecciona la primera posición disponible, garantizando que el agente siempre realice un movimiento válido.

Este enfoque en el diseño del agente `MordecaiBot`, busca un equilibrio entre la exploración exhaustiva del espacio de búsqueda y la capacidad de tomar decisiones rápidas y sensatas en escenarios donde el tiempo es un recurso limitado.

El algoritmo asigna un valor a cada estado del tablero utilizando una función de evaluación (`evaluate`). Esta función considera los siguientes factores:

1. **Distancia al Camino Más Corto** (`shortest_path_distance`):
    - Evalúa la distancia mínima necesaria para que el jugador actual y el oponente completen su conexión en el tablero.
    - **Ponderación**: `(opp_distance - my_distance) * 50`
    - Un menor valor para el jugador actual y un mayor valor para el oponente resultan en un puntaje más alto.

2. **Distancia al Segundo Camino Más Corto** (`two_distance`):
    - Considera caminos secundarios que podrían ser útiles para reforzar la estrategia del jugador o bloquear al oponente.
    - **Ponderación**: `(opp_second - my_second) * 20`
    - Promueve la creación de múltiples opciones estratégicas mientras penaliza las del oponente.

3. **Bonificación por Conectividad**:
    - Calcula una bonificación basada en la proximidad de las piezas del jugador al centro del tablero, incentivando una mayor conectividad y control estratégico.
    - **Ponderación**: `+5` por cada pieza del jugador cerca del centro, `-5` por cada pieza del oponente en una posición similar.
    - La fórmula incluye un factor de distancia para priorizar posiciones más cercanas al centro.
