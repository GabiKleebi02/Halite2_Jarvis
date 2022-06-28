import heapq
import math
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

        return path
