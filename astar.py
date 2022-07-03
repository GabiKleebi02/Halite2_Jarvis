import heapq
import logging
import math

from hlt.entity import Position
from hlt.game_map import Map


class AStar:
    def __init__(self, game_map: Map):
        self.game_map = game_map
        self.width = game_map.width
        self.height = game_map.height
        self.planets = game_map.all_planets()
        self._create_obstacle_map()

    def _create_empty_2d_map(self):
        return [[0 for x in range(self.width)] for y in range(self.height)]

    def _create_obstacle_map(self):
        self.obstacle_map = self._create_empty_2d_map()
        for y in range(self.height):
            for x in range(self.width):
                for planet in self.planets:
                    if math.pow(x - planet.x, 2) + math.pow(y - planet.y, 2) < math.pow(planet.radius, 2):
                        self.obstacle_map[y][x] = 1

    def _create_cost_map(self, start_x, start_y, goal_x, goal_y):
        costs_map = self._create_empty_2d_map()

        for y in range(self.height):
            for x in range(self.height):
                distance = math.sqrt(
                    math.pow(x - start_x, 2) +
                    math.pow(y - start_y, 2)
                )

                costs = math.ceil(distance)
                costs_map[y][x] = costs

        return costs_map

    def _get_neighbouring_cells(self, x, y):
        neighbours = []

        if x == 0:
            neighbours.append((1, y))

            if y == 0:
                neighbours.append((x, 1))
            elif y == self.height - 1:
                neighbours.append((x, y - 1))
            else:
                neighbours.append((x, y - 1))
                neighbours.append((x, y + 1))

        elif x == self.width - 1:
            neighbours.append((x, y))

            if y == 0:
                neighbours.append((x, 1))
            elif y == self.height - 1:
                neighbours.append((x, y - 1))
            else:
                neighbours.append((x, y - 1))
                neighbours.append((x, y + 1))

        else:
            neighbours.append((x - 1, y))
            neighbours.append((x + 1, y))

            if y == 0:
                neighbours.append((x, 1))
            elif y == self.height - 1:
                neighbours.append((x, y - 1))
            else:
                neighbours.append((x, y - 1))
                neighbours.append((x, y + 1))

        return neighbours

    # function to calculate if a Point p is in a line specified by two Points a and b
    # @params: a, b     -   two points specifying a line
    #           p       -   a Point tested if on the line
    # @return: boolean  -   True, if point is on the line, False otherwise
    @staticmethod
    def _is_in_line(a: Position, b: Position, p: Position):
        poi = Position(0, 0)  # point of intersection

        # Falls x-Werte gleich:
        if b.x == a.x:
            if b.y == a.y:
                logging.info(f"Die Punkte {a} und {b} sind verbotenerweise identisch!")
            return abs(p.x - a.x) <= 1.1
        # Falls nur y-Werte gleich:
        if b.y == a.y:
            return abs(p.y - a.y) <= 1.1

        # Ansonsten finde den Schnittpunkt v der Geraden g und der Normalen zu g durch den Punkt p
        else:
            m = (b.y - a.y) / (b.x - a.x)  # Steigung der Geraden g
            c = ((a.y * b.x) - (b.y * a.x)) / (b.x - a.x)  # Y-Achsenabschnitt von g
            n = -1 / m  # Steigung der Normalen zu g
            d = p.y - n * p.x  # Y-Achsenschnittpunkt der Normalen durch den Punkt p
            poi.x = (d - c) / (m - n)  # x-Wert des Schnittpunktes
            poi.y = m * poi.x + c  # y-Wert des Schnittpunktes
            dist = math.sqrt((p.x - poi.x) ** 2 + (p.y - poi.y) ** 2)  # Abstand der Punkte p und v (und damit zu g)
            return dist < 0.8  # Berücksichtige alle Punkte innerhalb eines Bandes der Breite 1,6, also 0,8 der Mitte

    # function to calculate if a Point p is in a rectangle specified by two opposite points a and b
    # @params: a, b     -   two points specifying a rectangle
    #           p       -   a Point tested if on the line
    # @return: boolean  -   True, if point is inside or on the edge of the rectangle, False otherwise
    @staticmethod
    def _is_between(a: Position, b: Position, p: Position):
        # x-value of 'a' is closer to origin than x-value of 'b'
        if a.x < b.x:
            result_x = a.x <= p.x <= b.x
        else:
            result_x = b.x <= p.x <= a.x
        # y-value of 'a' is closer to origin than y-value of 'b'
        if a.y < b.y:
            result_y = a.y <= p.y <= b.y
        else:
            result_y = b.y <= p.y <= a.y
        # both results must be true to have point 'p' inside the rectangle
        return result_x and result_y

    def _shorten_path(self, path: [(int, int)]):
        if len(path) < 3:
            return path

        start_point, end_point = Position(path[0][0], path[0][1]), Position(path[1][0], path[1][1])
        shortened_path = [(start_point.x, start_point.y)]

        for i in range(2, len(path)):
            point_to_check = path[i]
            position = Position(x=point_to_check[0], y=point_to_check[1])

            # Prüfen, ob der Punkt auf der Strecke liegt
            if self._is_in_line(start_point, end_point, position):
                # Neuen Endpunkt der derzeitigen Strecke setzen
                end_point = position
                continue

            # Punkt lag nicht auf der Strecke
            end_point = position
            shortened_path.append((end_point.x, end_point.y))
            start_point = end_point

        shortened_path.append((end_point.x, end_point.y))

        return shortened_path

    def find_path(self, start_x: int, start_y: int, goal_x: int, goal_y: int):
        costs_map = self._create_cost_map(start_x, start_y, goal_x, goal_y)
        start = (start_x, start_y)
        goal = (goal_x, goal_y)
        frontier = []
        came_from = dict()
        cost_so_far = dict()

        # Startwert hinzuzufügen
        heapq.heappush(frontier, (0, start))
        came_from[start] = None
        cost_so_far[start] = 0

        # solange frontier nicht leer ist, wird eine Route gesucht
        while frontier:
            (priority, (current_node_x, current_node_y)) = heapq.heappop(frontier)
            current_node = (current_node_x, current_node_y)

            if current_node == goal:
                break

            for (next_node_x, next_node_y) in self._get_neighbouring_cells(current_node_x, current_node_y):
                next_node = (next_node_x, next_node_y)

                # prüfen, ob Nachbar kein Planet ist
                if self.obstacle_map[next_node_y][next_node_x] == 1:
                    continue

                # Kosten für diese Zelle berechnen
                cell_costs = costs_map[next_node_y][next_node_x]
                path_costs = cost_so_far[current_node] + cell_costs

                # wenn dieser Pfad zu der Zelle der günstigste zu dieser ist
                if next_node not in cost_so_far or path_costs < cost_so_far[next_node]:
                    cost_so_far[next_node] = path_costs
                    priority = path_costs

                    next_node_heap = (priority, next_node)

                    heapq.heappush(frontier, next_node_heap)
                    came_from[next_node] = current_node

        # Pfad vom Ziel zum Start ermitteln
        cell, path = goal, [goal]

        while cell is not start:

            predecessor = came_from[cell]

            if predecessor is None:
                break

            path.append(predecessor)
            cell = predecessor

        # Pfad umdrehen, damit er vom Start zum Ziel geht
        path.reverse()
        path = self._shorten_path(path)

        return path
